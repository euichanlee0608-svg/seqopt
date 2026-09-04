# -*- coding: utf-8 -*-
"""Entry point (spec §7-2).

**Set up the environment before importing anything heavy.** The order of the
first two calls matters — matplotlib scans every font and builds a cache on
first import, and unless the cache location is pinned, a frozen executable
rebuilds it on every launch (see `_pin_matplotlib_cache`).
"""
from __future__ import annotations

import os
import platform
import sys
from datetime import datetime
from pathlib import Path


def _pin_matplotlib_cache() -> None:
    """Pin the font cache **to the user folder**. Call before importing matplotlib.

    PyInstaller onefile unpacks into a fresh temp folder on every run, and
    matplotlib puts its cache in there by default — the temp folder vanishes,
    and so does the cache. → **Every launch rescans all system fonts.**
    Measured on a Mac: 100+ seconds of freeze.

    In the home folder, the cache is built once and every later launch is instant.
    """
    if os.environ.get("MPLCONFIGDIR"):
        return
    cache = Path.home() / ".seqopt" / "mplcache"
    try:
        cache.mkdir(parents=True, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = str(cache)
    except OSError:
        pass                                     # fall back to the default behavior


_pin_matplotlib_cache()


LOG_DIR = Path.home() / ".seqopt"


def _install_crash_log() -> Path:
    """Write unexpected errors to a file and tell the user where it is.

    A GUI build (console=False) leaves nothing on screen when it fails. The
    user can only say "an error appeared", and we would have no clue to fix.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = LOG_DIR / "error.log"

    def handle(exc_type, exc, tb):
        import traceback
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        stamp = datetime.now().astimezone().isoformat(timespec="seconds")
        try:
            with open(log, "a", encoding="utf-8") as f:
                f.write(f"\n{'=' * 70}\n{stamp}  seqopt {platform.platform()}\n"
                        f"python {sys.version.split()[0]}\n{text}")
        except OSError:
            pass
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            if QApplication.instance() is not None:
                box = QMessageBox()
                box.setIcon(QMessageBox.Critical)
                box.setWindowTitle("Something went wrong")
                box.setText(f"{exc_type.__name__}: {exc}")
                box.setInformativeText(
                    "The details were written to the file below. "
                    f"Send that file and this can be fixed.\n\n{log}")
                box.setDetailedText(text)
                box.exec()
        except Exception:                        # noqa: BLE001
            pass
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = handle
    return log


def selftest() -> int:
    """Check that the shipped executable was bundled correctly.

    `seqopt --selftest` runs the checks without opening a window and exits.
    A Windows GUI build shows no stdout, so the **exit code** is the signal
    (0 = fine). The things that silently fall out of bundles get caught here.

    Heavy imports (matplotlib, Qt widgets) are deliberately avoided — a slow
    check is a check nobody runs in the build pipeline.
    """
    from core.project import Project
    from ui.start_screen import EXAMPLE_DIR

    problems: list[str] = []

    examples = sorted(EXAMPLE_DIR.glob("*.seqopt")) if EXAMPLE_DIR.is_dir() else []
    if not examples:
        problems.append(f"no example project found ({EXAMPLE_DIR})")
    else:
        try:
            if Project.load(str(examples[0])).dataset().n_conditions < 2:
                problems.append("the example opened but has too few conditions")
        except Exception as e:                   # noqa: BLE001
            problems.append(f"could not open the example: {e}")

    # The math bundle (numpy · scipy · scikit-learn) must actually run —
    # importing is not enough. sklearn opens its OpenMP DLL via ctypes at
    # import time.
    try:
        import numpy as np

        from core.diagnostics import discriminability, loocv_r2
        reps = [np.array([1.0, 1.02]), np.array([1.3, 1.28]), np.array([0.9, 0.94])]
        if discriminability(reps).sigma_w is None:
            problems.append("the discriminability calculation produced nothing")
        loocv_r2(np.array([[0.0], [0.5], [1.0]]), np.array([0.1, 0.6, 0.3]))
    except Exception as e:                       # noqa: BLE001
        problems.append(f"the math bundle does not work: {type(e).__name__}: {e}")

    report = "\n".join(problems) if problems else "OK"
    detail = (f"{report}\n\n[environment]\n{platform.platform()}\n"
              f"python {sys.version.split()[0]}\n"
              f"frozen={getattr(sys, 'frozen', False)}\n"
              f"exe={sys.argv[0]}")
    print(f"seqopt selftest: {report}")
    try:                                         # GUI builds show no stdout
        (Path(sys.argv[0]).resolve().parent / "selftest.txt").write_text(
            detail, encoding="utf-8")
    except OSError:
        pass
    return 1 if problems else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()

    log = _install_crash_log()

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication, QIcon
    from PySide6.QtWidgets import QApplication

    from core.project import Project
    from ui import theme
    from ui.main_window import MainWindow
    from ui.resources import icon_path

    # Keep text sharp at Windows 125%/150% scaling — pass the factor through
    # instead of rounding it
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    if sys.platform == "win32":
        # Make the taskbar show this program's icon, not python.exe's
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("seqopt.app.1")
        except Exception:                                 # noqa: BLE001
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("seqopt")
    app.setWindowIcon(QIcon(str(icon_path())))
    theme.apply(app)

    project = None
    if len(sys.argv) > 1 and sys.argv[1].endswith(".seqopt"):
        project = Project.load(sys.argv[1])

    win = MainWindow(project)
    if project is not None:
        win.shell.setCurrentIndex(1)      # opened with a file → jump straight to the workspace
    win.show()

    if os.environ.get("SEQOPT_EXIT_AFTER_SHOW"):
        # Hook for the build pipeline to time "seconds until the window shows".
        # A live process and a visible window are different things — this
        # exists to measure that difference.
        app.processEvents()
        return 0

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
