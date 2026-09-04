# -*- coding: utf-8 -*-
"""Surrogates · acquisitions · initial design — the swappable parts (§5-2 · §5-7 · F-20 ~ F-24).

This file verifies **contracts**, not numeric expectations. Registering a new
part must leave it passing untouched.
"""
from __future__ import annotations

import numpy as np
import pytest

from core.acquisition import (ACQUISITIONS, ExpectedImprovement, ThompsonSampling,
                              UpperConfidenceBound, batch_picks, best_of, make_acquisition,
                              maximise_continuous, should_stop, unmeasured)
from core.design import initial_design, maximin_lhs, suggest_initial_size
from core.diagnostics import sensitivity
from core.protocols import Acquisition, Surrogate
from core.registry import Registry
from core.spec import VarSpec
from core.surrogate import (DEFAULT_SURROGATE, LENGTH_SCALE_BOUNDS, SURROGATES, fit,
                            make_surrogate)
from tests.loaders import synthetic


@pytest.fixture(scope="module")
def syn():
    return synthetic()


@pytest.fixture(scope="module")
def toy():
    """A one-variable toy problem, with the true maximum near x=0.8."""
    XN = np.array([[0.0], [0.2], [0.45], [0.6], [1.0]])
    y = np.array([0.1, 0.35, 0.55, 0.62, 0.30])
    return XN, y, fit(XN, y)


# ══════════════════════════════════════════════════════════════════════
# The registry — can a new part attach without touching existing files
# ══════════════════════════════════════════════════════════════════════
def test_registry_rejects_duplicate_names():
    r: Registry = Registry("test")

    @r.register("A")
    class _A:
        pass

    with pytest.raises(ValueError, match="already registered"):
        @r.register("A")
        class _B:
            pass


def test_registry_error_lists_what_is_available():
    """An unknown name answers with **what exists** — a typo is never left to hunt alone."""
    with pytest.raises(KeyError) as e:
        make_acquisition("EL")                 # a typo of EI
    assert "EI" in str(e.value)


def test_new_acquisition_needs_no_change_elsewhere():
    """Registering alone makes it constructible and screen-listed (open-closed)."""
    r: Registry[Acquisition] = Registry("acquisition")

    @r.register("Greedy")
    class Greedy:
        label = "Greedy — mean only"
        supports_continuous = True

        def score(self, model, X, best, rng=None):
            return model.predict(X)[0]

        def describe(self):
            return "Greedy"

    made = r.create("Greedy")
    assert isinstance(made, Acquisition)       # satisfies the protocol
    assert r.label_of("Greedy") == "Greedy — mean only"


def test_registered_parts_satisfy_their_protocols(toy):
    XN, y, _ = toy
    for name, _ in SURROGATES:
        model = make_surrogate(name).fit(XN, y)
        assert isinstance(model, Surrogate)
        mean, std = model.predict(XN)
        assert mean.shape == std.shape == (len(XN),)
        assert (std >= 0).all()
    for name, _ in ACQUISITIONS:
        assert isinstance(make_acquisition(name), Acquisition)


# ══════════════════════════════════════════════════════════════════════
# The default surrogate — must stay pinned (SPEC_AMENDMENTS A1)
# ══════════════════════════════════════════════════════════════════════
def test_default_surrogate_is_the_pinned_gp():
    assert DEFAULT_SURROGATE == "gp-matern-ard"
    assert isinstance(make_surrogate(), type(make_surrogate(DEFAULT_SURROGATE)))


def test_kernel_is_ard(syn):
    """Per-variable length scales are what the sensitivity view (F-33) is made of."""
    model = fit(syn.XN, syn.y_mean)
    assert len(model.length_scales()) == syn.XN.shape[1]


def test_fit_is_deterministic(syn):
    """restarts>0, so without random_state the regression tests would wobble."""
    a = fit(syn.XN, syn.y_mean).length_scales()
    b = fit(syn.XN, syn.y_mean).length_scales()
    assert np.allclose(a, b)


def test_surrogate_without_length_scales_reports_none(toy):
    """The random forest has no length scales. It returns None instead of inventing zeros."""
    XN, y, _ = toy
    rf = make_surrogate("random-forest", n_estimators=30).fit(XN, y)
    assert rf.length_scales() is None
    assert sensitivity(rf, ["x"]) == []       # sensitivity stays empty too — no drawing of absent values


def test_unfitted_surrogate_fails_loudly():
    with pytest.raises(RuntimeError, match="fit"):
        make_surrogate().predict(np.zeros((1, 2)))


# ══════════════════════════════════════════════════════════════════════
# Sensitivity (§5-6 · F-33) — the screen shows 'bigger = more sensitive'
# ══════════════════════════════════════════════════════════════════════
def test_sensitivity_is_inverse_length_scale(syn):
    model = fit(syn.XN, syn.y_mean)
    ls = model.length_scales()
    pairs = sensitivity(model, ["power", "dwell"])
    assert [n for n, _ in pairs] == ["power", "dwell"]
    assert sum(p for _, p in pairs) == pytest.approx(100.0, abs=1e-6)
    tighter = int(np.argmin(ls))               # the shorter length scale is the more sensitive axis
    assert pairs[tighter][1] == max(p for _, p in pairs)


def test_sensitivity_zero_at_upper_bound():
    """A length scale stuck at the search bound reads as "no influence" (0)."""
    hi = LENGTH_SCALE_BOUNDS[1]

    class Fake:
        def length_scales(self):
            return np.array([hi, 0.2])

    out = sensitivity(Fake(), ["a", "b"])
    assert out[0][1] == 0.0
    assert out[1][1] == pytest.approx(100.0)


# ══════════════════════════════════════════════════════════════════════
# Initial design (F-22)
# ══════════════════════════════════════════════════════════════════════
def test_suggested_initial_size_is_quarter_of_budget():
    assert suggest_initial_size(40) == 11        # 40 × 27.5%
    assert suggest_initial_size(4) == 3          # never fewer than 3


def test_maximin_lhs_is_space_filling():
    """maximin beats random on nearest-neighbor distance — why grids and random are not used."""
    k, dim = 12, 2
    lhs = maximin_lhs(k, dim, seed=0)
    rand = np.random.default_rng(0).random((k, dim))

    def min_dist(P):
        d = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
        return d[np.triu_indices(len(P), 1)].min()

    assert min_dist(lhs) > min_dist(rand)
    assert lhs.min() >= 0.0 and lhs.max() <= 1.0


def test_initial_design_respects_types():
    inputs = [VarSpec("power", "W", "continuous", 150, 200),
              VarSpec("dwell", "s", "integer", 3, 7)]
    X = initial_design(10, inputs, seed=0)
    assert X.shape == (10, 2)
    assert (X[:, 0] >= 150).all() and (X[:, 0] <= 200).all()
    assert np.allclose(X[:, 1], np.round(X[:, 1]))
    assert (X[:, 1] >= 3).all() and (X[:, 1] <= 7).all()


# ══════════════════════════════════════════════════════════════════════
# Acquisition functions (§5-7)
# ══════════════════════════════════════════════════════════════════════
def test_ei_is_nonnegative(toy):
    XN, y, model = toy
    grid = np.linspace(0, 1, 101).reshape(-1, 1)
    assert (ExpectedImprovement().score(model, grid, y.max()) >= -1e-12).all()


def test_ei_is_small_at_the_measured_best(toy):
    """At the measured best, EI is nearly 0 — it never says measure it again."""
    XN, y, model = toy
    acq = ExpectedImprovement()
    here = acq.score(model, XN[int(np.argmax(y))].reshape(1, -1), y.max())[0]
    grid = acq.score(model, np.linspace(0, 1, 101).reshape(-1, 1), y.max())
    assert here < grid.max()


def test_ucb_beta_moves_toward_uncertainty(toy):
    """A larger b picks the more uncertain spot."""
    XN, y, model = toy
    grid = np.linspace(0, 1, 201).reshape(-1, 1)
    _, sd = model.predict(grid)
    lo = sd[int(np.argmax(UpperConfidenceBound(0.5).score(model, grid, y.max())))]
    hi = sd[int(np.argmax(UpperConfidenceBound(4.0).score(model, grid, y.max())))]
    assert hi >= lo


def test_thompson_is_random_but_finite(toy):
    XN, y, model = toy
    grid = np.linspace(0, 1, 50).reshape(-1, 1)
    acq = ThompsonSampling()
    a = acq.score(model, grid, y.max(), np.random.default_rng(1))
    b = acq.score(model, grid, y.max(), np.random.default_rng(2))
    assert np.isfinite(a).all()
    assert not np.allclose(a, b)               # sampling — different every draw


def test_thompson_refuses_continuous_optimisation(toy):
    XN, y, model = toy
    with pytest.raises(ValueError, match="continuous"):
        maximise_continuous(model, ThompsonSampling(), y.max(), np.array([[0.0, 1.0]]))


def test_describe_includes_parameters():
    """A report saying just "UCB" invites the question of which b it used."""
    assert "2" in UpperConfidenceBound(2.0).describe()
    assert "4" in UpperConfidenceBound(4.0).describe()


# ══════════════════════════════════════════════════════════════════════
# Maximization · batches · stopping
# ══════════════════════════════════════════════════════════════════════
def test_continuous_maximisation_beats_dense_grid(toy):
    XN, y, model = toy
    acq = ExpectedImprovement()
    pick = maximise_continuous(model, acq, y.max(), np.array([[0.0, 1.0]]))
    grid = acq.score(model, np.linspace(0, 1, 1001).reshape(-1, 1), y.max())
    assert pick.acq_value >= grid.max() - 1e-6
    assert 0.0 <= pick.x_norm[0] <= 1.0


def test_best_of_picks_from_candidates(toy):
    XN, y, model = toy
    cand = np.array([[0.1], [0.75], [0.9]])
    pick = best_of(model, ExpectedImprovement(), cand, y.max())
    assert any(np.allclose(pick.x_norm, c) for c in cand)


def test_best_is_measured_value_not_truth(toy):
    """Swap best for a (larger) true value and EI shrinks — violating P3 changes the recommendation."""
    XN, y, model = toy
    acq = ExpectedImprovement()
    grid = np.linspace(0, 1, 101).reshape(-1, 1)
    assert acq.score(model, grid, y.max() + 0.2).max() < acq.score(model, grid, y.max()).max()


def test_batch_returns_distinct_points(toy):
    """kriging believer — never picks the same point twice (F-21)."""
    XN, y, model = toy
    cand = unmeasured(np.linspace(0, 1, 21).reshape(-1, 1), XN)
    picks = batch_picks(model, ExpectedImprovement(), cand, y.max(), 3, DEFAULT_SURROGATE)
    xs = np.array([p.x_norm for p in picks])
    assert len(picks) == 3
    assert len(np.unique(np.round(xs, 9), axis=0)) == 3


def test_batch_stops_when_pool_exhausted(toy):
    XN, y, model = toy
    cand = np.array([[0.72], [0.85]])
    assert len(batch_picks(model, ExpectedImprovement(), cand, y.max(), 5,
                           DEFAULT_SURROGATE)) == 2


def test_unmeasured_excludes_measured():
    allX = np.array([[0.0], [0.5], [1.0]])
    left = unmeasured(allX, np.array([[0.5]]))
    assert len(left) == 2
    assert not any(np.allclose(x, [0.5]) for x in left)


def test_should_stop_needs_three_consecutive():
    assert not should_stop([0.005, 0.005], 1.0)              # only two
    assert should_stop([0.5, 0.005, 0.005, 0.005], 1.0)      # three in a row
    assert not should_stop([0.005, 0.05, 0.005], 1.0)        # broken streak
    assert not should_stop([0.005] * 3, 0.0)                 # zero range → withhold judgment
