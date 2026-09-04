# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build definition.

**This file builds only for the OS it runs on.** Run it on a Mac and you get a
Mac app; on Windows, an .exe — PyInstaller does not cross-compile.
Details in docs/BUILD.md.
"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs


def _flat_libs(package):
    """Put a package's bundled dynamic libraries at the bundle **root**.

    scikit-learn opens `sklearn/.libs/vcomp140.dll` via ctypes at import time.
    PyInstaller intercepts that call and re-resolves it as —

        os.path.join(sys._MEIPASS, os.path.basename(name))     # pyimod03_ctypes

    i.e. **by bare filename at the bundle root.** It never looks in subfolders.

    onefile happened to work because it flattens every library into the temp
    root; switching to onedir moved them into `_internal/sklearn/__dot__libs/`
    where the lookup fails (PyInstaller renames `.libs` to `__dot__libs` to
    avoid hidden folders). So dest is pinned to '.' — exactly what onefile did.
    """
    return [(src, ".") for src, _dest in collect_dynamic_libs(package)]

ROOT = Path(SPECPATH).parent
IS_WINDOWS = sys.platform.startswith("win")

a = Analysis(
    [str(ROOT / "app.py")],
    pathex=[str(ROOT)],
    binaries=_flat_libs("sklearn") + _flat_libs("scipy") + _flat_libs("numpy"),
    # ship the example project — a first-time user must have something to open
    datas=[(str(ROOT / "examples"), "examples"),
           (str(ROOT / "assets"), "assets")],          # icons (window · start screen)
    # Dynamic imports PyInstaller cannot see. Missing ones kill the app at startup.
    hiddenimports=[
        "sklearn.utils._typedefs",
        "sklearn.utils._heap",
        "sklearn.utils._sorting",
        "sklearn.utils._vector_sentinel",
        "sklearn.neighbors._partition_nodes",
        "scipy.special._cdflib",
        "matplotlib.backends.backend_qtagg",
    ],
    hookspath=[],
    runtime_hooks=[],
    # drop unused GUI backends to cut size
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2", "IPython", "jupyter",
              "pytest", "nbconvert", "notebook"],
    noarchive=False,
)
pyz = PYZ(a.pure)

# ── why onedir, not onefile ──────────────────────────────────────────
# onefile unpacks all 76MB into a temp folder on every launch.
# Measured: 0s from source vs 61s as onefile. Nobody uses a program that
# makes them wait a minute every time. onedir has nothing to unpack and shows
# instantly; the price is a folder instead of a single file, so releases zip
# the folder (GitHub Actions does that automatically).
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="seqopt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                    # UPX triggers antivirus false positives — a real problem on lab PCs
    console=False,                # a GUI app — no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / ("seqopt.ico" if IS_WINDOWS else "seqopt.icns")),
)

coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="seqopt")

if not IS_WINDOWS:
    app = BUNDLE(coll, name="seqopt.app", icon=str(ROOT / "assets" / "seqopt.icns"),
                 bundle_identifier="dev.seqopt")
