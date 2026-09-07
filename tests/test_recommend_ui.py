# -*- coding: utf-8 -*-
"""The Recommend screen at a narrow window — nothing cut off, nothing over-precise.

Five variables with four-decimal values used to run the suggestion table off the
right edge of a 1024 px window ("table wider than its viewport (905px in 766px)"),
and the values were printed as `89.0915 %` — a precision no instrument can be set
to. The screen now puts the one suggestion to act on in a card and the runners-up
in a table that always fits, and every value is shown at the precision the
variable itself declares.

Both halves are measured here, in both languages, with a synthetic five-variable
dataset built in the test.
"""
from __future__ import annotations

import numpy as np
import pytest

from core.acquisition import ExpectedImprovement
from core.diagnostics import Gate
from core.project import Project
from core.recommend import Recommendation
from core.spec import ObjSpec, VarSpec
from core.surrogate import fit
from tests.clipcheck import clipped_texts

NARROW = 1000        # the page area left inside the 1024 px minimum window

# one variable per precision rule: step 10 → 0 · step 0.5 → 1 · step 0.25 → 2 ·
# integer → 0 · no step over a range of 1 → 3
INPUTS = [VarSpec("temperature", "°C", "continuous", 150, 350, step=10.0),
          VarSpec("dwell time", "min", "continuous", 5, 60, step=0.5),
          VarSpec("pressure", "bar", "continuous", 0.25, 2.0, step=0.25),
          VarSpec("passes", "", "integer", 1, 9),
          VarSpec("flow fraction", "", "continuous", 0.0, 1.0)]
DECIMALS = [0, 1, 2, 0, 3]


def _project() -> Project:
    """A five-variable project with 16 conditions × 2 replicates — enough for a GP to fit."""
    p = Project(inputs=INPUTS, objective=ObjSpec("yield", "%", "max"), budget_total=60)
    rng = np.random.default_rng(7)
    for i in range(16):
        x = [float(np.round(rng.uniform(150, 350) / 10) * 10),
             float(np.round(rng.uniform(5, 60) * 2) / 2),
             float(np.round(rng.uniform(0.25, 2.0) * 4) / 4),
             float(rng.integers(1, 10)),
             float(rng.uniform(0, 1))]
        base = 0.01 * x[0] + 0.05 * x[1] - 2.0 * x[2] + 0.3 * x[3] + 4.0 * x[4]
        for _ in range(2):
            p.add(x, base + rng.normal(0, 0.05))
    return p


def _tab(qapp, width: int = NARROW):
    """The screen, shown at the given width, wired to an open gate.

    Built after the language is set — the widgets take their text once, the way
    the real window does (it is rebuilt on a language switch).
    """
    from ui.tab_recommend import RecommendTab
    p = _project()
    ds = p.dataset()
    w = RecommendTab(p)
    w.resize(width, 640)
    w.show()
    w.set_context(ds, Gate(cond_count="OK", learnable="OK", discrim="OK",
                           replicates="OK", locked=False),
                  fit(ds.XN, ds.y_mean), ExpectedImprovement())
    qapp.processEvents()
    return w


@pytest.fixture
def tab(qapp):
    w = _tab(qapp)
    yield w
    w.close()
    qapp.processEvents()


def _card_values(tab) -> list[str]:
    return [value.text() for _, value in tab._card_rows]


# ══════════════════════════════════════════════════════════════════════
# the precision rule — the value has to be settable on the instrument
# ══════════════════════════════════════════════════════════════════════
def test_card_shows_each_value_at_its_declared_precision(tab, qapp):
    tab.request()
    qapp.processEvents()
    assert isinstance(tab.result, Recommendation)
    for text, spec, want in zip(_card_values(tab), INPUTS, DECIMALS):
        number = text.split(" ")[0]
        got = len(number.split(".")[1]) if "." in number else 0
        assert got == want, f"{spec.name}: {text!r} has {got} decimals, wants {want}"


def test_alternatives_use_the_same_precision(tab, qapp):
    tab.batch.setValue(4)
    tab.request()
    qapp.processEvents()
    assert tab.table.rowCount() == 3                 # ranks 2, 3, 4
    for r in range(tab.table.rowCount()):
        for c, want in enumerate(DECIMALS):
            number = tab.table.item(r, c).text()
            got = len(number.split(".")[1]) if "." in number else 0
            assert got == want, f"row {r} column {c}: {number!r}"


# ══════════════════════════════════════════════════════════════════════
# the layout — five variables at 1000 px, in both languages
# ══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("lang", ("en", "ko"))
def test_nothing_is_cut_off_at_a_narrow_window(qapp, lang):
    from core import i18n
    i18n.set_language(lang)
    tab = _tab(qapp)
    try:
        tab.batch.setValue(4)
        tab.request()
        qapp.processEvents()
        assert tab.table.isVisibleTo(tab) and tab.table.columnCount() == len(INPUTS) + 3
        assert not tab.table.horizontalScrollBar().isVisible()
        assert not clipped_texts(tab)
    finally:
        tab.close()
        qapp.processEvents()


# ══════════════════════════════════════════════════════════════════════
# the response in the user's frame — the internal number is never printed
# ══════════════════════════════════════════════════════════════════════
def test_the_log_example_answers_in_the_users_own_units(qapp):
    """P3HT is modelled in log10. The screen said "best measured so far 2.931"
    while the Data tab, two clicks away, read 853 S/cm — the same measurement.
    The status line now speaks in S/cm, and the card says the transform out loud."""
    from core.project import Project
    from ui.start_screen import example_files
    from ui.tab_recommend import RecommendTab

    project = Project.load(str(next(p for p in example_files() if "p3ht" in p.stem)))
    assert project.objective.log                      # the premise of this test
    ds = project.dataset()
    tab = RecommendTab(project)
    tab.resize(NARROW, 640)
    tab.show()
    tab.set_context(ds, Gate(cond_count="OK", learnable="OK", discrim="OK",
                             replicates="OK", locked=False),
                    fit(ds.XN, ds.y_mean), ExpectedImprovement())
    try:
        tab.request()
        qapp.processEvents()
        assert isinstance(tab.result, Recommendation)
        assert "S/cm" in tab.status.text(), tab.status.text()
        assert "log10" in tab.card_meta.text(), tab.card_meta.text()
    finally:
        tab.close()
        qapp.processEvents()


def test_a_lone_suggestion_hides_the_alternatives_table(tab, qapp):
    tab.batch.setValue(1)
    tab.request()
    qapp.processEvents()
    assert len(tab.result.suggestions) == 1
    assert not tab.table.isVisibleTo(tab)
    assert not tab.alt_title.isVisibleTo(tab)
    assert tab.card.isVisibleTo(tab)


def test_the_lock_hides_card_and_table(tab, qapp):
    tab.request()
    qapp.processEvents()
    assert tab.card.isVisibleTo(tab)
    tab.set_context(tab.dataset,
                    Gate(cond_count="FAIL", learnable="FAIL", discrim="OK",
                         replicates="OK", locked=True),
                    tab.model, ExpectedImprovement())
    tab.request()
    qapp.processEvents()
    assert not tab.card.isVisibleTo(tab)
    assert not tab.table.isVisibleTo(tab)
    assert not tab.accept.isEnabled()
