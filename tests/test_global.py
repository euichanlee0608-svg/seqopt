# -*- coding: utf-8 -*-
"""Global search — do the acquisitions on screen agree with the validation (docs/bench_global.json).

Three layers.
1. **The decision rule** — only an alternative whose multimodal hit rate in the baseline JSON is
   higher than EI's goes on screen (`ACQUISITIONS`). The 2026-09-05 result was "nothing beats it",
   so the screen offers just EI · UCB · Thompson. If the baseline is re-run and some candidate
   beats EI, this test breaks — that is the signal to promote it.
2. **Claims vs. baseline** — do the numbers in `core/acquisition.py: BENCH_CLAIMS` (what the help
   tab reads) match the JSON.
3. **Candidate behaviour** — do the candidates (`packaging/bench_global.py`) pass through the real
   recommendation path and behave as defined. The evidence that the comparison was fair.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from core.acquisition import ACQUISITIONS, BENCH_CLAIMS, ExpectedImprovement
from core.dataset import build
from core.diagnostics import Gate
from core.recommend import Recommendation, recommend
from core.spec import ObjSpec, VarSpec
from core.surrogate import fit

ROOT = Path(__file__).resolve().parents[1]
BENCH_JSON = ROOT / "docs" / "bench_global.json"
OPEN = Gate(cond_count="OK", learnable="OK", discrim="OK", replicates="OK", locked=False)
SHIPPED = {"EI", "UCB", "Thompson"}          # the three on screen — anything else must pass validation
CANDIDATES = {"MES", "MIX4", "MIX4-TS", "GPUCB", "UCB2", "TS"}   # the comparison names in the JSON

sys.path.insert(0, str(ROOT / "packaging"))          # the name `packaging` collides with a PyPI package, so import it as a module
import bench_global  # noqa: E402


def _twopeak(u):
    u = np.asarray(u, dtype=float)
    broad = 0.6 * np.exp(-np.sum((u - [0.25, 0.3]) ** 2) / (2 * 0.22 ** 2))
    sharp = 1.0 * np.exp(-np.sum((u - [0.78, 0.72]) ** 2) / (2 * 0.07 ** 2))
    return float(broad + sharp)


def _dataset(n: int, inputs, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.random((n, len(inputs)))
    y = np.array([_twopeak(x) for x in X]) + rng.normal(0, 0.01, n)
    groups = {tuple(round(float(v), 6) for v in x): [float(v)] for x, v in zip(X, y)}
    return build(groups, inputs, ObjSpec("y"))


CONT = [VarSpec("x1", "", "continuous", 0.0, 1.0), VarSpec("x2", "", "continuous", 0.0, 1.0)]
GRID = [VarSpec("x1", "", "continuous", 0.0, 1.0, step=0.05),
        VarSpec("x2", "", "continuous", 0.0, 1.0, step=0.05)]


@pytest.fixture(scope="module")
def bench():
    assert BENCH_JSON.exists(), "docs/bench_global.json is missing — run packaging/bench_global.py"
    return json.loads(BENCH_JSON.read_text(encoding="utf-8"))


def _hit(bench, strategy, names):
    return float(np.mean([bench["summary"][b][strategy]["hit_rate"] for b in names]))


def _split(bench):
    multi = [b["name"] for b in bench["benches"] if b["multimodal"]]
    uni = [b["name"] for b in bench["benches"] if not b["multimodal"]]
    return multi, uni


# ══════════════════════════════════════════════════════════════════════
# 1. The decision rule — what is on screen needs evidence, and a candidate with evidence must be on screen
# ══════════════════════════════════════════════════════════════════════
def test_benchmark_baseline_has_the_full_design(bench):
    assert bench["budget"] == 40 and bench["initial"] == 11 and len(bench["seeds"]) == 10
    assert len(bench["benches"]) == 8 and len(bench["runs"]) == 8 * 7 * 10
    for b in bench["benches"]:
        for s in ("EI", *CANDIDATES):
            assert bench["summary"][b["name"]][s]["seeds"] == 10, (b["name"], s)
    multi, uni = _split(bench)
    assert len(multi) == 6 and len(uni) == 2


def test_only_strategies_that_beat_ei_on_multimodal_are_on_screen(bench):
    """Better than EI on multimodal and no loss on unimodal to go on screen — right now nothing beats it."""
    multi, uni = _split(bench)
    ei_multi, ei_uni = _hit(bench, "EI", multi), _hit(bench, "EI", uni)
    on_screen = {n for n, _ in ACQUISITIONS}
    assert on_screen == SHIPPED, f"acquisitions on screen without validation: {on_screen - SHIPPED}"
    for s in CANDIDATES:
        earns = _hit(bench, s, multi) > ei_multi and _hit(bench, s, uni) >= ei_uni - 0.1
        assert not earns, (f"{s} beat EI in the baseline (multimodal {_hit(bench, s, multi):.2f} > "
                           f"{ei_multi:.2f}) — time to promote it to core and fix this test")


def test_numbers_in_code_match_the_baseline(bench):
    multi, uni = _split(bench)
    assert BENCH_CLAIMS["multimodal_hit"] == pytest.approx(_hit(bench, "EI", multi), abs=0.005)
    assert BENCH_CLAIMS["unimodal_hit"] == pytest.approx(_hit(bench, "EI", uni), abs=0.005)
    best_alt = max(_hit(bench, s, multi) for s in CANDIDATES)
    assert BENCH_CLAIMS["best_alternative_multimodal_hit"] == pytest.approx(best_alt, abs=0.005)
    assert BENCH_CLAIMS["ucb_multimodal_hit"] == pytest.approx(_hit(bench, "UCB2", multi), abs=0.005)
    assert set(BENCH_CLAIMS["ei_hit"]) == {b["name"] for b in bench["benches"]}
    for name, hit in BENCH_CLAIMS["ei_hit"].items():
        assert hit == pytest.approx(bench["summary"][name]["EI"]["hit_rate"], abs=1e-9), name


def test_inner_maximiser_is_not_the_weak_link(bench):
    """Does the acquisition maximization over continuous variables (multi-start L-BFGS-B) find the same peak as differential evolution."""
    rows = bench["inner_maximiser"]
    assert len(rows) == 8 * 3 * 3, "8 functions × 3 seeds × 3 points in time"
    tol = bench["inner_tol"]
    for r in rows:
        scale = max(abs(r["de"]), abs(r["multistart"]), 1e-12)
        assert r["multistart"] >= r["de"] - tol * scale, r
        assert r["multistart_ge_de"], r


# ══════════════════════════════════════════════════════════════════════
# 2. Candidate behaviour — the evidence that the comparison was fair
# ══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("name", ["MES", "MIX4", "GPUCB"])
@pytest.mark.parametrize("inputs", [CONT, GRID], ids=["continuous", "gridded"])
def test_candidates_run_through_the_real_recommend_path(name, inputs):
    ds = _dataset(12, inputs, seed=1)
    rec = recommend(ds, inputs, OPEN, acquisition=bench_global.STRATEGIES[name](),
                    rng=np.random.default_rng(0))
    assert isinstance(rec, Recommendation)
    s = rec.suggestions[0]
    assert np.all(s.x_real >= -1e-9) and np.all(s.x_real <= 1 + 1e-9)
    assert np.isfinite(s.acq_value)
    if inputs is GRID:
        assert np.allclose(np.round(s.x_real / 0.05), s.x_real / 0.05), "must lie on the grid"


def test_mes_max_value_samples_lie_above_the_current_best():
    ds = _dataset(12, CONT, seed=2)
    model = fit(ds.XN, ds.y_mean)
    acq = bench_global.MaxValueEntropySearch()
    pool = np.random.default_rng(0).random((500, 2))
    best = float(ds.y_mean.max())
    acq.prepare(model, pool, best, np.random.default_rng(0))
    assert acq._fstar.shape == (acq.n_samples,)
    assert np.all(acq._fstar > best)
    score = acq.score(model, pool, best)
    assert score.shape == (500,) and np.all(np.isfinite(score)) and np.all(score >= -1e-9)


def test_explore_mix_takes_the_most_uncertain_point_every_fourth_turn():
    for n in (11, 12, 13):
        ds = _dataset(n, CONT, seed=3)
        model = fit(ds.XN, ds.y_mean)
        acq = bench_global.ExploreMix(period=4)
        X = np.random.default_rng(0).random((400, 2))
        best = float(ds.y_mean.max())
        acq.prepare(model, X, best)
        assert acq._explore is (n % 4 == 0)
        got = acq.score(model, X, best)
        _, std = model.predict(X)
        if n % 4 == 0:
            assert np.allclose(got, std), "an exploration turn returns σ as is"
            assert "this turn explores" in acq.describe()
        else:
            assert np.allclose(got, ExpectedImprovement().score(model, X, best)), "otherwise it equals EI"
