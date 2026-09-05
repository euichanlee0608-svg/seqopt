# -*- coding: utf-8 -*-
"""M4, recommendations — is the gate held **structurally** (F-20 ~ F-25 · F-42).

What this file protects is a **property**, not a feature. The one path to a
recommendation is `recommend()`, and without a passed gate it returns a
`Locked` that carries no suggestions. Screens cannot misuse what is simply
not in the object.
"""
from __future__ import annotations

import numpy as np
import pytest

from core.acquisition import ExpectedImprovement, ThompsonSampling, UpperConfidenceBound
from core.dataset import build, group_measurements
from core.diagnostics import Gate, discriminability, gate, loocv_r2
from core.project import Project
from core.recommend import (Locked, Recommendation, candidate_pool, recommend,
                            recommended_reps)
from core.spec import ObjSpec, VarSpec, count_candidates
from core.surrogate import fit
from tests.loaders import external, synthetic


@pytest.fixture(scope="module")
def syn():
    return synthetic()


@pytest.fixture(scope="module")
def syn_inputs():
    # The live measured range: the all-zero conditions (power 190, dwell 7) are
    # excluded, so declaring beyond 180/6 would make extrapolation legitimate.
    # Power gets an instrument step (SPEC_AMENDMENTS A6). It is 5 W, not the
    # fixture's 10 W: with 10 W every grid point but (180, 3) is already
    # measured, and the batch tests need unmeasured candidates to pick from.
    return [VarSpec("power", "W", "continuous", 150, 180, step=5.0),
            VarSpec("dwell", "s", "integer", 3, 6)]


@pytest.fixture(scope="module")
def locked_gate(syn, syn_inputs):
    """The fixture's real gate — locked (learnability fails by design)."""
    d = discriminability(syn.reps)
    r = loocv_r2(syn.XN, syn.y_mean)
    return gate(count_candidates(syn_inputs), 40, r.r2, d, syn.frac_with_reps)


@pytest.fixture(scope="module")
def open_gate():
    return Gate(cond_count="OK", learnable="OK", discrim="OK", replicates="OK", locked=False)


# ══════════════════════════════════════════════════════════════════════
# the gate — this file's reason to exist
# ══════════════════════════════════════════════════════════════════════
def test_locked_gate_returns_no_suggestions(syn, syn_inputs, locked_gate):
    """Locked means **no suggestions in the object.** No screen can take them out by mistake."""
    assert locked_gate.locked
    result = recommend(syn, syn_inputs, locked_gate)
    assert isinstance(result, Locked)
    assert not hasattr(result, "suggestions")
    assert result.reasons
    assert "no recommendation" in result.headline


def test_open_gate_returns_suggestions(syn, syn_inputs, open_gate):
    result = recommend(syn, syn_inputs, open_gate)
    assert isinstance(result, Recommendation)
    assert len(result.suggestions) == 1
    assert not result.gate_bypassed


def test_override_marks_the_result(syn, syn_inputs, locked_gate):
    """Forcing works — but **it leaves a mark** (§10 risk table)."""
    result = recommend(syn, syn_inputs, locked_gate, override=True)
    assert isinstance(result, Recommendation)
    assert result.gate_bypassed is True


def test_override_off_by_default(syn, syn_inputs, locked_gate):
    """The default is the safe side. Forcing must be explicit."""
    assert isinstance(recommend(syn, syn_inputs, locked_gate), Locked)


# ══════════════════════════════════════════════════════════════════════
# candidates — no lookahead, and only measurable values (principle P2)
# ══════════════════════════════════════════════════════════════════════
def test_candidates_exclude_already_measured(syn, syn_inputs):
    pool = candidate_pool(syn, syn_inputs, size=800)
    gap = np.linalg.norm(pool[:, None, :] - syn.XN[None, :, :], axis=2)
    assert (gap.min(axis=1) > 1e-9).all()


def test_integer_variables_land_on_measurable_values(syn, syn_inputs, open_gate):
    """A dwell of 5.83 seconds cannot go on an instruction sheet."""
    result = recommend(syn, syn_inputs, open_gate, batch=5)
    for s in result.suggestions:
        assert float(s.x_real[1]).is_integer(), f"dwell is not an integer: {s.x_real}"


def test_suggestion_label_is_human_readable(syn, syn_inputs, open_gate):
    result = recommend(syn, syn_inputs, open_gate)
    label = result.suggestions[0].label
    assert "power" in label and "W" in label
    assert "dwell" in label and "s" in label


def test_recommended_reps_follows_current_median(syn):
    """One measurement of a new condition drags D down — the sheet says how many times."""
    assert recommended_reps(syn) == 3          # the fixture's replicate median


# ══════════════════════════════════════════════════════════════════════
# extrapolation — never blocked, always marked
# ══════════════════════════════════════════════════════════════════════
def _sine_dataset(lo: float = 0.0, hi: float = 6.0):
    """A learnable one-variable dataset. The measured range is always [lo, hi]."""
    groups = {(float(x),): [float(np.sin(x) + 1.5), float(np.sin(x) + 1.53)]
              for x in np.linspace(lo, hi, 9)}
    return build(groups, [VarSpec("x", "", "continuous", lo, hi)], ObjSpec("y"))


def test_extrapolation_is_flagged(open_gate):
    """Beyond the measured range, the model has learned nothing.

    Measured x ∈ [0, 6], declared [0, 20] — the outside carries the most
    uncertainty, so the acquisition goes there. Not blocked, **always marked.**
    """
    ds = _sine_dataset()
    wide = [VarSpec("x", "", "continuous", 0, 20)]
    result = recommend(ds, wide, open_gate)
    assert any(s.extrapolated for s in result.suggestions)
    assert any("outside the measured range" in w for w in result.warnings)


def test_extrapolation_flag_is_computed_from_the_point_itself(open_gate):
    """The flag depends on **the coordinates alone**, whatever the acquisition picked."""
    from core.acquisition import Pick
    from core.recommend import _to_suggestion

    ds = _sine_dataset()
    inputs = [VarSpec("x", "", "continuous", 0, 20)]
    inside = _to_suggestion(Pick(np.array([0.5]), 1.0, 0.0, 0.1), ds, inputs)
    outside = _to_suggestion(Pick(np.array([2.5]), 1.0, 0.0, 0.1), ds, inputs)
    assert not inside.extrapolated
    assert outside.extrapolated
    assert outside.x_real[0] > ds.X[:, 0].max()


def test_no_extrapolation_flag_inside_measured_range(syn, syn_inputs, open_gate):
    result = recommend(syn, syn_inputs, open_gate, batch=6)
    assert not any(s.extrapolated for s in result.suggestions)
    assert result.warnings == []


def test_flat_acquisition_still_returns_something(syn, syn_inputs, open_gate):
    """On the fixture, EI is effectively flat (far below 1% of the range, by design).

    A recommendation still comes out — the stopping rule and the Model tab say
    "nothing left to learn" instead. The point is never to hand over some
    arbitrary point in silence.
    """
    result = recommend(syn, syn_inputs, open_gate)
    assert len(result.suggestions) == 1
    assert result.acq_max < 0.01 * result.response_range


# ══════════════════════════════════════════════════════════════════════
# batches · the stopping rule
# ══════════════════════════════════════════════════════════════════════
def test_batch_returns_distinct_conditions(syn, syn_inputs, open_gate):
    result = recommend(syn, syn_inputs, open_gate, batch=4)
    xs = np.array([s.x_norm for s in result.suggestions])
    assert len(result.suggestions) == 4
    assert len(np.unique(np.round(xs, 9), axis=0)) == 4


def test_stop_rule_fires_after_three_flat_cycles(syn, syn_inputs, open_gate):
    """The fixture's EI is negligible — three flat cycles advise stopping (F-24)."""
    tiny = [1e-9, 1e-9]                          # the two previous cycles
    result = recommend(syn, syn_inputs, open_gate, acq_history=tiny)
    assert result.stop_advised
    assert "1%" in result.stop_reason


def test_stop_rule_silent_when_there_is_still_gain():
    """p3ht still has things to learn — the rule must stay silent."""
    ds = external("p3ht")
    inputs = [VarSpec(f"x{i}", "", "continuous", float(ds.X[:, i].min()),
                      float(ds.X[:, i].max())) for i in range(ds.X.shape[1])]
    g = Gate(locked=False)
    result = recommend(ds, inputs, g)
    assert not result.stop_advised


# ══════════════════════════════════════════════════════════════════════
# part swaps — does the same contract survive
# ══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("acq", [ExpectedImprovement(), UpperConfidenceBound(2.0),
                                 ThompsonSampling()])
def test_any_acquisition_produces_a_valid_suggestion(syn, syn_inputs, open_gate, acq):
    result = recommend(syn, syn_inputs, open_gate, acquisition=acq,
                       rng=np.random.default_rng(0))
    assert isinstance(result, Recommendation)
    assert len(result.suggestions) == 1
    assert acq.describe() in result.acquisition_label


def test_swapping_surrogate_needs_no_other_change(syn, syn_inputs, open_gate):
    """Swapping the surrogate leaves the path untouched — only a label changes."""
    result = recommend(syn, syn_inputs, open_gate,
                       surrogate_name="random-forest",
                       model=fit(syn.XN, syn.y_mean, "random-forest", n_estimators=40))
    assert isinstance(result, Recommendation)
    assert "forest" in result.surrogate_label.lower()
    assert len(result.suggestions) == 1


def test_ucb_beta_shows_up_in_the_label(syn, syn_inputs, open_gate):
    """The report alone must reveal which b was used (the no-unexplained-constants rule)."""
    result = recommend(syn, syn_inputs, open_gate, acquisition=UpperConfidenceBound(3.5))
    assert "3.5" in result.acquisition_label


# ══════════════════════════════════════════════════════════════════════
# the screen — does it merely display what the core decided
# ══════════════════════════════════════════════════════════════════════
@pytest.fixture
def tab(qapp, syn, syn_inputs):
    from ui.tab_recommend import RecommendTab
    p = Project(inputs=syn_inputs, objective=ObjSpec("G/D ratio", "a.u.", "max"),
                budget_total=40)
    t = RecommendTab(p)
    return t


def test_acquisition_is_chosen_in_one_place_only(tab):
    """Two places to choose and nobody knows which applied.

    An attribute `self.acquisition = None` once shadowed the method of the
    same name and blew up the whole screen — the name clash is fenced by test.
    """
    assert callable(tab.acquisition), 'acquisition must be a method'
    assert tab.acquisition().describe().startswith('EI')
    tab.method.setCurrentIndex(1)                       # explore wider (UCB)
    assert 'UCB' in tab.acquisition().describe()
    assert tab.method_why.text(), 'it must say when to use it'
    tab.method.setCurrentIndex(0)


def test_every_method_says_when_to_use_it():
    """A name without a when-to-use cannot be chosen between."""
    from core.acquisition import ACQUISITIONS
    for name, cls in ACQUISITIONS:
        assert getattr(cls, 'when', ''), f'{name} has no when explanation'
        assert getattr(cls, 'label', '') != name, f'{name} has no plain-language label'


def test_tab_shows_lock_and_disables_export(tab, syn, locked_gate):
    tab.set_context(syn, locked_gate, fit(syn.XN, syn.y_mean), ExpectedImprovement())
    tab.request()
    assert isinstance(tab.result, Locked)
    assert tab.table.rowCount() == 0
    assert not tab.accept.isEnabled()
    assert not tab.export.isEnabled()
    assert "no recommendation" in tab.status.text()


def test_tab_lists_suggestions_when_open(tab, syn, syn_inputs, open_gate):
    tab.set_context(syn, open_gate, fit(syn.XN, syn.y_mean), ExpectedImprovement())
    tab.batch.setValue(3)
    tab.request()
    assert isinstance(tab.result, Recommendation)
    assert tab.table.rowCount() == 3
    assert tab.accept.isEnabled()
    # 2 inputs + suggested reps + mean + σ + acq value + note
    assert tab.table.columnCount() == len(syn_inputs) + 5


def test_accepting_emits_rows_for_the_data_tab(tab, syn, open_gate, qapp):
    tab.set_context(syn, open_gate, fit(syn.XN, syn.y_mean), ExpectedImprovement())
    tab.request()
    got = []
    tab.points_accepted.connect(got.append)
    tab._accept()
    assert len(got) == 1
    (inputs, note), = got[0]
    assert len(inputs) == 2
    assert "suggested" in note


# ══════════════════════════════════════════════════════════════════════
# pending rows — must never enter the math as zeros
# ══════════════════════════════════════════════════════════════════════
def test_pending_rows_stay_out_of_the_dataset():
    """A pre-inserted suggested row is **not a measurement yet.**

    Entering the math as 0 would wreck the surface, the discriminability and
    the gate wholesale.
    """
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    p.add([1.0], 0.5)
    p.add([2.0], 0.9)
    pending = p.add([7.0], 0.0)
    pending["pending"] = True

    assert p.dataset().n_conditions == 2
    assert p.used == 2                              # the budget counts it as unspent too
    assert len(group_measurements(p.measurements)) == 2


def test_filling_a_pending_row_confirms_it(qapp):
    from ui.tab_data import DataTab
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    p.add([1.0], 0.5)
    tab = DataTab(p)
    tab.insert_pending([([7.0], "suggested")])
    assert p.measurements[-1]["pending"] is True
    assert p.dataset().n_conditions == 1

    tab.table.item(1, 1).setText("1.7")             # a measured value lands in the cell
    assert "pending" not in p.measurements[-1]
    assert p.dataset().n_conditions == 2
