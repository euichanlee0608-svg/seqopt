# -*- coding: utf-8 -*-
"""Does a first-time user find their way (onboarding).

The usability bar (§9-3) ultimately needs a human, but **whether the screen
says what to do next** is checkable by machine.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from core.project import Project
from core.spec import ObjSpec, VarSpec
from ui import theme
from ui.stepper import DATA, DIAG, MODEL, RECOMMEND, REPORT, SETUP, assess

from ui.start_screen import EXAMPLE_DIR as EXAMPLES


@pytest.fixture
def win(qapp):
    theme.apply(qapp)
    from ui.main_window import MainWindow
    return MainWindow()


# ══════════════════════════════════════════════════════════════════════
# the start screen
# ══════════════════════════════════════════════════════════════════════
def test_program_opens_on_the_start_screen(win):
    """It opens on "choose what to do", not on an empty table with a red error."""
    assert win.shell.currentIndex() == 0


def test_an_example_project_ships_with_the_program():
    """A first-time user has never seen the tool working (the JMP Sample Data pattern)."""
    files = list(EXAMPLES.glob("*.seqopt"))
    assert files, "examples/ has no example project"
    p = Project.load(str(files[0]))
    assert p.dataset().n_conditions > p.budget_total     # the example passes gate ①
    assert len(p.measurements) > 50


def test_opening_the_example_lands_on_the_work_screen(win, qapp):
    win._open_path(str(sorted(EXAMPLES.glob("*.seqopt"))[0]))
    for _ in range(4):
        win.runner.wait()
        qapp.processEvents()
    assert win.shell.currentIndex() == 1
    assert win.project.dataset().n_conditions > 40


def test_recent_files_survive_a_restart(win, tmp_path):
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 1)], objective=ObjSpec("y"))
    p.add([0.5], 1.0)
    path = p.save(str(tmp_path / "r.seqopt"))
    win.remember_recent(path)
    assert path in win.recent_files()


# ══════════════════════════════════════════════════════════════════════
# what to do next — the screen decides
# ══════════════════════════════════════════════════════════════════════
def test_empty_project_says_define_variables(win):
    r = assess(win.project, None, None)
    assert r.current == SETUP
    assert "variable" in r.next_action
    assert "Next" in win.guide.text()


def test_variables_but_no_data_says_enter_measurements():
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    r = assess(p, None, None)
    assert r.current == DATA
    assert "measurement" in r.next_action


def test_locked_gate_points_at_the_prescription():
    from core.diagnostics import Gate
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    p.add([1.0], 0.5)
    p.add([2.0], 0.9)
    r = assess(p, p.dataset(), Gate(locked=True, reasons=["learnability R² ≤ 0"]))
    assert r.current == DIAG
    assert "prescription" in r.next_action


def test_open_gate_points_at_the_recommendation():
    from core.diagnostics import Gate
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    for x, y in [(1.0, 0.5), (2.0, 0.9), (3.0, 1.2)]:
        p.add([x], y)
    r = assess(p, p.dataset(), Gate(locked=False))
    assert r.current == RECOMMEND
    assert "met" in r.next_action


# ══════════════════════════════════════════════════════════════════════
# tab gating — blocked steps always say why
# ══════════════════════════════════════════════════════════════════════
def test_new_project_only_opens_setup_and_help(win):
    enabled = [i for i in range(win.nav.count())
               if win.nav.item(i).flags() & Qt.ItemIsEnabled]
    assert enabled == [SETUP, 6], "a new project opens only Setup and Help"


def test_every_blocked_step_explains_why(win):
    """A gray button with no reason is indistinguishable from a broken one."""
    for i in range(win.nav.count()):
        if not (win.nav.item(i).flags() & Qt.ItemIsEnabled):
            assert win.nav.item(i).toolTip(), f"tab {i} is locked with no reason"


def test_steps_open_as_the_project_fills_in():
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    assert assess(p, None, None).ready[DATA] is True          # variables exist → Data opens
    assert assess(p, None, None).ready[DIAG] is False

    for x, y in [(1.0, 0.5), (2.0, 0.9), (3.0, 1.2)]:
        p.add([x], y)
    r = assess(p, p.dataset(), None)
    assert r.ready[DIAG] and r.ready[MODEL] and r.ready[REPORT]


# ══════════════════════════════════════════════════════════════════════
# does the screen speak the user's language
# ══════════════════════════════════════════════════════════════════════
def test_status_bar_never_leaks_a_python_exception(win):
    """Exception text used to leak into the status bar verbatim."""
    text = win.badges.text()
    for leak in ("Traceback", "Error", "raise", "There are no measurements", "None"):
        assert leak not in text, f"exception text is visible: {text}"


def test_empty_variable_table_guides_instead_of_scolding(win):
    """A red error before the user has done anything reads as "what did I break"."""
    setup = win.tab_setup
    assert not setup.vars.isVisible() or setup.vars.rowCount() == 0
    assert not setup.empty_hint.isHidden()
    assert "Add variable" in setup.empty_hint.text()
    assert setup.var_msg.text() == "", "no error text in the empty state"
