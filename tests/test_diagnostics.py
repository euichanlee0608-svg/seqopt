# -*- coding: utf-8 -*-
"""Regression tests — the diagnostics reproduce their expectations within 1e-3.

Two expectation sources, both pinned:
  · synthetic_expect.json — computed by tests/data/make_synthetic.py with its
    own numpy formulas, never by core/ (two independent implementations)
  · verify_external.json / verify_terrain.json — the original validation
    study's numbers for the three public datasets

When this file breaks, the kernel, the preprocessing or a definition changed.
Before touching an expectation, **say what changed first** — auto-updating a
baseline is how regressions get through.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest

from core.diagnostics import (D_COMFORTABLE, D_LEVELS, D_RECOMMENDED, D_THRESHOLD,
                              NUGGET_CLASSES, NUGGET_THRESHOLD, discriminability, gate,
                              loocv_r2, nugget_ratio, replicate_plan, required_reps)
from core.spec import VarSpec, count_candidates
from tests.loaders import DATA, external, synthetic

TOL = 1e-3
# The synthetic fixture's design space — power has an instrument step of 10 W (SPEC_AMENDMENTS A6)
SYN_INPUTS = [VarSpec("power", "W", "continuous", 150, 190, step=10.0),
              VarSpec("dwell", "s", "integer", 3, 7)]


@pytest.fixture(scope="module")
def syn():
    return synthetic()


@pytest.fixture(scope="module")
def expected():
    with open(os.path.join(DATA, "synthetic_expect.json"), encoding="utf-8") as f:
        syn_json = json.load(f)
    with open(os.path.join(DATA, "verify_external.json"), encoding="utf-8") as f:
        ext_json = json.load(f)
    with open(os.path.join(DATA, "verify_terrain.json"), encoding="utf-8") as f:
        terrain_json = json.load(f)
    return syn_json, ext_json, terrain_json


# ══════════════════════════════════════════════════════════════════════
# Synthetic lab spreadsheet — loading and exclusion (T-01)
# ══════════════════════════════════════════════════════════════════════
def test_synthetic_condition_counts(syn, expected):
    exp, _, _ = expected
    assert syn.n_conditions_all == exp["conditions_all"] == 25
    assert syn.n_conditions == exp["conditions_live"] == 15
    assert syn.n_excluded_conditions == exp["conditions_dead"] == 10
    assert syn.n_measurements == exp["measurements"] == 45


def test_synthetic_replicate_distribution(syn, expected):
    exp, _, _ = expected
    assert syn.rep_distribution == {int(k): v for k, v in exp["rep_dist"].items()}


def test_synthetic_replicate_fraction(syn):
    # 14 of the 15 conditions carry replicates — one singleton, by design
    assert syn.frac_with_reps == pytest.approx(14 / 15, abs=TOL)


# ══════════════════════════════════════════════════════════════════════
# Discriminability (§5-3 · F-11 ~ F-13)
# ══════════════════════════════════════════════════════════════════════
def test_synthetic_discriminability(syn, expected):
    """core's numbers match the generator's independent numpy computation."""
    exp, _, _ = expected
    d = discriminability(syn.reps)
    assert d.sigma_w == pytest.approx(exp["sigma_w"], abs=TOL)
    assert d.sigma_b == pytest.approx(exp["sigma_b"], abs=TOL)
    assert d.D[1] == pytest.approx(exp["D"]["1"], abs=TOL)
    assert d.D[5] == pytest.approx(exp["D"]["5"], abs=TOL)
    assert d.n_median == exp["n_median"] == 3.0
    assert d.total_ss == pytest.approx(exp["total_ss"], abs=1e-9)
    assert d.total_df == exp["total_df"]


def test_synthetic_bootstrap_ci(syn):
    """The interval straddles the gate at 1.0 → undecided (principle P5).

    The fixture was designed to sit in exactly this regime — a point estimate
    above 1 that honestly cannot claim to have passed.
    """
    d = discriminability(syn.reps)
    assert d.ci_lo is not None and d.ci_hi is not None
    assert d.ci_lo < 1.0 < d.ci_hi
    assert 1.0 < d.D[1] < 2.0
    assert d.verdict == "UNDECIDED"
    # deterministic — the bootstrap seed is fixed
    e = discriminability(syn.reps)
    assert (e.ci_lo, e.ci_hi) == (d.ci_lo, d.ci_hi)


def test_synthetic_dominant_condition(syn, expected):
    """One condition is engineered to carry ~48% of the within-condition variance (F-13)."""
    exp, _, _ = expected
    d = discriminability(syn.reps)
    assert d.top_share == pytest.approx(exp["top_share"], abs=0.05)
    power, dwell = syn.X[d.top_condition]
    assert f"{power:.0f}W-{dwell:.0f}s" == exp["top_cond"] == "180W-6s"
    assert d.sigma_w_drop_top == pytest.approx(exp["sw_drop_top"], abs=TOL)
    assert d.D_drop_top == pytest.approx(exp["D_drop_top"], abs=TOL)


def test_required_reps_matches_prescription(syn):
    """The prescription card (F-16) — a target D back-computes the replicates n."""
    d = discriminability(syn.reps)
    n = required_reps(d.sigma_b, d.sigma_w, target_D=2.0)
    assert d.D[n] >= 2.0
    if n > 1:
        assert d.D[n - 1] < 2.0


def test_threshold_levels_are_ordered_and_documented():
    """The gate (1.0) stays as specified; recommended/comfortable sit above it, each with a basis."""
    assert D_THRESHOLD == 1.0                       # spec §5-3 — do not change
    assert D_THRESHOLD < D_RECOMMENDED < D_COMFORTABLE
    assert [lv[0] for lv in D_LEVELS] == [D_THRESHOLD, D_RECOMMENDED, D_COMFORTABLE]
    for value, name, meaning, basis in D_LEVELS:
        assert name and meaning and len(basis) > 10  # every threshold carries its basis
    assert "1.96" in D_LEVELS[1][3]                 # recommended 2 = two standard errors (95%)
    assert "ndc" in D_LEVELS[2][3]                  # comfortable 3.5 = AIAG MSA ndc ≥ 5
    limits = [lim for lim, _ in NUGGET_CLASSES]
    assert limits == sorted(limits) and limits[-1] == float("inf")


def test_replicate_plan_matches_required_reps(syn):
    """The plan table — same n as required_reps per target, extras summed per condition."""
    d = discriminability(syn.reps)
    counts = [len(v) for v in syn.reps]
    rows = replicate_plan(d.sigma_b, d.sigma_w, counts)
    assert [r["target"] for r in rows] == [D_THRESHOLD, D_RECOMMENDED, D_COMFORTABLE]
    for r in rows:
        assert r["n"] == required_reps(d.sigma_b, d.sigma_w, r["target"])
        assert r["extra"] == sum(max(0, r["n"] - c) for c in counts)
        assert r["D"] >= r["target"]                # with that n, the target is met
    assert rows[0]["n"] == 1 and rows[0]["extra"] == 0      # D(1) > 1 already
    with pytest.raises(ValueError):
        replicate_plan(0.0, d.sigma_w, counts)      # σb = 0 → no n can help


# ══════════════════════════════════════════════════════════════════════
# Surface learnability (§5-4 · F-14) — the study's central number
# ══════════════════════════════════════════════════════════════════════
def test_synthetic_loocv_r2_is_negative(syn):
    """The fixture's between-condition signal is spatially unstructured,
    so the surface must be unlearnable — worse than answering the mean."""
    r = loocv_r2(syn.XN, syn.y_mean)
    assert r.r2 < 0
    assert r.ss_res > r.ss_tot          # the definition of R² < 0
    assert not r.low_sample_warning     # 15 conditions ≥ 8
    # deterministic — restarts are seeded
    assert loocv_r2(syn.XN, syn.y_mean).r2 == pytest.approx(r.r2, abs=1e-9)


def test_loocv_learns_a_learnable_surface():
    """The counterpart: on a smooth function the same pipeline must say YES.
    Without this, a loocv that always fails would still pass the suite."""
    rng = np.random.default_rng(0)
    XN = rng.random((18, 2))
    y = np.sin(3 * XN[:, 0]) + XN[:, 1] ** 2 + rng.normal(0, 0.01, 18)
    assert loocv_r2(XN, y).r2 > 0.5


def test_low_sample_warning_threshold():
    """The low-sample warning fires only below 8 conditions (§5-4)."""
    XN = np.linspace(0, 1, 6).reshape(-1, 1)
    y = np.array([0.1, 0.3, 0.2, 0.5, 0.4, 0.6])
    assert loocv_r2(XN, y).low_sample_warning


# ══════════════════════════════════════════════════════════════════════
# Nugget ratio (§5-5 · F-15)
# ══════════════════════════════════════════════════════════════════════
def test_synthetic_nugget_ratio_is_rough(syn):
    d = discriminability(syn.reps)
    r = nugget_ratio(syn.XN, syn.y_mean, sigma_w=d.sigma_w)
    assert r is not None
    assert r.ratio > NUGGET_THRESHOLD and r.rough
    assert r.noise_share is not None and r.noise_share > 0.5
    # the ratio is nugget/sill by definition
    assert r.ratio == pytest.approx(r.nugget / r.sill, abs=1e-12)


def test_nugget_returns_none_when_pairs_are_too_few():
    """4 conditions give 6 pairs — forcing a value would invent rough/smooth."""
    XN = np.array([[0.0], [0.3], [0.7], [1.0]])
    y = np.array([1.0, 1.2, 0.8, 1.1])
    assert nugget_ratio(XN, y) is None


# ══════════════════════════════════════════════════════════════════════
# The three public datasets — same yardstick, same numbers
# ══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("name,key", [
    ("p3ht", "P3HT-CNT"), ("perovskite", "Perovskite"), ("agnp", "AgNP"),
])
def test_external_discriminability(name, key, expected):
    _, ext, _ = expected
    e = ext[key]
    d = discriminability(external(name).reps)
    assert external(name).n_conditions == e["cond"]
    assert d.sigma_w == pytest.approx(e["sigma_w"], abs=TOL)
    assert d.sigma_b == pytest.approx(e["sigma_b"], abs=TOL)
    assert d.D[1] == pytest.approx(e["D"], abs=5e-3)


@pytest.mark.parametrize("name,key", [
    ("p3ht", "P3HT-CNT"), ("perovskite", "Perovskite"), ("agnp", "AgNP"),
])
def test_external_nugget_ratio(name, key, expected):
    _, _, terrain = expected
    e = terrain[key]
    ds = external(name)
    r = nugget_ratio(ds.XN, ds.y_mean)
    assert r.ratio == pytest.approx(e["nugget_ratio"], abs=TOL)


def test_nugget_separates_learnable_from_not(expected):
    """The nugget ratio separates learnable data from unlearnable data.

    ⚠ The original write-up claimed the *ordering* matches R² exactly; the
       actual values do not support that (AgNP has a lower nugget ratio than
       P3HT-CNT and a lower R²). What holds is the **separation**, so the
       separation is what gets verified.
    """
    _, _, terrain = expected
    pairs = sorted((v["nugget_ratio"], float(v["r2"])) for v in terrain.values())
    smooth = [r2 for ng, r2 in pairs if ng <= NUGGET_THRESHOLD]
    rough = [r2 for ng, r2 in pairs if ng > NUGGET_THRESHOLD]
    assert smooth and rough
    assert all(r2 > 0 for r2 in smooth), "every smooth terrain is learnable"
    assert all(r2 < 0 for r2 in rough), "every rough terrain is not"
    assert min(smooth) > max(rough)


# ══════════════════════════════════════════════════════════════════════
# The gate (§12-1 · F-17)
# ══════════════════════════════════════════════════════════════════════
def test_synthetic_gate_is_locked(syn):
    """The fixture locks on **learnability (②)**, with discriminability undecided —
    the same failure profile as the original study's lab data."""
    d = discriminability(syn.reps)
    r = loocv_r2(syn.XN, syn.y_mean)
    g = gate(count_candidates(SYN_INPUTS), budget=40, r2=r.r2, disc=d,
             frac_with_reps=syn.frac_with_reps)
    assert g.learnable == "FAIL"        # R² < 0
    assert g.discrim == "UNDECIDED"     # the interval straddles 1.0
    assert g.cond_count == "FAIL"       # 25 candidates (power step 10 W × dwell 5) ≤ budget 40
    assert g.replicates == "OK"         # 14/15 = 93%
    assert g.locked


def test_gate_counts_candidates_not_measured_conditions(syn):
    """Gate ① compares **the number of selectable candidates** with the budget (SPEC_AMENDMENTS A6).

    Not the number of conditions already measured (15) — before anything is
    measured there are 0 conditions, and if ① failed then nothing could ever
    start; conversely, on a continuous design with infinitely many candidates,
    "measuring everything is better" is meaningless.
    """
    d = discriminability(syn.reps)
    assert count_candidates(SYN_INPUTS) == 25
    assert gate(25, 40, r2=0.5, disc=d, frac_with_reps=1.0).cond_count == "FAIL"   # 25 ≤ 40
    assert gate(25, 24, r2=0.5, disc=d, frac_with_reps=1.0).cond_count == "OK"     # 25 > 24
    no_step = [VarSpec("power", "W", "continuous", 150, 190), SYN_INPUTS[1]]
    assert count_candidates(no_step) is None                                       # infinite
    assert gate(None, 40, r2=0.5, disc=d, frac_with_reps=1.0).cond_count == "OK"
    g = gate(25, 40, r2=0.5, disc=d, frac_with_reps=1.0)
    assert any("measuring everything is better" in r for r in g.reasons)


def test_gate_stays_locked_while_r2_pending(syn):
    """The lock holds while R² is computing — never opens optimistically (principle P1)."""
    d = discriminability(syn.reps)
    g = gate(200, budget=40, r2=None, disc=d, frac_with_reps=1.0)
    assert g.learnable == "PENDING"
    assert g.locked


def test_gate_opens_when_all_pass():
    """Everything passing must unlock — the gate is not a machine that only says no."""
    reps = [np.array([1.0 + 0.3 * i, 1.02 + 0.3 * i, 0.98 + 0.3 * i]) for i in range(12)]
    d = discriminability(reps)
    g = gate(100, budget=40, r2=0.7, disc=d, frac_with_reps=1.0)
    assert d.verdict == "OK"
    assert not g.locked


def test_discriminability_uncomputable_without_replicates():
    """Without replicates, D is not computed. No assumed value is substituted."""
    reps = [np.array([v]) for v in (1.0, 1.2, 0.9, 1.4)]
    d = discriminability(reps)
    assert d.sigma_w is None
    assert d.verdict == "UNCOMPUTABLE"
    g = gate(100, budget=40, r2=0.5, disc=d, frac_with_reps=0.0)
    assert g.locked
