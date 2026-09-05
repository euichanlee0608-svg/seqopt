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

from ui.start_screen import EXAMPLES, example_files


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


def test_both_example_projects_ship_with_the_program():
    """A first-time user has never seen the tool working (the JMP Sample Data pattern).

    The passing example (synthetic annealing) comes first, the real-data one (P3HT) second.
    """
    files = example_files()
    assert [f.name for f in files][:2] == [name for name, _, _ in EXAMPLES]
    success, p3ht = (Project.load(str(f)) for f in files[:2])
    assert success.dataset().n_conditions == 14 and len(success.measurements) == 42
    assert "simulated" in success.name.lower()
    assert p3ht.dataset().n_conditions == 48 and len(p3ht.measurements) == 69


def test_start_screen_shows_one_card_per_example(qapp):
    from ui.start_screen import StartScreen, _Card
    s = StartScreen()
    titles = [c.layout().itemAt(0).widget().text() for c in s.findChildren(_Card)]
    assert any("Synthetic annealing" in t for t in titles)
    assert any("P3HT" in t for t in titles)
    assert titles.index(next(t for t in titles if "Synthetic annealing" in t)) \
        < titles.index(next(t for t in titles if "P3HT" in t))


def test_opening_the_example_lands_on_the_work_screen(win, qapp):
    win._open_path(str(example_files()[1]))          # P3HT
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


def test_inserted_recommendation_points_back_at_the_data_tab():
    """Once a recommendation is in the data table, say 'measure the gray rows', not 'get candidates'."""
    from core.diagnostics import Gate
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    for x, y in [(1.0, 0.5), (2.0, 0.9), (3.0, 1.2)]:
        p.add([x], y)
    p.add([4.0], 0.0, note="recommended")["pending"] = True      # the same mark tab_data.insert_pending sets
    r = assess(p, p.dataset(), Gate(locked=False))
    assert r.current == DATA
    assert "1 recommended" in r.next_action and "gray row" in r.next_action


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
