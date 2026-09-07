# -*- coding: utf-8 -*-
"""No clipped text, in either language, at either window size.

Every tab of every bundled example is walked exactly the way CI photographs it (`ui.shots.visit_tabs`),
and every visible widget is measured (`tests/clipcheck.py`). One finding fails the test, with the
tab, the widget and the text — so a label that no longer fits after a wording change is caught
here, not by a user.
"""
from __future__ import annotations

import pytest

from core import i18n
from core.project import Project
from ui.start_screen import EXAMPLES as BUNDLED, example_files

MIN, LAPTOP = (1024, 660), (1366, 768)
# The catalogued examples only — a .seqopt dropped next to them (a lab's own project) is
# its owner's to gate, with its own cases, so the count here stays the one the help tab claims.
EXAMPLES = {p.stem: p for p in example_files() if p.name in {name for name, _, _ in BUNDLED}}
CASES = [(name, size) for name in EXAMPLES for size in (MIN, LAPTOP)]


def _walk(qapp, project, size, lang):
    from ui.main_window import MainWindow
    from ui.shots import visit_tabs
    from tests.clipcheck import clipped_texts

    i18n.set_language(lang)
    win = MainWindow(project)
    win.resize(*size)
    win.show()
    qapp.processEvents()
    findings = []
    try:
        win.shell.setCurrentIndex(0)
        qapp.processEvents()
        findings += [f"[start] {f}" for f in clipped_texts(win)]
        for name, _widget in visit_tabs(qapp, win, "layout"):
            if name.endswith("_full"):          # the scroll interior — the same widgets as the tab itself
                continue
            findings += [f"[{name}] {f}" for f in clipped_texts(win)]
    finally:
        win._dirty = False
        win.close()
        qapp.processEvents()
    return findings


@pytest.mark.parametrize("lang", ("en", "ko"))
@pytest.mark.parametrize("name,size", CASES, ids=[f"{n}-{s[0]}" for n, s in CASES])
def test_no_clipped_text(qapp, real_fonts, name, size, lang):
    findings = _walk(qapp, Project.load(str(EXAMPLES[name])), size, lang)
    assert not findings, f"{len(findings)} clipped:\n  " + "\n  ".join(findings)


@pytest.mark.parametrize("lang", ("en", "ko"))
def test_unlearned_surface_keeps_its_validation_figure_readable(qapp, real_fonts, lang):
    """Neither bundled example locks, so the walk above never sees the Model tab with the
    'unlearned' banner and a two-line readout above it. At the minimum window height those once
    squeezed the 2×2 validation figure to 176 px — axes eight pixels tall, labels spilling out.
    The figure keeps the 300 px four readable panels need and the page scrolls."""
    from ui.main_window import MainWindow
    from ui.shots import visit_tabs
    from tests.clipcheck import clipped_texts
    from tests.loaders import synthetic_project

    i18n.set_language(lang)
    win = MainWindow(synthetic_project())
    win.resize(*MIN)
    win.show()
    qapp.processEvents()
    findings, seen = [], False
    try:
        for name, _widget in visit_tabs(qapp, win, "layout"):
            if name == "06_model_checks":
                seen = True
                assert not win.tab_model.banner.isHidden()          # the case this test is about
                assert win.tab_model.check_canvas.height() >= 300
                findings = clipped_texts(win)
    finally:
        win._dirty = False
        win.close()
        qapp.processEvents()
    assert seen
    assert not findings, f"{len(findings)} clipped:\n  " + "\n  ".join(findings)


@pytest.mark.parametrize("lang", ("en", "ko"))
@pytest.mark.parametrize("width", (1024, 1366))
def test_import_wizard_has_no_clipped_text(qapp, real_fonts, width, lang):
    """The wizard is a dialog, so the tab walk above never sees it — it gets its own case."""
    from pathlib import Path
    from ui.import_wizard import ImportWizard
    from tests.clipcheck import clipped_texts

    i18n.set_language(lang)
    dlg = ImportWizard(path=str(Path(__file__).parent / "data" / "synthetic_raman.xlsx"))
    dlg.resize(width, 660)
    dlg.show()
    qapp.processEvents()
    try:
        findings = clipped_texts(dlg)
    finally:
        dlg.close()
        dlg.deleteLater()
        qapp.processEvents()
    assert not findings, f"{len(findings)} clipped:\n  " + "\n  ".join(findings)
