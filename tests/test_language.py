# -*- coding: utf-8 -*-
"""Choosing the language — and the window that comes back in it.

Three rules the app depends on and a person cannot check by eye every release:
  · a first run follows the OS, a saved choice beats the OS, `SEQOPT_LANG` beats both
  · the env override is for **one run** (CI captures both languages) and is never saved
  · switching rebuilds the window: same project object, same page, all text in the new language
"""
from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolButton

from core import i18n
from core.project import Project
from core.spec import ObjSpec, VarSpec


@pytest.fixture
def settings(tmp_path, monkeypatch):
    """QSettings pointed at a throwaway file — a test must not touch the developer's real one."""
    was = QSettings.defaultFormat()
    QSettings.setDefaultFormat(QSettings.IniFormat)
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(tmp_path))
    monkeypatch.delenv("SEQOPT_LANG", raising=False)
    yield QSettings("seqopt", "seqopt")
    QSettings.setDefaultFormat(was)


@pytest.fixture
def window(qapp, settings):
    """A window on a small real project, closed afterwards however many rebuilds it went through."""
    from ui.main_window import MainWindow
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    for x, y in [(1.0, 0.5), (1.0, 0.54), (2.0, 0.9), (3.0, 1.2)]:
        p.add([x], y)
    win = MainWindow(p)
    win.resize(1024, 660)
    win.show()
    qapp.processEvents()
    yield win
    for w in {win, getattr(qapp, "_seqopt_window", None)}:
        if w is not None:
            w.runner.cancel()
            w._dirty = False
            w.close()
    if hasattr(qapp, "_seqopt_window"):
        del qapp._seqopt_window
    qapp.processEvents()


def _menu_entry(win, code: str) -> QAction:
    """The Language-menu entry for `code`, found the way a user finds it — by walking the menu bar."""
    for top in win.menuBar().actions():
        menu = top.menu()
        for a in menu.actions() if menu is not None else ():
            if a.text() == i18n.NAMES[code]:
                assert a.isCheckable(), f"{a.text()!r} should show which language is running"
                return a
    raise AssertionError(f"no menu entry labelled {i18n.NAMES[code]!r}")


def _rail(win) -> list[str]:
    return [win.nav.item(i).text() for i in range(win.nav.count())]


# ══════════════════════════════════════════════════════════════════════
# which language a run starts in
# ══════════════════════════════════════════════════════════════════════
def test_the_first_run_follows_the_operating_system(monkeypatch):
    monkeypatch.delenv("SEQOPT_LANG", raising=False)
    assert i18n.default_language(None, "ko_KR") == "ko"
    assert i18n.default_language(None, "en_US") == "en"
    assert i18n.default_language(None, None) == "en"


def test_a_saved_choice_beats_the_operating_system(monkeypatch):
    monkeypatch.delenv("SEQOPT_LANG", raising=False)
    assert i18n.default_language("en", "ko_KR") == "en"
    assert i18n.default_language("ko", "en_US") == "ko"


def test_the_env_override_beats_both_and_is_never_saved(settings, monkeypatch):
    """SEQOPT_LANG exists so CI can capture both languages — it must not become the user's choice."""
    settings.setValue("language", "en")
    monkeypatch.setenv("SEQOPT_LANG", "ko")
    assert i18n.default_language(settings.value("language"), "en_US") == "ko"
    assert settings.value("language") == "en"


# ══════════════════════════════════════════════════════════════════════
# switching rebuilds the window
# ══════════════════════════════════════════════════════════════════════
def test_the_menu_rebuilds_the_window_in_korean_and_back(qapp, window, settings):
    project = window.project
    window.shell.setCurrentIndex(1)
    window.nav.setCurrentRow(1)
    qapp.processEvents()
    assert _rail(window)[:3] == ["Setup", "Data", "Diagnose"]

    _menu_entry(window, "ko").trigger()
    qapp.processEvents()
    ko = qapp._seqopt_window
    assert ko is not window
    assert ko.project is project                 # the object, not the file — unsaved edits survive
    assert _rail(ko)[:3] == ["설정", "데이터", "진단"]
    assert ko.shell.currentIndex() == 1 and ko.nav.currentRow() == 1
    assert settings.value("language") == "ko"

    _menu_entry(ko, "en").trigger()
    qapp.processEvents()
    back = qapp._seqopt_window
    assert _rail(back)[:3] == ["Setup", "Data", "Diagnose"]
    assert back.project is project
    assert settings.value("language") == "en"


def test_switching_to_the_language_already_running_changes_nothing(qapp, window):
    assert window.switch_language("en") is window


def test_the_start_screen_button_switches_the_language(qapp, window, settings):
    window.shell.setCurrentIndex(0)
    qapp.processEvents()
    button = next(b for b in window.shell.widget(0).findChildren(QToolButton)
                  if b.text() == i18n.NAMES["ko"])
    button.click()
    qapp.processEvents()
    ko = qapp._seqopt_window
    assert i18n.language() == "ko"
    assert ko.shell.currentIndex() == 0          # still on the start screen, now in Korean
    assert _rail(ko)[:2] == ["설정", "데이터"]
    assert settings.value("language") == "ko"


def test_unsaved_work_is_not_asked_about_twice(qapp, window):
    """The old window hands its unsaved state to the new one; closing it must not raise a dialog."""
    window._dirty = True
    _menu_entry(window, "ko").trigger()
    qapp.processEvents()
    assert qapp._seqopt_window._dirty is True
    assert window._dirty is False


# ══════════════════════════════════════════════════════════════════════
# the header, in whichever language, however long the name
# ══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("lang", ("en", "ko"))
def test_a_long_project_name_is_elided_not_cut(qapp, settings, lang):
    """The bundled examples have short names, so the layout gate never sees this one.

    Korean is wider per character than English, so the header has to survive both.
    """
    from tests.clipcheck import clipped_texts
    from ui.main_window import MainWindow

    i18n.set_language(lang)
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    p.name = "Annealing temperature and dwell time versus crystallinity, third round, June 2026"
    p.path = "/a/deep/folder/" + "n" * 40 + ".seqopt"
    win = MainWindow(p)
    win.resize(1024, 660)
    win.shell.setCurrentIndex(1)
    win.show()
    qapp.processEvents()
    try:
        assert win.title.text().endswith("…") and win.title.text() != p.name
        assert win.title.toolTip() == p.name              # the whole name is still readable
        assert not [f for f in clipped_texts(win) if "_Elided" in f]
    finally:
        win.runner.cancel()
        win._dirty = False
        win.close()
        qapp.processEvents()
