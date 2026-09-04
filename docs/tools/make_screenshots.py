# -*- coding: utf-8 -*-
"""App screenshots for the explainer page — taken from the real program.

    QT_QPA_PLATFORM=offscreen .venv/bin/python docs/tools/make_screenshots.py

Three states, because the page argues three things:
  app_diagnose — the gate open, every requirement shown with its number
  app_model    — the surface, uncertainty and EI drawn from real data
  app_locked   — the gate shut, and no recommendation constructed at all

Both projects are shipped data: the bundled P3HT example (public dataset) and
the synthetic Raman fixture the tests use. No lab data is ever loaded here.
"""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image                                            # noqa: E402
from PySide6.QtWidgets import QApplication                       # noqa: E402

from core.importer import apply_profile, preview                 # noqa: E402
from core.project import Project                                 # noqa: E402
from core.spec import ObjSpec, VarSpec                           # noqa: E402
from tests.test_ui import synthetic_profile                      # noqa: E402
from ui import theme                                             # noqa: E402
from ui.main_window import MainWindow                            # noqa: E402

OUT = ROOT / "docs" / "figures"
GRAB = (1920, 1040)          # grabbed at 1.5x and downscaled — text stays crisp
WIDE = 1280


def settle(w, app, rounds: int = 6) -> None:
    """Diagnostics run on a background thread; wait them out before grabbing."""
    for _ in range(rounds):
        w.runner.wait()
        app.processEvents()


def save(w, name: str) -> None:
    tmp = OUT / f".{name}.raw.png"
    w.grab().save(str(tmp))
    im = Image.open(tmp)
    im.resize((WIDE, round(im.height * WIDE / im.width)), Image.LANCZOS).save(OUT / name)
    tmp.unlink()
    print(f"  {name:20s} {WIDE}x{round(im.height * WIDE / im.width)}")


def pick_slice(w, x: str, y: str, zero: tuple[str, ...]) -> None:
    """Drive the Model tab's own controls — no drawing is bypassed."""
    m = w.tab_model
    names = [v.name for v in w.project.inputs]
    m.ax_i.setCurrentIndex(names.index(x))
    m.ax_j.setCurrentIndex(names.index(y))
    for s in m._sliders:                                          # noqa: SLF001
        if names[s._axis] in zero:                                # noqa: SLF001
            s.setValue(0)
    m.redraw()
    n = len(m._points_on_slice(names.index(x), names.index(y)))   # noqa: SLF001
    print(f"  slice {x} x {y}: {n} measured conditions on the plane")
    assert n >= 4, "the model shot must land on a populated slice"


def locked_project() -> Project:
    """The synthetic fixture, whose gate genuinely fails — not a mocked failure."""
    _, rows = preview(str(ROOT / "tests/data/synthetic_raman.xlsx"), "xlsx", 1, limit=10 ** 9)
    prof = synthetic_profile()
    ms, _ = apply_profile(rows, prof)
    for i, m in enumerate(ms, 1):
        m["id"] = i
    return Project(
        name="Demo — coating trial (in progress)",
        inputs=[VarSpec("power", "W", "continuous", 150, 190),
                VarSpec("dwell", "s", "integer", 3, 7)],
        objective=ObjSpec("G/D ratio", "a.u.", "max"),
        budget_total=40, measurements=ms, exclude_zero=True, import_profile=prof)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    theme.apply(app)

    # ── gate open: the bundled example ──────────────────────────────
    w = MainWindow(Project.load(str(ROOT / "examples/p3ht_conductivity.seqopt")))
    w.resize(*GRAB)
    w.shell.setCurrentIndex(1)
    w.show()
    settle(w, app)
    w.nav.setCurrentRow(2)                    # Diagnose
    settle(w, app, 3)
    save(w, "app_diagnose.png")
    w.nav.setCurrentRow(3)                    # Model
    settle(w, app, 4)
    # The opening slice sits at the best condition, where only one other
    # measurement lies — honest, but a featureless picture. Move to the plane
    # the data populates, exactly as the axis pickers do: of the ten pairs,
    # P3HT x D1 is the only one carrying both measurements (16) and a real
    # spread in mu (1.24). Chosen by measurement, not by eye.
    pick_slice(w, x="P3HT content", y="D1 content", zero=("D2 content",
                                                          "D6 content",
                                                          "D8 content"))
    settle(w, app, 3)
    save(w, "app_model.png")
    print(f"  example gate locked = {w.gate.locked}  (must be False)")
    assert not w.gate.locked, "the example must show an OPEN gate"
    w.close()

    # ── gate shut: the synthetic fixture ────────────────────────────
    w = MainWindow(locked_project())
    w.resize(*GRAB)
    w.shell.setCurrentIndex(1)
    w.show()
    settle(w, app)
    w.nav.setCurrentRow(4)                    # Recommend
    w.tab_recommend.request()
    settle(w, app, 3)
    save(w, "app_locked.png")
    print(f"  locked = {w.gate.locked} | learnable = {w.gate.learnable} "
          f"| discrim = {w.gate.discrim}")
    assert w.gate.locked, "the locked shot must show a SHUT gate"
    w.close()


if __name__ == "__main__":
    main()
