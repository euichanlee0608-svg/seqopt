# -*- coding: utf-8 -*-
"""Global-search validation — does the way we choose (the acquisition function) get stuck in local optima.

    .venv/bin/python packaging/bench_global.py            # full run (about 70 min with 8 workers — docs/GLOBAL_SEARCH.md)
    .venv/bin/python packaging/bench_global.py --quick    # 1 function · 2 seeds (smoke test)

**What is measured**  Budget 40 = 11 initial points (maximin LHS) + 29 sequential. The next
point is chosen on the same path as the real program (`core.recommend.recommend`), and a
value with noise (3% of the range) is observed. At the end, taking **the true value of the
condition whose observation was best**,

    regret = (global maximum − true value) / range          smaller is better
    hit    = regret < 5%                                    did it actually reach the global peak

over 10 seeds. Functions with several peaks (Branin · six-hump camel · Hartmann-3 · two-peak ·
Hartmann-6 · Levy-4) are mixed with a single-peak one (Rosenbrock) and a rugged one (Ackley),
and only a strategy that "gains on multimodal without losing on unimodal" goes on screen.
(In a first round with only the four 2–3-D functions, the three other than two-peak sat at
100% for every strategy — a ceiling, no discrimination — so the 4-D and 6-D ones were added.
The decision rule stayed the same. docs/GLOBAL_SEARCH.md)

**Inner-maximizer check**  Whether the acquisition maximization over continuous variables
(multi-start L-BFGS-B) falls into local optima: the same model and acquisition are maximized
again with differential evolution (scipy `differential_evolution`) and compared. The fraction
of cases where multi-start came out lower than DE is recorded.

The result is saved to `docs/bench_global.json` and a summary table is printed.
`tests/test_global.py` reads the numbers in that file and checks that they match what the
screen claims — the file is neither hand-edited nor auto-refreshed (baseline rule).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dataclasses import field  # noqa: E402

from scipy.stats import norm  # noqa: E402

from core.acquisition import (_SD_FLOOR, ExpectedImprovement, ThompsonSampling,  # noqa: E402
                              UpperConfidenceBound, maximise_continuous)
from core.dataset import build  # noqa: E402
from core.design import initial_design  # noqa: E402
from core.diagnostics import Gate  # noqa: E402
from core.protocols import Surrogate  # noqa: E402
from core.recommend import _axis_bounds, recommend  # noqa: E402
from core.spec import ObjSpec, VarSpec  # noqa: E402
from core.surrogate import fit  # noqa: E402

OUT = ROOT / "docs" / "bench_global.json"
BUDGET, INITIAL = 40, 11
NOISE_FRAC = 0.03            # observation noise σ = 3% of the range
HIT_FRAC = 0.05              # regret < 5% counts as reaching the global peak
SEEDS = list(range(10))
INNER_TOL = 1e-3             # inner-maximizer comparison — a relative gap below this is the same peak
OPEN = Gate(cond_count="OK", learnable="OK", discrim="OK", replicates="OK", locked=False)


# ══════════════════════════════════════════════════════════════════════
# Test functions — all on [0,1]^d, **maximized**. (Standard definitions with the sign flipped)
# ══════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class Bench:
    name: str
    dim: int
    f: callable                  # x_unit(d,) -> float, larger is better
    fmax: float                  # global maximum (true value)
    frange: float                # value range over the domain (fmax − fmin)
    multimodal: bool
    note: str


def _branin(u):
    x1, x2 = -5 + 15 * u[0], 15 * u[1]
    a, b, c, r, s, t = 1, 5.1 / (4 * np.pi ** 2), 5 / np.pi, 6, 10, 1 / (8 * np.pi)
    return -(a * (x2 - b * x1 ** 2 + c * x1 - r) ** 2 + s * (1 - t) * np.cos(x1) + s)


def _camel6(u):
    x1, x2 = -2 + 4 * u[0], -1 + 2 * u[1]
    return -((4 - 2.1 * x1 ** 2 + x1 ** 4 / 3) * x1 ** 2 + x1 * x2 + (-4 + 4 * x2 ** 2) * x2 ** 2)


_H3_A = np.array([[3.0, 10, 30], [0.1, 10, 35], [3.0, 10, 30], [0.1, 10, 35]])
_H3_P = 1e-4 * np.array([[3689, 1170, 2673], [4699, 4387, 7470],
                         [1091, 8732, 5547], [381, 5743, 8828]])
_H3_ALPHA = np.array([1.0, 1.2, 3.0, 3.2])


def _hartmann3(u):
    u = np.asarray(u, dtype=float)
    return float(np.sum(_H3_ALPHA * np.exp(-np.sum(_H3_A * (u - _H3_P) ** 2, axis=1))))


def _twopeak(u):
    """A broad low peak (0.6) + a narrow high peak (1.0). EI settles on the low peak easily."""
    u = np.asarray(u, dtype=float)
    broad = 0.6 * np.exp(-np.sum((u - [0.25, 0.3]) ** 2) / (2 * 0.22 ** 2))
    sharp = 1.0 * np.exp(-np.sum((u - [0.78, 0.72]) ** 2) / (2 * 0.07 ** 2))
    return float(broad + sharp)


def _rosen2(u):
    x1, x2 = -2 + 4 * u[0], -1 + 4 * u[1]
    return -(100 * (x2 - x1 ** 2) ** 2 + (1 - x1) ** 2)


def _ackley2(u):
    x = -4 + 8 * np.asarray(u, dtype=float)
    d = len(x)
    return -(-20 * np.exp(-0.2 * np.sqrt(np.sum(x ** 2) / d))
             - np.exp(np.sum(np.cos(2 * np.pi * x)) / d) + 20 + np.e)


_H6_A = np.array([[10, 3, 17, 3.5, 1.7, 8], [0.05, 10, 17, 0.1, 8, 14],
                  [3, 3.5, 1.7, 10, 17, 8], [17, 8, 0.05, 10, 0.1, 14]], dtype=float)
_H6_P = 1e-4 * np.array([[1312, 1696, 5569, 124, 8283, 5886], [2329, 4135, 8307, 3736, 1004, 9991],
                         [2348, 1451, 3522, 2883, 3047, 6650], [4047, 8828, 8732, 5743, 1091, 381]])


def _hartmann6(u):
    u = np.asarray(u, dtype=float)
    return float(np.sum(_H3_ALPHA * np.exp(-np.sum(_H6_A * (u - _H6_P) ** 2, axis=1))))


def _levy4(u):
    x = -10 + 20 * np.asarray(u, dtype=float)
    w = 1 + (x - 1) / 4
    return -float(np.sin(np.pi * w[0]) ** 2
                  + np.sum((w[:-1] - 1) ** 2 * (1 + 10 * np.sin(np.pi * w[:-1] + 1) ** 2))
                  + (w[-1] - 1) ** 2 * (1 + np.sin(2 * np.pi * w[-1]) ** 2))


def _range_of(f, dim, n=200_000, seed=0):
    """Value range over the domain — max and min of a random sample."""
    rng = np.random.default_rng(seed)
    pts = rng.random((n, dim))
    vals = np.array([f(p) for p in pts])
    return float(vals.max()), float(vals.min())


def benches() -> list[Bench]:
    out = []
    for name, dim, f, fmax, multi, note in [
        ("branin", 2, _branin, -0.397887, True, "3 global optima, wide valley"),
        ("camel6", 2, _camel6, 1.031628, True, "4 local + 2 global"),
        ("hartmann3", 3, _hartmann3, 3.86278, True, "4 local, 1 global (3-D)"),
        ("twopeak", 2, _twopeak, None, True, "broad low peak + narrow high peak (deceptive)"),
        ("hartmann6", 6, _hartmann6, 3.32237, True, "6 local, 1 global (6-D — a device with many variables)"),
        ("levy4", 4, _levy4, 0.0, True, "many local + wide funnel (4-D)"),
        ("rosen2", 2, _rosen2, 0.0, False, "unimodal, curved valley (checks there is no loss)"),
        ("ackley2", 2, _ackley2, 0.0, False, "rugged multimodal — so fine the GP reads it as noise"),
    ]:
        hi, lo = _range_of(f, dim)
        if fmax is None:
            fmax = hi
        out.append(Bench(name, dim, f, float(max(fmax, hi)), float(max(fmax, hi) - lo),
                         multi, note))
    return out


# ══════════════════════════════════════════════════════════════════════
# What is compared — what is on screen + candidates (defined only here; nothing
# goes into core before it passes validation)
#
# 2026-09-05 result: none of the candidates below beat EI on multimodal hit rate
# (docs/GLOBAL_SEARCH.md). So none is on screen. The code stays here for
# re-validation (with a different budget, noise or functions).
# ══════════════════════════════════════════════════════════════════════
@dataclass
class MaxValueEntropySearch:
    """Max-value entropy search (Wang & Jegelka, ICML 2017).

    Scores "how much the next measurement tells us about **what the global
    maximum is**". EI is 'expected gain over the current best', so it tends to
    stay near places that are already good; MES measures information about the
    maximum itself, so it also scores **peaks not yet seen**.

    The distribution of the maximum f* is sampled by approximating the maximum
    of the posterior over the candidate grid with a Gumbel (Algorithm 1 in the
    paper). The samples are drawn once in `prepare()` and held fixed during
    maximization.

        α(x) = mean_k [ γ_k φ(γ_k) / (2 Φ(γ_k)) − log Φ(γ_k) ],   γ_k = (f*_k − μ(x)) / σ(x)
    """

    n_samples: int = 16
    label = "Global search — max-value information (MES)"
    supports_continuous = True
    _fstar: np.ndarray | None = field(default=None, init=False, repr=False, compare=False)
    _model_id: int | None = field(default=None, init=False, repr=False, compare=False)

    def prepare(self, model: Surrogate, pool: np.ndarray, best: float,
                rng: np.random.Generator | None = None) -> None:
        rng = rng or np.random.default_rng(0)
        mean, std = model.predict(np.asarray(pool, dtype=float))
        std = np.maximum(std, _SD_FLOOR)

        def cdf_max(z: float) -> float:            # P(max_i f(x_i) < z)
            return float(np.exp(np.sum(norm.logcdf((z - mean) / std))))

        left = max(float(best), float(mean.max()))
        right = float((mean + 5.0 * std).max())
        if right <= left:
            right = left + 1e-6

        def quantile(q: float) -> float:            # cdf_max is monotone → bisection
            lo, hi = left, right
            if cdf_max(lo) > q:                     # if the left end already exceeds q, that value
                return lo
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if cdf_max(mid) < q:
                    lo = mid
                else:
                    hi = mid
            return 0.5 * (lo + hi)

        q1, q3 = quantile(0.25), quantile(0.75)
        b = (q1 - q3) / (np.log(-np.log(0.75)) - np.log(-np.log(0.25)))
        a = q1 + b * np.log(-np.log(0.25))
        u = rng.random(self.n_samples)
        fstar = a - b * np.log(-np.log(u))
        # the maximum must exceed the current best — samples below it carry no information
        self._fstar = np.maximum(fstar, float(best) + 1e-6 * max(1.0, abs(float(best))))
        self._model_id = id(model)

    def score(self, model: Surrogate, X: np.ndarray, best: float,
              rng: np.random.Generator | None = None) -> np.ndarray:
        if self._fstar is None or self._model_id != id(model):
            self.prepare(model, X, best, rng)
        mean, std = model.predict(X)
        std = np.maximum(std, _SD_FLOOR)
        gamma = (self._fstar[None, :] - mean[:, None]) / std[:, None]
        log_cdf = norm.logcdf(gamma)
        ratio = np.exp(norm.logpdf(gamma) - log_cdf)          # φ/Φ, stably
        return np.mean(0.5 * gamma * ratio - log_cdf, axis=1)

    def describe(self) -> str:
        return f"MES ({self.n_samples} max-value samples)"


@dataclass
class ExploreMix:
    """Mix **periodic pure exploration** into the default (EI) (a deterministic ε-greedy).

    De Ath et al. (ACM TELO 2021) showed that mixing a fixed share of exploration
    into EI-type strategies reduces getting stuck in local optima on multimodal
    terrain, with almost no loss on unimodal terrain. It is decided by **turn**,
    not by a random draw — "every `period`-th recommendation goes to the least
    known place (max σ)" — because a user reading the instruction sheet must be
    able to explain why that point.

    Whether this recommendation is an exploration turn is decided in `prepare()`
    from the number of training points.
    """

    period: int = 4
    label = "Global search — mix exploration into the default"
    supports_continuous = True
    _explore: bool = field(default=False, init=False, repr=False, compare=False)

    def prepare(self, model: Surrogate, pool: np.ndarray, best: float,
                rng: np.random.Generator | None = None) -> None:
        raw = getattr(model, "_raw", model)
        n_train = len(getattr(raw, "X_train_", []))
        self._explore = self.period > 0 and n_train > 0 and n_train % self.period == 0

    def score(self, model: Surrogate, X: np.ndarray, best: float,
              rng: np.random.Generator | None = None) -> np.ndarray:
        mean, std = model.predict(X)
        if self._explore:
            return np.asarray(std, dtype=float)
        std = np.maximum(std, _SD_FLOOR)
        z = (mean - best) / std
        return (mean - best) * norm.cdf(z) + std * norm.pdf(z)

    def describe(self) -> str:
        return ("EI + exploration (this turn explores — max σ)" if self._explore
                else f"EI + exploration (every {self.period}th turn)")


class GPUCBSchedule:
    """The β_t schedule of Srinivas et al. (ICML 2010). Scaled down by 1/5, as in the paper."""

    name = "GPUCB"
    label = "GP-UCB (β_t schedule)"
    supports_continuous = True
    delta = 0.1

    def prepare(self, model, pool, best, rng=None):
        raw = getattr(model, "_raw", model)
        t, d = len(raw.X_train_), raw.X_train_.shape[1]
        beta = 2 * np.log(t ** (d / 2 + 2) * np.pi ** 2 / (3 * self.delta)) / 5
        self.beta = float(np.sqrt(max(beta, 1e-9)))

    def score(self, model, X, best, rng=None):
        mean, std = model.predict(X)
        return mean + getattr(self, "beta", 2.0) * std

    def describe(self):
        return f"GP-UCB β={getattr(self, 'beta', 0):.2f}"


class ExploreMixTS(ExploreMix):
    """Variant that uses a Thompson draw instead of max σ on exploration turns (candidate enumeration only)."""

    name = "MIX-TS"

    @property
    def supports_continuous(self):          # exploration turns go by enumeration
        return not self._explore

    def score(self, model, X, best, rng=None):
        if self._explore:
            return model.sample(X, rng or np.random.default_rng(0))
        return super().score(model, X, best, rng)


STRATEGIES = {
    "EI": lambda: ExpectedImprovement(),
    "UCB2": lambda: UpperConfidenceBound(2.0),
    "TS": lambda: ThompsonSampling(),
    "MES": lambda: MaxValueEntropySearch(),
    "MIX4": lambda: ExploreMix(period=4),
    "MIX4-TS": lambda: ExploreMixTS(period=4),
    "GPUCB": lambda: GPUCBSchedule(),
}


# ══════════════════════════════════════════════════════════════════════
# One optimization run — the same path as the real program
# ══════════════════════════════════════════════════════════════════════
def _dataset(X, y, inputs):
    groups = {tuple(round(float(v), 6) for v in x): [float(v)] for x, v in zip(X, y)}
    return build(groups, inputs, ObjSpec("y"))


def run_one(args):
    bench_name, strat, seed = args
    warnings.filterwarnings("ignore")
    bench = next(b for b in benches() if b.name == bench_name)
    inputs = [VarSpec(f"x{k + 1}", "", "continuous", 0.0, 1.0) for k in range(bench.dim)]
    rng = np.random.default_rng(1000 * seed + 7)
    sigma = NOISE_FRAC * bench.frange

    X = initial_design(INITIAL, inputs, seed=seed)
    y = np.array([bench.f(x) + rng.normal(0, sigma) for x in X])
    t0 = time.time()
    for _ in range(BUDGET - INITIAL):
        ds = _dataset(X, y, inputs)
        acq = STRATEGIES[strat]()
        rec = recommend(ds, inputs, OPEN, acquisition=acq, rng=rng)
        if not rec.suggestions:
            break
        x = np.clip(rec.suggestions[0].x_real, 0.0, 1.0)
        X = np.vstack([X, x])
        y = np.append(y, bench.f(x) + rng.normal(0, sigma))

    k = int(np.argmax(y))                        # best by observation (principle P3)
    true_best = float(bench.f(X[k]))
    regret = (bench.fmax - true_best) / bench.frange
    return {"bench": bench_name, "strategy": strat, "seed": seed,
            "regret": float(regret), "hit": bool(regret < HIT_FRAC),
            "n": int(len(y)), "seconds": round(time.time() - t0, 1)}


# ══════════════════════════════════════════════════════════════════════
# Inner-maximizer check — multi-start L-BFGS-B vs differential evolution
# ══════════════════════════════════════════════════════════════════════
def check_inner_maximiser(seeds=(0, 1, 2), steps=(15, 25, 35)):
    from scipy.optimize import differential_evolution

    out = []
    for bench in benches():
        inputs = [VarSpec(f"x{k + 1}", "", "continuous", 0.0, 1.0) for k in range(bench.dim)]
        for seed in seeds:
            rng = np.random.default_rng(seed)
            X = rng.random((max(steps), bench.dim))
            y = np.array([bench.f(x) for x in X]) + rng.normal(0, NOISE_FRAC * bench.frange,
                                                             len(X))
            for n in steps:
                ds = _dataset(X[:n], y[:n], inputs)
                model = fit(ds.XN, ds.y_mean)
                acq = ExpectedImprovement()
                best = float(ds.y_mean.max())
                bounds = _axis_bounds(ds, inputs)
                ms = maximise_continuous(model, acq, best, bounds, rng)
                de = differential_evolution(
                    lambda v: -float(acq.score(model, v.reshape(1, -1), best)[0]),
                    bounds=[tuple(b) for b in bounds], seed=0, tol=1e-10, maxiter=400,
                    popsize=25, polish=True)
                # Same peak → nearly the same value. At first this used 1e-6, and 4 cases in 6-D
                # were caught at a relative gap of 2e-6 — not a different peak but L-BFGS-B's
                # finishing, so 1e-3 it is.
                scale = max(abs(ms.acq_value), abs(-de.fun), 1e-12)
                out.append({"bench": bench.name, "seed": seed, "n": n,
                            "multistart": float(ms.acq_value), "de": float(-de.fun),
                            "multistart_ge_de": bool(ms.acq_value >= -de.fun - INNER_TOL * scale)})
    return out


# ══════════════════════════════════════════════════════════════════════
def summarise(rows):
    table = {}
    for r in rows:
        key = (r["bench"], r["strategy"])
        table.setdefault(key, []).append(r)
    summary = {}
    for (b, s), rs in sorted(table.items()):
        reg = np.array([r["regret"] for r in rs])
        summary.setdefault(b, {})[s] = {
            "hit_rate": float(np.mean([r["hit"] for r in rs])),
            "median_regret": float(np.median(reg)),
            "mean_regret": float(reg.mean()),
            "seeds": len(rs),
        }
    return summary


def print_table(summary, names):
    strategies = list(STRATEGIES)
    print("\nhit rate (regret<5%) / median regret")
    print("function".ljust(11) + "".join(s.rjust(13) for s in strategies))
    for b in names:
        row = b.ljust(11)
        for s in strategies:
            c = summary.get(b, {}).get(s)
            row += (f"{c['hit_rate'] * 100:4.0f}%/{c['median_regret'] * 100:4.1f}".rjust(13)
                    if c else "-".rjust(13))
        print(row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--inner-only", action="store_true",
                    help="keep the run results, redo only the inner-maximizer check and replace that part")
    a = ap.parse_args()

    if a.inner_only:
        data = json.loads(a.out.read_text(encoding="utf-8"))
        data["inner_maximiser"] = check_inner_maximiser()
        data["inner_tol"] = INNER_TOL
        bad = [r for r in data["inner_maximiser"] if not r["multistart_ge_de"]]
        print(f"inner maximizer: fraction with multi-start ≥ DE "
              f"{1 - len(bad) / len(data['inner_maximiser']):.3f} (relative tolerance {INNER_TOL})")
        a.out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        return

    bl = benches()
    names = [b.name for b in bl]
    seeds = SEEDS[:2] if a.quick else SEEDS
    if a.quick:
        names = ["twopeak"]
    jobs = [(b, s, sd) for b in names for s in STRATEGIES for sd in seeds]
    print(f"{len(jobs)} runs × {BUDGET - INITIAL} steps, workers={a.workers}")
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(run_one, jobs, chunksize=1), 1):
            rows.append(r)
            if i % 20 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)}  {time.time() - t0:.0f}s", flush=True)

    inner = [] if a.quick else check_inner_maximiser()
    summary = summarise(rows)
    print_table(summary, names)
    if inner:
        bad = [r for r in inner if not r["multistart_ge_de"]]
        print(f"\ninner maximizer: fraction with multi-start ≥ DE {1 - len(bad) / len(inner):.3f} "
              f"({len(inner) - len(bad)}/{len(inner)})")

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({
        "budget": BUDGET, "initial": INITIAL, "noise_frac": NOISE_FRAC, "hit_frac": HIT_FRAC,
        "seeds": seeds, "benches": [{"name": b.name, "dim": b.dim, "multimodal": b.multimodal,
                                     "fmax": b.fmax, "frange": b.frange, "note": b.note}
                                    for b in bl if b.name in names],
        "summary": summary, "runs": rows, "inner_maximiser": inner, "inner_tol": INNER_TOL,
        "elapsed_s": round(time.time() - t0),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n→ {a.out}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
