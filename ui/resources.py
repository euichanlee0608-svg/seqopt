# -*- coding: utf-8 -*-
"""Find bundled assets (icons, examples) the same way in and out of the bundle.

PyInstaller unpacks under `sys._MEIPASS`; running from source, it is the repo root.
"""
from __future__ import annotations

import sys
from pathlib import Path


def resource_dir() -> Path:
    base = getattr(sys, "_MEIPASS", None)
    return Path(base) if base else Path(__file__).resolve().parent.parent


def icon_path() -> Path:
    return resource_dir() / "assets" / "seqopt.png"


def example_dir() -> Path:
    return resource_dir() / "examples"
