# -*- coding: utf-8 -*-
"""Acquisition functions — turn "where would the next measurement teach the most" into a score (§5-7 · F-20 ~ F-24).

To add an acquisition function, **add a class** with `@ACQUISITIONS.register("name")`.
Do not touch the existing classes or the rest of this file.

    @ACQUISITIONS.register("PI")
    class ProbabilityOfImprovement:
        label = "PI — probability of improvement"
        supports_continuous = True
        def score(self, model, X, best, rng=None): ...
        def describe(self): return "PI"

**`best` is always the best measured value** (principle P3). Passing a true or
corrected value changes the ranking.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm

from .protocols import Acquisition, Surrogate
from .registry import Registry

ACQUISITIONS: Registry[Acquisition] = Registry("acquisition")
DEFAULT_ACQUISITION = "EI"

STOP_EI_FRACTION = 0.01      # F-24 : suggest stopping when the max acquisition value
STOP_PATIENCE = 3            #        stays below 1% of the response range 3 times in a row

_SD_FLOOR = 1e-9             # avoid dividing by zero where σ=0

# Global-search validation (packaging/bench_global.py → docs/bench_global.json, 2026-09-05).
# The help tab's «How it chooses» reads these values, and tests/test_global.py checks that they
# match the JSON — do not edit them by hand.
# hit rate = fraction of seeds (10 seeds) with regret < 5% within a 40-run budget
# (11 initial + 29 sequential, 3% noise).
# 6 multimodal = Branin · six-hump camel · Hartmann-3 · two-peak · Hartmann-6 · Levy-4,
# 2 unimodal/rugged = Rosenbrock · Ackley.
# None of the 4 alternatives (MES · EI + exploration mixing · GP-UCB schedule · the Thompson
# variant of the mixing) beat EI on the multimodal set, so none went on screen
# (the candidate code lives only in packaging/bench_global.py — docs/GLOBAL_SEARCH.md).
BENCH_CLAIMS = {
    "multimodal_hit": 0.717,                    # EI, mean over the 6 multimodal functions
    "unimodal_hit": 0.700,                      # EI, mean over the 2 unimodal/rugged functions
    "ucb_multimodal_hit": 0.617,                # UCB(b=2), multimodal mean — "pushing exploration harder does not help"
    "best_alternative_multimodal_hit": 0.700,   # best multimodal mean among the 4 alternatives (MES)
    "ei_hit": {"branin": 1.0, "camel6": 1.0, "hartmann3": 1.0, "rosen2": 1.0,
               "levy4": 0.8, "twopeak": 0.4, "ackley2": 0.4, "hartmann6": 0.1},
}


def prepare(acquisition: Acquisition, model: Surrogate, pool: np.ndarray, best: float,
            rng: np.random.Generator | None) -> None:
    """Called once per recommendation, before any scoring.

    Acquisitions that carry state (e.g. MES's max-value samples, whether this
    turn explores) settle it here. `score()` is called thousands of times during
    maximization, so drawing random numbers inside it would change the objective
    on every call and send L-BFGS-B in circles. The three on screen (EI · UCB ·
    Thompson) are stateless and pass straight through — the hook is kept so the
    candidates in `packaging/bench_global.py` can be validated **on the real
    recommendation path, unchanged**.
    """
    hook = getattr(acquisition, "prepare", None)
    if hook is not None:
        hook(model, pool, best, rng)


@ACQUISITIONS.register("EI")
@dataclass
class ExpectedImprovement:
    """Expected improvement. EI = (μ − best)·Φ(z) + σ·φ(z), z = (μ − best)/σ.

    In the 8-test-function benchmark its global-optimum hit rate within a
    40-run budget averaged 72% on the multimodal set — the highest of the 7
    strategies, the 4 alternatives included (`BENCH_CLAIMS` ·
    docs/GLOBAL_SEARCH.md). That is why it is the default.
    """

    label = "Default — expected improvement (EI)"
    when = ("Use this in most cases. It scores each candidate by how much it is "
            "expected to beat the best so far.")
    supports_continuous = True

    def score(self, model: Surrogate, X: np.ndarray, best: float,
              rng: np.random.Generator | None = None) -> np.ndarray:
        mean, std = model.predict(X)
        std = np.maximum(std, _SD_FLOOR)
        z = (mean - best) / std
        return (mean - best) * norm.cdf(z) + std * norm.pdf(z)

    def describe(self) -> str:
        return "EI (expected improvement)"


@ACQUISITIONS.register("UCB")
@dataclass
class UpperConfidenceBound:
    """μ + b·σ. A larger b pushes further into uncertainty.

    ⚠ Pushing harder does not help — in the original validation study (2026-08),
      raising b from 1 to 4 dropped the global-optimum hit rate from 90% to 61%,
      and in the 8-test-function benchmark b=2 averaged 62% on the multimodal
      set, below EI's 72% (`BENCH_CLAIMS`). Do not casually raise the default 2.0.
    """

    beta: float = 2.0
    label = "Explore wider — upper confidence bound (UCB)"
    when = ("When the terrain is still unknown. Looks harder at uncertain regions. "
            "Pushing too far backfires — raising b from 1 to 4 dropped the "
            "global-optimum hit rate from 90% to 61% in the validation study.")
    supports_continuous = True

    def score(self, model: Surrogate, X: np.ndarray, best: float,
              rng: np.random.Generator | None = None) -> np.ndarray:
        mean, std = model.predict(X)
        return mean + self.beta * std

    def describe(self) -> str:
        return f"UCB (b = {self.beta:g})"


@ACQUISITIONS.register("Thompson")
@dataclass
class ThompsonSampling:
    """Draw one function from the posterior and pick its maximum.

    Sampling does not mix with continuous optimization (L-BFGS-B) → candidate
    enumeration only.
    """

    label = "Diversify — Thompson sampling"
    when = ("When you receive several suggestions at once. Each draw picks a "
            "different place, so candidates do not pile up in one spot. "
            "Running alone, the default (EI) is better.")
    supports_continuous = False

    def score(self, model: Surrogate, X: np.ndarray, best: float,
              rng: np.random.Generator | None = None) -> np.ndarray:
        return model.sample(X, rng or np.random.default_rng())

    def describe(self) -> str:
        return "Thompson sampling"


def make_acquisition(name: str = DEFAULT_ACQUISITION, **kwargs) -> Acquisition:
    return ACQUISITIONS.create(name, **kwargs)


# ══════════════════════════════════════════════════════════════════════
# Maximization — enumeration when discrete, multi-start L-BFGS-B when continuous (§5-7)
# ══════════════════════════════════════════════════════════════════════
@dataclass
class Pick:
    """One chosen point. Screens, instructions and the report use these values verbatim."""

    x_norm: np.ndarray
    acq_value: float
    mean: float
    std: float


def best_of(model: Surrogate, acquisition: Acquisition, candidates: np.ndarray,
            best: float, rng: np.random.Generator | None = None) -> Pick:
    """The single highest-scoring candidate in the list."""
    if len(candidates) == 0:
        raise ValueError("The candidate list is empty")
    values = acquisition.score(model, candidates, best, rng)
    k = int(np.argmax(values))
    mean, std = model.predict(candidates[k:k + 1])
    return Pick(candidates[k], float(values[k]), float(mean[0]), float(std[0]))


def maximise_continuous(model: Surrogate, acquisition: Acquisition, best: float,
                        bounds: np.ndarray,
                        rng: np.random.Generator | None = None,
                        n_starts: int = 20, n_seed: int = 2000) -> Pick:
    """Maximize the acquisition over continuous space. Starts = top n_starts LHS points.

    `bounds` is the (d, 2) search range in normalized coordinates. **It is not
    pinned to [0,1]** — [0,1] is merely the measured range, and the design range
    the user declared can be wider. Ignore that difference and the tool can
    never conclude "widen the range and measure there."
    """
    if not acquisition.supports_continuous:
        raise ValueError(
            f"{acquisition.label} does not support continuous optimization — enumerate candidates instead")

    from .design import maximin_lhs
    bounds = np.asarray(bounds, dtype=float)
    dim = len(bounds)
    unit = maximin_lhs(n_seed, dim, seed=0, tries=1)
    seeds = bounds[:, 0] + unit * (bounds[:, 1] - bounds[:, 0])
    starts = seeds[np.argsort(acquisition.score(model, seeds, best, rng))[-n_starts:]]

    def negative(x: np.ndarray) -> float:
        return -float(acquisition.score(model, x.reshape(1, -1), best, rng)[0])

    best_x, best_v = starts[-1], -negative(starts[-1])
    for x0 in starts:
        result = minimize(negative, x0, method="L-BFGS-B",
                          bounds=[tuple(b) for b in bounds])
        if -result.fun > best_v:
            best_x, best_v = result.x, -result.fun
    mean, std = model.predict(best_x.reshape(1, -1))
    return Pick(best_x, float(best_v), float(mean[0]), float(std[0]))


def batch_picks(model: Surrogate, acquisition: Acquisition, candidates: np.ndarray,
                best: float, count: int, surrogate_name: str,
                rng: np.random.Generator | None = None) -> list[Pick]:
    """Batch recommendation (F-21) — kriging believer.

    Pick sequentially, but refit the model **assuming each picked point observed
    its predicted mean**. No true value is ever consulted, so the no-lookahead
    rule (principle P2) holds.
    """
    from .surrogate import fit

    X = np.asarray(getattr(model, "_raw", model).X_train_, dtype=float)
    y = np.asarray(getattr(model, "_raw", model).y_train_, dtype=float)
    pool = np.asarray(candidates, dtype=float).copy()
    picks: list[Pick] = []
    current = model

    for _ in range(count):
        if len(pool) == 0:
            break
        pick = best_of(current, acquisition, pool, best, rng)
        picks.append(pick)
        pool = pool[~np.all(np.isclose(pool, pick.x_norm), axis=1)]
        X = np.vstack([X, pick.x_norm])
        y = np.append(y, pick.mean)              # believer: treat the predicted mean as observed
        current = fit(X, y, surrogate_name)
    return picks


def should_stop(acq_history: list[float], response_range: float) -> bool:
    """Stopping rule (F-24). True when the max acquisition value stays below 1% of the response range 3 times in a row."""
    if len(acq_history) < STOP_PATIENCE or response_range <= 0:
        return False
    return all(v < STOP_EI_FRACTION * response_range for v in acq_history[-STOP_PATIENCE:])


def unmeasured(all_points: np.ndarray, measured: np.ndarray, tol: float = 1e-9) -> np.ndarray:
    """Keep only candidates not yet measured (principle P2)."""
    if len(measured) == 0:
        return all_points
    gap = np.linalg.norm(all_points[:, None, :] - measured[None, :, :], axis=2)
    return all_points[gap.min(axis=1) > tol]
