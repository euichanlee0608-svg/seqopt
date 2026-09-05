# -*- coding: utf-8 -*-
"""Startup log and child-process window hiding — so a GUI build does not flash black windows.

The Windows GUI build (console=False) flashed several console windows on startup — it
looked like a virus. The cause is not our code but **the child processes the math
bundle spawns while it is being imported**:

  · `platform.uname()` → `cmd /c ver`          Python standard library (`platform._syscmd_ver`).
                                               numpy, scipy and friends call `platform.system()`
                                               at import time.
  · joblib/loky counting physical cores → `powershell.exe -Command (Get-CimInstance …)`,
    falling back to `wmic CPU Get NumberOfCores`   when scikit-learn is imported.

When a process without a window spawns a console program, Windows **creates a new console
window for it.** So here every `subprocess.Popen` gets `CREATE_NO_WINDOW` plus a hidden
STARTUPINFO — whoever spawns whatever, no window appears. What was spawned goes into the
startup log.

The startup log (`~/.seqopt/seqopt.log`) is the only clue we have when someone says "it is
slow to open" or "a strange window appeared". It records how long every stage took.

Does not import the GUI (core rule). Standard library only.
"""
from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

LOG_DIR = Path.home() / ".seqopt"
LOG_FILE = LOG_DIR / "seqopt.log"
MAX_LOG_BYTES = 512 * 1024          # beyond this the file is emptied and started afresh

_T0 = time.perf_counter()
_lines: list[str] = []              # this run's log (tests and the self-check read it)
_path: Path | None = None
_hidden_spawns: list[str] = []


def start(path: Path | None = None) -> None:
    """Open this run's log. The program keeps going even if this fails."""
    global _path
    _path = path or LOG_FILE
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    head = (f"{'=' * 70}\n{stamp}  seqopt start  frozen={getattr(sys, 'frozen', False)}  "
            f"python {sys.version.split()[0]}  {sys.platform}")
    try:
        _path.parent.mkdir(parents=True, exist_ok=True)
        if _path.exists() and _path.stat().st_size > MAX_LOG_BYTES:
            _path.write_text("", encoding="utf-8")
        with open(_path, "a", encoding="utf-8") as f:
            f.write(head + "\n")
    except OSError:
        _path = None
    _lines.append(head)


def mark(msg: str) -> str:
    """Record one stage with its timestamp. Returns the line that was written."""
    line = f"  +{time.perf_counter() - _T0:6.2f}s  {msg}"
    _lines.append(line)
    if _path is not None:
        try:
            with open(_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass
    return line


def lines() -> list[str]:
    return list(_lines)


def hidden_spawns() -> list[str]:
    """The child processes spawned with their window hidden (this run)."""
    return list(_hidden_spawns)


def _describe(args) -> str:
    if isinstance(args, (list, tuple)):
        return " ".join(str(a) for a in args)
    return str(args)


def hide_child_windows() -> bool:
    """On Windows, hide the console window of every child process. Call it **before** importing anything heavy.

    Returns True if it was actually switched on. False off Windows, or if it is already on.
    """
    if sys.platform != "win32" or getattr(subprocess.Popen, "_seqopt_quiet", False):
        return False
    orig_init = subprocess.Popen.__init__

    def quiet_init(self, args, *a, **kw):
        # We assume nobody passes startupinfo (13th) or creationflags (14th) positionally.
        # If such a call does come, it is passed through untouched — better than meddling wrongly.
        if len(a) < 12:
            si = kw.get("startupinfo") or subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            kw["startupinfo"] = si
            kw["creationflags"] = kw.get("creationflags", 0) | subprocess.CREATE_NO_WINDOW
            _hidden_spawns.append(_describe(args))
            mark(f"  hidden child process: {_describe(args)[:120]}")
        else:
            mark(f"  could not hide child process: {_describe(args)[:120]}")
        orig_init(self, args, *a, **kw)

    subprocess.Popen.__init__ = quiet_init
    subprocess.Popen._seqopt_quiet = True
    mark("child-process window hiding on (CREATE_NO_WINDOW)")
    return True
