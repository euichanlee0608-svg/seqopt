# -*- coding: utf-8 -*-
"""Design-review screenshots — every screen at the minimum (1024×660), laptop (1366×728) and
desktop (1920×1040) sizes, in one language.

    QT_QPA_PLATFORM=offscreen .venv/bin/python packaging/review_shots.py <output dir>
    SEQOPT_LANG=ko QT_QPA_PLATFORM=offscreen .venv/bin/python packaging/review_shots.py <output dir>/ko

No PDF — just captures. After a design or wording change, **look at these images** in both
languages and fix again. `tests/test_layout.py` measures what these show.
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
from PySide6.QtWidgets import QApplication                       # noqa: E402

from core import i18n                                             # noqa: E402
from core.project import Project                                  # noqa: E402
from ui import theme                                              # noqa: E402
from ui.main_window import MainWindow                             # noqa: E402
from ui.resources import example_dir                              # noqa: E402
from ui.shots import capture_tabs, save                           # noqa: E402


def demo_project() -> Project:
    """The bundled example — the same thing a first-time user opens."""
    example = sorted(example_dir().glob("*.seqopt"))[0]
    return Project.load(str(example))

SIZES = {"min": (1024, 660), "laptop": (1366, 728), "desktop": (1920, 1040)}


def shoot(app: QApplication, out: Path, w: int, h: int) -> None:
    out.mkdir(parents=True, exist_ok=True)

    win = MainWindow()
    win.resize(w, h)
    win.show()
    save(app, win, out / "00_start.png")
    win.close()

    win = MainWindow(demo_project())
    win.resize(w, h)
    win.show()
    capture_tabs(app, win, out)
    win.close()


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "docs" / "review_shots")
    app = QApplication.instance() or QApplication(sys.argv)
    theme.apply(app)
    i18n.set_language(i18n.default_language())          # SEQOPT_LANG=ko for the Korean screens
    for tag, (w, h) in SIZES.items():
        shoot(app, out / tag, w, h)
        print(f"  {tag}: {w}×{h} → {out / tag}")


if __name__ == "__main__":
    main()
