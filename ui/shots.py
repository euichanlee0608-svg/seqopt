# -*- coding: utf-8 -*-
"""Screen capture — every tab of the workspace window as PNGs.

Two callers share this.
  · `packaging/review_shots.py` — design review. Offscreen on a Mac, at two window sizes.
  · `app.py` with `SEQOPT_SHOTS=<dir>` — CI's Windows runner starts **the shipped exe on a
    real display**, captures every tab of every example and uploads them as an artifact
    (seqopt-windows-shots). A person looks at how Windows fonts, scaling and plugins actually
    render before anything goes to a user.

Screens are captured after the computation is done — diagnostics and the report run on
background threads, so we have to wait for them.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication, QScrollArea

from core import boot

# (row in the left rail, file name) — the number in the name is the flow order (01 is the import wizard)
TABS = ((0, "02_setup"), (1, "03_data"), (2, "04_diag"), (3, "05_model"),
        (4, "07_recommend"), (5, "08_report"), (6, "09_help"))


def save(app: QApplication, widget, path: Path) -> Path:
    app.processEvents()
    path.parent.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(path))
    return path


def visit_tabs(app: QApplication, win, tag: str = ""):
    """Walk every tab of a shown workspace window with a project loaded, waiting for each computation.

    Yields (name, widget) once a screen is settled — `capture_tabs` saves the widget as name.png,
    `tests/test_layout.py` measures the window for clipped text. One walk, two consumers, so
    what CI photographs and what the layout test checks can never drift apart.
    """
    win.shell.setCurrentIndex(1)
    win.runner.wait()
    app.processEvents()
    for row, name in TABS:
        boot.mark(f"capture {tag}/{name}")       # the log shows where it stalled
        win.nav.setCurrentRow(row)
        if row == 2:
            win.tab_diag.toggle.setChecked(True)
            app.processEvents()
            # the whole scroll interior — including what is folded below, in one image
            yield "04_diag_full", win.tab_diag.findChild(QScrollArea).widget()
        if row == 3:
            win.tab_model.canvas.draw()
        if row == 4:
            win.tab_recommend.request()
        if row == 5:
            win.tab_report.rebuild()
            QThreadPool.globalInstance().waitForDone(120_000)
        if row == 6:
            win.tab_help.show_topic("gate")
        app.processEvents()
        yield name, win
        if row == 3:
            win.tab_model.tabs.setCurrentIndex(1)
            app.processEvents()
            yield "06_model_checks", win


def capture_tabs(app: QApplication, win, out: Path, prefix: str = "") -> list[Path]:
    """Every tab of a workspace window with a project loaded. `win` is an already show()n MainWindow."""
    return [save(app, widget, out / f"{prefix}{name}.png") for name, widget in visit_tabs(app, win, out.name)]


def capture_examples(app: QApplication, start_win, out: Path,
                     size: tuple[int, int] = (1366, 728)) -> list[Path]:
    """The start screen + every tab of every bundled example. Called by the SEQOPT_SHOTS hook in `app.py`.

    The folders are named ex1, ex2, … rather than after the example files (whose names need
    not be ASCII), and index.txt records which is which.
    """
    from core.project import Project

    from .main_window import MainWindow
    from .start_screen import example_files

    w, h = size
    out.mkdir(parents=True, exist_ok=True)
    start_win.resize(w, h)
    files = [save(app, start_win, out / "00_start.png")]
    index = []
    for i, path in enumerate(example_files(), 1):
        tag = f"ex{i}"
        index.append(f"{tag} = {path.name}")
        win = MainWindow(Project.load(str(path)))
        win.resize(w, h)
        win.show()
        files += capture_tabs(app, win, out / tag)
        win._dirty = False       # a capture never saves — a "save changes?" dialog would make CI wait forever
        win.close()
        boot.mark(f"{tag} closed")
    (out / "index.txt").write_text("\n".join(index) + "\n", encoding="utf-8")
    return files
