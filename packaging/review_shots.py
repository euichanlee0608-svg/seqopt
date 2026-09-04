# -*- coding: utf-8 -*-
"""Design-review screenshots — every screen at laptop (1366×728) and desktop (1920×1040) sizes.

    QT_QPA_PLATFORM=offscreen .venv/bin/python packaging/review_shots.py <output dir>

No PDF — just captures at two window sizes. After a design change, **look at
these images** and fix again.
"""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PySide6.QtWidgets import QApplication, QScrollArea          # noqa: E402

from core.project import Project                                  # noqa: E402
from ui import theme                                              # noqa: E402
from ui.main_window import MainWindow                             # noqa: E402
from ui.resources import example_dir                              # noqa: E402


def demo_project() -> Project:
    """The bundled example — the same thing a first-time user opens."""
    example = sorted(example_dir().glob("*.seqopt"))[0]
    return Project.load(str(example))

SIZES = {"laptop": (1366, 728), "desktop": (1920, 1040)}


def shoot(app: QApplication, out: Path, w: int, h: int) -> None:
    out.mkdir(parents=True, exist_ok=True)

    def save(widget, name):
        app.processEvents()
        widget.grab().save(str(out / f"{name}.png"))

    win = MainWindow()
    win.resize(w, h)
    win.show()
    save(win, "00_start")
    win.close()

    win = MainWindow(demo_project())
    win.resize(w, h)
    win.shell.setCurrentIndex(1)
    win.show()
    win.runner.wait()
    app.processEvents()
    for row, name in ((0, "02_setup"), (1, "03_data"), (2, "04_diag"), (3, "05_model"),
                      (4, "07_recommend"), (5, "08_report"), (6, "09_help")):
        win.nav.setCurrentRow(row)
        if row == 2:
            win.tab_diag.toggle.setChecked(True)
            app.processEvents()
            # the whole scroll interior — including what is folded below
            inner = win.tab_diag.findChild(QScrollArea).widget()
            save(inner, "04_diag_full")
        if row == 3:
            win.tab_model.canvas.draw()
        if row == 4:
            win.tab_recommend.request()
        if row == 5:
            win.tab_report.rebuild()
        if row == 6:
            win.tab_help.show_topic("gate")
        app.processEvents()
        save(win, name)
        if row == 3:
            win.tab_model.tabs.setCurrentIndex(1)
            app.processEvents()
            save(win, "06_model_checks")
    win.close()


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "docs" / "review_shots")
    app = QApplication.instance() or QApplication(sys.argv)
    theme.apply(app)
    for tag, (w, h) in SIZES.items():
        shoot(app, out / tag, w, h)
        print(f"  {tag}: {w}×{h} → {out / tag}")


if __name__ == "__main__":
    main()
