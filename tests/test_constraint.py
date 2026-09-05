# -*- coding: utf-8 -*-
"""Step · sum constraint · candidate count (SPEC_AMENDMENTS A6 — the input of gate ①).

Gate ① asks "are there more conditions to choose from than budget?". The rule for
counting them, and the path that picks points only inside a sum constraint
(composition A+B+C = 100 %), are pinned down here.
"""
from __future__ import annotations

import numpy as np
import pytest

from core.dataset import build
from core.design import initial_design, snap_to_constraint
from core.diagnostics import Gate
from core.project import Project
from core.recommend import Recommendation, candidate_pool, recommend
from core.spec import (CANDIDATE_CAP, ObjSpec, SumConstraint, VarSpec, candidate_summary,
                       count_candidates)


def _open() -> Gate:
    return Gate(cond_count="OK", learnable="OK", discrim="OK", replicates="OK")


# ══════════════════════════════════════════════════════════════════════
# Step
# ══════════════════════════════════════════════════════════════════════
def test_step_counts_levels_like_the_instrument():
    v = VarSpec("power", "W", "continuous", 150, 200, step=10.0)
    assert v.n_levels() == 6                                  # 150·160·…·200
    assert v.snap(163.0) == 160.0 and v.snap(166.0) == 170.0
    assert v.snap(999.0) == 200.0                             # outside the range → the last grid point


def test_step_is_only_for_continuous_and_must_fit_the_range():
    with pytest.raises(ValueError):
        VarSpec("n", "", "integer", 1, 5, step=1.0)
    with pytest.raises(ValueError):
        VarSpec("x", "", "continuous", 0, 1, step=0.0)
    with pytest.raises(ValueError):
        VarSpec("x", "", "continuous", 0, 1, step=2.0)


def test_continuous_without_step_is_infinite():
    assert VarSpec("x", "", "continuous", 0, 1).n_levels() is None
    assert VarSpec("n", "", "integer", 3, 7).n_levels() == 5
    assert VarSpec("c", "", "categorical", levels=("a", "b", "c")).n_levels() == 3


# ══════════════════════════════════════════════════════════════════════
# Candidate count — the numerator of gate ①
# ══════════════════════════════════════════════════════════════════════
NANO = [VarSpec("power", "W", "continuous", 150, 200, step=10.0),
        VarSpec("dwell", "s", "integer", 3, 7)]


def test_nanofilm_has_30_candidates_not_15_measured():
    """Count the conditions that can be chosen (6 × 5 = 30), not the ones already measured (15)."""
    assert count_candidates(NANO) == 30
    assert candidate_summary(NANO) == "30 candidate conditions (power 6 × dwell 5)"


def test_any_stepless_continuous_makes_the_count_infinite():
    inputs = [VarSpec("power", "W", "continuous", 150, 200), NANO[1]]
    assert count_candidates(inputs) is None
    assert "infinite" in candidate_summary(inputs) and "power" in candidate_summary(inputs)


def test_count_stops_at_the_cap():
    inputs = [VarSpec(f"x{i}", "", "integer", 0, 999) for i in range(4)]   # 1e12
    assert count_candidates(inputs) == CANDIDATE_CAP
    assert "or more" in candidate_summary(inputs)


def test_composition_sum_counts_only_feasible_mixtures():
    """A+B+C = 100, step 10 → ways to split 0..100 in tens across three = C(12,2) = 66."""
    abc = [VarSpec(n, "%", "continuous", 0, 100, step=10.0) for n in "ABC"]
    eq = SumConstraint(("A", "B", "C"), 100.0, "eq")
    assert count_candidates(abc, eq) == 66
    le = SumConstraint(("A", "B", "C"), 100.0, "le")
    assert count_candidates(abc, le) == 286                   # C(13,3)
    assert "constraint A + B + C = 100" in candidate_summary(abc, eq)


def test_perovskite_style_fraction_sum_to_one():
    """CsPbI + FAPbI + MAPbI = 1, step 0.05 → C(22,2) = 231."""
    xs = [VarSpec(n, "", "continuous", 0, 1, step=0.05) for n in ("CsPbI", "FAPbI", "MAPbI")]
    c = SumConstraint(("CsPbI", "FAPbI", "MAPbI"), 1.0)
    assert count_candidates(xs, c) == 231


def test_constraint_with_a_free_variable_multiplies():
    abc = [VarSpec(n, "%", "continuous", 0, 100, step=10.0) for n in "AB"]
    abc.append(VarSpec("T", "C", "integer", 20, 22))
    c = SumConstraint(("A", "B"), 100.0)
    assert count_candidates(abc, c) == 11 * 3                 # once A is fixed, B is fixed too


def test_constraint_over_stepless_variables_is_infinite():
    ab = [VarSpec(n, "%", "continuous", 0, 100) for n in "AB"]
    assert count_candidates(ab, SumConstraint(("A", "B"), 100.0)) is None


# ══════════════════════════════════════════════════════════════════════
# Sum constraint — definition and validation
# ══════════════════════════════════════════════════════════════════════
def test_constraint_rejects_impossible_or_ill_fitting_definitions():
    abc = [VarSpec(n, "%", "continuous", 0, 40, step=10.0) for n in "ABC"]
    with pytest.raises(ValueError):                           # maximum sum 120 < 200
        SumConstraint(("A", "B", "C"), 200.0).validate(abc)
    with pytest.raises(ValueError):                           # 95 cannot be made with step 10
        SumConstraint(("A", "B", "C"), 95.0).validate(abc)
    with pytest.raises(ValueError):                           # missing variable
        SumConstraint(("A", "Z"), 50.0).validate(abc)
    with pytest.raises(ValueError):                           # a single variable
        SumConstraint(("A",), 50.0)
    cat = abc[:2] + [VarSpec("C", "", "categorical", levels=("x", "y"))]
    with pytest.raises(ValueError):
        SumConstraint(("A", "B", "C"), 50.0).validate(cat)
    SumConstraint(("A", "B", "C"), 100.0).validate(abc)       # fine


def test_snap_keeps_the_sum_on_the_grid():
    abc = [VarSpec(n, "%", "continuous", 0, 100, step=10.0) for n in "ABC"]
    c = SumConstraint(("A", "B", "C"), 100.0)
    x = snap_to_constraint(np.array([33.3, 33.3, 33.4]), abc, c)
    assert x.sum() == pytest.approx(100.0)
    assert all(abs(v / 10 - round(v / 10)) < 1e-9 for v in x)


# ══════════════════════════════════════════════════════════════════════
# Initial design · candidates · recommendation — all inside the constraint
# ══════════════════════════════════════════════════════════════════════
ABC = [VarSpec(n, "%", "continuous", 0, 100, step=5.0) for n in "ABC"]
EQ = SumConstraint(("A", "B", "C"), 100.0)


def test_initial_design_satisfies_the_constraint():
    X = initial_design(11, ABC, seed=0, constraint=EQ)
    assert X.shape == (11, 3)
    assert np.allclose(X.sum(1), 100.0)
    assert np.all((X >= 0) & (X <= 100))
    assert np.allclose(X / 5, np.round(X / 5))               # on the grid
    assert len(np.unique(np.round(X, 6), axis=0)) >= 9        # distinct points


def test_le_constraint_design_stays_under_the_total():
    le = SumConstraint(("A", "B"), 30.0, "le")
    ab = [VarSpec(n, "wt%", "continuous", 0, 30, step=1.0) for n in "AB"]
    X = initial_design(12, ab, seed=1, constraint=le)
    assert np.all(X.sum(1) <= 30.0 + 1e-9)


def _mixture_dataset():
    rng = np.random.default_rng(3)
    groups = {}
    for _ in range(14):
        a = float(rng.integers(0, 21) * 5)
        b = float(rng.integers(0, (100 - a) // 5 + 1) * 5)
        c = 100.0 - a - b
        y = -((a - 40) ** 2 + (b - 30) ** 2) / 500.0
        groups[(a, b, c)] = [y + rng.normal(0, 0.05) for _ in range(3)]
    return build(groups, ABC, ObjSpec("y"))


def test_candidates_and_recommendation_respect_the_constraint():
    ds = _mixture_dataset()
    pool = candidate_pool(ds, ABC, size=500, constraint=EQ)
    lo, span = ds.X.min(0), np.ptp(ds.X, axis=0)
    real = lo + pool * np.where(span > 0, span, 1.0)
    assert len(pool) > 50
    assert np.allclose(real.sum(1), 100.0)
    result = recommend(ds, ABC, _open(), batch=3, constraint=EQ)
    assert isinstance(result, Recommendation)
    for s in result.suggestions:
        assert EQ.satisfied(s.x_real, ABC)
        assert np.allclose(s.x_real / 5, np.round(s.x_real / 5))


def test_project_saves_step_and_constraint(tmp_path):
    p = Project(name="composition", inputs=ABC, objective=ObjSpec("y"), constraint=EQ, budget_total=40)
    path = p.save(str(tmp_path / "c.seqopt"))
    q = Project.load(path)
    assert q.constraint == EQ
    assert q.inputs[0].step == 5.0
    assert q.n_candidates() == 231                            # C(22,2)


def test_project_refuses_a_constraint_that_names_missing_variables(tmp_path):
    p = Project(name="composition", inputs=ABC, objective=ObjSpec("y"), constraint=EQ)
    d = p.to_dict()
    d["constraint"]["names"] = ["A", "Z"]
    with pytest.raises(ValueError):
        Project.from_dict(d)


# ══════════════════════════════════════════════════════════════════════
# Setup tab — the step column and the sum-constraint section (SPEC_AMENDMENTS A6)
# ══════════════════════════════════════════════════════════════════════
def test_setup_tab_round_trips_step_and_constraint(qapp):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QTableWidgetItem
    from ui.tab_setup import SetupTab

    p = Project(name="composition", inputs=ABC, objective=ObjSpec("y"), constraint=EQ, budget_total=40)
    tab = SetupTab(p)
    inputs, errs = tab.collect()
    assert not errs and [v.step for v in inputs] == [5.0, 5.0, 5.0]
    assert tab.con_on.isChecked()
    assert tab.collect_constraint(inputs) == (EQ, "")
    assert "231 candidate conditions" in tab.cand_hint.text()   # the input of gate ① shows on the setup tab
    assert "passes" in tab.cand_hint.text()

    # clearing the step makes the candidates infinite — ① still passes, but the sentence changes
    tab.vars.setItem(0, 5, QTableWidgetItem(""))
    assert p.inputs[0].step is None
    assert p.constraint == EQ
    assert "infinite" in tab.cand_hint.text()

    # removing one constraint variable leaves the definition incomplete — not saved, and the reason is shown
    tab.con_vars.item(2).setCheckState(Qt.Unchecked)
    assert p.constraint is not None and p.constraint.names == ("A", "B")
    tab.con_vars.item(1).setCheckState(Qt.Unchecked)
    assert p.constraint is None
    assert "at least 2" in tab.con_msg.text()

    # switching it off removes the constraint
    tab.con_on.setChecked(False)
    assert p.constraint is None and tab.con_msg.text() == ""


def test_setup_tab_flags_candidates_below_budget(qapp):
    from ui.tab_setup import SetupTab
    p = Project(name="nano", inputs=NANO, objective=ObjSpec("G/D"), budget_total=40)
    tab = SetupTab(p)
    assert "30 candidate conditions" in tab.cand_hint.text()
    assert "requirement ① unmet" in tab.cand_hint.text()
    tab.budget.setValue(20)
    assert "passes" in tab.cand_hint.text()


def test_setup_tab_reports_measurements_that_break_the_constraint(qapp):
    from ui.tab_setup import SetupTab
    p = Project(name="composition", inputs=ABC, objective=ObjSpec("y"), constraint=EQ)
    p.add([50.0, 50.0, 0.0], 1.0)
    p.add([50.0, 40.0, 0.0], 1.0)                             # sum 90 — violates it
    tab = SetupTab(p)
    assert "1 measured row" in tab.con_msg.text() and "violate" in tab.con_msg.text()


def test_setup_tab_explains_that_categorical_has_no_editor_yet(qapp):
    """Choosing categorical is refused in the user's language, not with a Python exception message (FINDINGS F10)."""
    from ui.tab_setup import SetupTab
    p = Project(name="nano", inputs=NANO, objective=ObjSpec("G/D"), budget_total=40)
    tab = SetupTab(p)
    cb = tab.vars.cellWidget(0, 2)
    cb.setCurrentIndex([cb.itemData(i) for i in range(cb.count())].index("categorical"))
    specs, errs = tab.collect()
    assert len(specs) == len(NANO) - 1
    assert any("categorical" in e and "yet" in e for e in errs)
    assert not any("levels" in e for e in errs)
