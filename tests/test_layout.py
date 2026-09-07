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
from ui.start_screen import example_files

MIN, LAPTOP = (1024, 660), (1366, 768)
EXAMPLES = {p.stem: p for p in example_files()}
CASES = [(name, size) for name in EXAMPLES for size in (MIN, LAPTOP)]


def _walk(qapp, project_path, size, lang):
    from ui.main_window import MainWindow
    from ui.shots import visit_tabs
    from tests.clipcheck import clipped_texts

    i18n.set_language(lang)
    win = MainWindow(Project.load(str(project_path)))
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
def test_no_clipped_text(qapp, name, size, lang):
    findings = _walk(qapp, EXAMPLES[name], size, lang)
    assert not findings, f"{len(findings)} clipped:\n  " + "\n  ".join(findings)


@pytest.mark.parametrize("lang", ("en", "ko"))
@pytest.mark.parametrize("width", (1024, 1366))
def test_import_wizard_has_no_clipped_text(qapp, width, lang):
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
