#!/usr/bin/env bash
# seqopt macOS app build. Windows .exe files cannot be made here (see build_windows.bat).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[1/3] checking dependencies"
.venv/bin/python -m pip install --quiet pyinstaller

echo "[2/3] regression tests"
.venv/bin/python -m pytest tests -q

echo "[3/3] building the app"
.venv/bin/pyinstaller packaging/seqopt.spec --noconfirm --clean

echo
echo "done: dist/seqopt.app"
