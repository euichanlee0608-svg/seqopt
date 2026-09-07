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

# Startup log + child-process window hiding. Must be switched on **before numpy and
# scikit-learn** — they spawn cmd/powershell while being imported, and in a program
# without a window those flash as console windows (see the core/boot.py header).
# The log is ~/.seqopt/seqopt.log.
from core import boot  # noqa: E402  (a standard-library-only module)
from core import i18n  # noqa: E402  (stdlib only — picks the language before anything is drawn)
from core.i18n import tr  # noqa: E402

boot.start()
boot.mark("font cache location pinned")
boot.hide_child_windows()


LOG_DIR = Path.home() / ".seqopt"
SHOTS_TIMEOUT = 300            # a capture (SEQOPT_SHOTS) that cannot finish within this kills itself (seconds)


def _headless() -> bool:
    """Launched by a CI hook? Then nobody is there — no dialogs (nobody can click, so it would wait forever)."""
    return bool(os.environ.get("SEQOPT_SHOTS") or os.environ.get("SEQOPT_EXIT_AFTER_SHOW"))


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
                f.write(f"\n{'=' * 70}\n{stamp}  seqopt {platform.platform()}\n"      # i18n: skip
                        f"python {sys.version.split()[0]}\n{text}")
        except OSError:
            pass
        boot.mark(f"error {exc_type.__name__}: {exc} → {log}")
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            if QApplication.instance() is not None and not _headless():
                box = QMessageBox()
                box.setIcon(QMessageBox.Critical)
                box.setWindowTitle(tr("Something went wrong"))
                box.setText(f"{exc_type.__name__}: {exc}")                       # i18n: skip (a Python exception)
                box.setInformativeText(tr(
                    "The details were written to the file below. "
                    "Send that file and this can be fixed.\n\n{log}", log=log))
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
    from ui.start_screen import EXAMPLE_DIR, EXAMPLES, example_files

    problems: list[str] = []

    examples = example_files()
    if len(examples) < len(EXAMPLES):
        problems.append(tr("an example project is missing ({where}: {found})",
                           where=EXAMPLE_DIR, found=[p.name for p in examples]))
    for path in examples:
        try:
            if Project.load(str(path)).dataset().n_conditions < 2:
                problems.append(tr("the example opened but has too few conditions: {name}", name=path.name))
        except Exception as e:                   # noqa: BLE001
            problems.append(tr("could not open the example: {name}: {why}", name=path.name, why=e))

    # The math bundle (numpy · scipy · scikit-learn) must actually run —
    # importing is not enough. sklearn opens its OpenMP DLL via ctypes at
    # import time.
    try:
        import numpy as np

        from core.diagnostics import discriminability, loocv_r2
        reps = [np.array([1.0, 1.02]), np.array([1.3, 1.28]), np.array([0.9, 0.94])]
        if discriminability(reps).sigma_w is None:
            problems.append(tr("the discriminability calculation produced nothing"))
        loocv_r2(np.array([[0.0], [0.5], [1.0]]), np.array([0.1, 0.6, 0.3]))
    except Exception as e:                       # noqa: BLE001
        problems.append(tr("the math bundle does not work: {why}", why=f"{type(e).__name__}: {e}"))

    report = "\n".join(problems) if problems else tr("OK")
    # the machine fingerprint below the verdict — versions and paths, the same in any language
    detail = (f"{report}\n\n[environment]\n{platform.platform()}\n"      # i18n: skip
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


def _splash(app):
    """A small card shown while opening — one line saying what is happening right now.

    This is what we show instead of a black terminal window. Opening takes 3–8 seconds,
    and if nothing is visible for that long, people double-click again and get two copies.
    """
    from PySide6.QtCore import QRect, Qt
    from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
    from PySide6.QtWidgets import QSplashScreen

    from ui import theme
    from ui.resources import icon_path

    w, h = 440, 190
    pm = QPixmap(w, h)
    pm.fill(QColor(theme.BG))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QColor(theme.BORDER))
    p.drawRect(0, 0, w - 1, h - 1)
    icon = QPixmap(str(icon_path()))
    if not icon.isNull():
        p.drawPixmap(28, 34, icon.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    family = theme.pick_font_family() or app.font().family()
    p.setPen(QColor(theme.TEXT))
    title = QFont(family, -1, QFont.DemiBold)
    title.setPixelSize(theme.H1 + 6)
    p.setFont(title)
    p.drawText(QRect(112, 36, w - 130, 36), Qt.AlignLeft | Qt.AlignVCenter, "seqopt")   # i18n: skip (the name)
    body = QFont(family)
    body.setPixelSize(theme.FONT_SIZE)
    p.setFont(body)
    p.setPen(QColor(theme.TEXT_MUTED))
    p.drawText(QRect(112, 72, w - 130, 24), Qt.AlignLeft | Qt.AlignVCenter,
               tr("Sequential optimization — requirements first"))
    p.end()

    splash = QSplashScreen(pm, Qt.WindowStaysOnTopHint)
    splash.setFont(body)

    def say(msg: str) -> None:
        boot.mark(msg)
        splash.showMessage(f"   {msg}", Qt.AlignBottom | Qt.AlignLeft, QColor(theme.TEXT_MUTED))
        app.processEvents()

    splash.show()
    say(tr("Opening…"))
    return splash, say


def _tolerant_stdout() -> None:
    """Windows consoles and pipes are cp1252/cp949 — printing '→' or non-Latin text dies with UnicodeEncodeError.

    On 2026-09-05 the CI capture finished completely, then died on its very last print and
    stood for 16 minutes with an error dialog open. Characters that cannot be written become
    ? and we move on. A GUI build may have no stdout at all (None).
    """
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass


def main() -> int:
    _tolerant_stdout()
    if "--selftest" in sys.argv:
        return selftest()

    log = _install_crash_log()

    from PySide6.QtCore import QLocale, QSettings, Qt
    from PySide6.QtGui import QGuiApplication, QIcon
    from PySide6.QtWidgets import QApplication

    boot.mark("GUI engine (PySide6) loaded")

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

    # The language is chosen here, before the first widget exists — SEQOPT_LANG → the saved
    # setting → the OS locale. The env override is for one run (CI captures both languages)
    # and is never written back into the settings; only the Language menu saves.
    i18n.set_language(i18n.default_language(QSettings("seqopt", "seqopt").value("language"),
                                            QLocale.system().name()))

    from ui import theme
    from ui.resources import icon_path
    app.setWindowIcon(QIcon(str(icon_path())))
    theme.apply(app)
    splash, say = _splash(app)

    # From here on it gets heavy. Every stage goes on the card and into the log.
    say(tr("Loading the math engine… (numpy · scipy · scikit-learn)"))
    from core.project import Project
    import core.diagnostics  # noqa: F401  — this is where scikit-learn comes up (2–3 seconds)
    say(tr("Building the screens…"))
    from ui.main_window import MainWindow

    project = None
    if len(sys.argv) > 1 and sys.argv[1].endswith(".seqopt"):
        say(tr("Opening the project…"))
        project = Project.load(sys.argv[1])

    win = MainWindow(project)
    if project is not None:
        win.shell.setCurrentIndex(1)      # opened with a file → jump straight to the workspace
    win.show()
    splash.finish(win)
    boot.mark(f"window shown ({len(boot.hidden_spawns())} child processes hidden)")

    if os.environ.get("SEQOPT_EXIT_AFTER_SHOW"):
        # Hook for the build pipeline to time "seconds until the window shows".
        # A live process and a visible window are different things — this
        # exists to measure that difference.
        app.processEvents()
        return 0

    shots = os.environ.get("SEQOPT_SHOTS")
    if shots:
        # CI's Windows runner drives the shipped exe to capture every tab of every example
        # (ui/shots.py). Only after a person has looked at those images can anyone say
        # "it looks right on Windows". If this stalls somewhere, CI waits forever — so once
        # the watchdog runs out, we write a log line and kill ourselves.
        import threading
        from ui.shots import capture_examples

        def give_up() -> None:
            boot.mark(f"capture did not finish within {SHOTS_TIMEOUT} s — forcing exit "
                      "(the last line above is where it stalled)")
            os._exit(3)

        watchdog = threading.Timer(SHOTS_TIMEOUT, give_up)
        watchdog.daemon = True
        watchdog.start()
        try:
            files = capture_examples(app, win, Path(shots))
        except Exception:                                 # noqa: BLE001
            import traceback
            boot.mark("capture failed\n" + traceback.format_exc())
            return 2
        boot.mark(f"captured {len(files)} screens → {shots} — exiting")
        print(f"seqopt shots: {len(files)} -> {shots}", flush=True)
        return 0

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
