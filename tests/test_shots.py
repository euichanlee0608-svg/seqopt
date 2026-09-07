# -*- coding: utf-8 -*-
"""The CI hook in app.py (SEQOPT_SHOTS) — the path where the shipped exe captures every tab of every example.

This runs **the same entry point** CI's Windows runner uses (`python app.py`), offscreen.
On 2026-09-05 that path stood still on Windows for 16 minutes — with nobody there, a dialog
has nobody to click it and waits forever. So while the hook is on, no dialog is opened, the
process kills itself once the watchdog runs out, and the log (~/.seqopt/seqopt.log) records
how far it got.

The home folder is redirected to a temp folder — the real ~/.seqopt log stays clean.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_SHOTS, MIN_BYTES = 19, 10_000      # the same thresholds as .github/workflows/build-windows.yml


def _env(home: Path, **extra) -> dict:
    # PYTHONIOENCODING=cp1252 — exactly what a Windows console or pipe is. Printing '→' or any
    # non-Latin text dies there with UnicodeEncodeError. On 2026-09-05 CI finished the whole capture,
    # then died on the very last print and stood for 16 minutes with an error dialog open.
    # The same condition is reproduced here on a Mac.
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONIOENCODING": "cp1252",
           "HOME": str(home), "USERPROFILE": str(home), **extra}
    # Use the real font cache — building a fresh one takes 8 seconds, more on CI
    real_cache = Path.home() / ".seqopt" / "mplcache"
    if real_cache.exists():
        env.setdefault("MPLCONFIGDIR", str(real_cache))
    return env


def test_shots_hook_captures_every_tab_of_every_example(tmp_path):
    shots = tmp_path / "shots"
    r = subprocess.run([sys.executable, str(ROOT / "app.py")], cwd=ROOT, capture_output=True,
                       text=True, timeout=240, env=_env(tmp_path, SEQOPT_SHOTS=str(shots)))
    assert r.returncode == 0, r.stderr[-2000:]
    pngs = list(shots.rglob("*.png"))
    assert len(pngs) >= MIN_SHOTS, sorted(p.name for p in pngs)
    assert all(p.stat().st_size >= MIN_BYTES for p in pngs)
    from ui.start_screen import example_files
    assert len((shots / "index.txt").read_text(encoding="utf-8").splitlines()) == len(example_files())
    log = (tmp_path / ".seqopt" / "seqopt.log").read_text(encoding="utf-8")
    assert "ex1 closed" in log and "ex2 closed" in log
    assert f"captured {len(pngs)} screens" in log
    assert f"seqopt shots: {len(pngs)}" in r.stdout


DRIVER = """
import sys
sys.path.insert(0, {root!r})
import app
from PySide6.QtWidgets import QApplication, QMessageBox
a = QApplication([])
QMessageBox.exec = lambda self: print("DIALOG_OPENED") or 0
app._install_crash_log()
app._tolerant_stdout()
print("arrow →")               # a character cp1252 cannot encode — must not die, must print ? instead
sys.excepthook(ValueError, ValueError("driver test"), None)
print("DRIVER_DONE")
"""


def _crash(tmp_path, **extra) -> str:
    r = subprocess.run([sys.executable, "-c", DRIVER.format(root=str(ROOT))], cwd=ROOT,
                       capture_output=True, text=True, timeout=120, env=_env(tmp_path, **extra))
    assert r.returncode == 0 and "DRIVER_DONE" in r.stdout, r.stderr[-1500:]
    err = (tmp_path / ".seqopt" / "error.log").read_text(encoding="utf-8")
    assert "ValueError: driver test" in err                # the file record is written either way
    return r.stdout


def test_crash_dialog_is_skipped_while_the_ci_hook_is_on(tmp_path):
    assert "DIALOG_OPENED" not in _crash(tmp_path, SEQOPT_SHOTS=str(tmp_path / "s"))
    assert "error ValueError" in (tmp_path / ".seqopt" / "seqopt.log").read_text(encoding="utf-8")


def test_crash_dialog_still_shows_for_a_person(tmp_path):
    assert "DIALOG_OPENED" in _crash(tmp_path)
