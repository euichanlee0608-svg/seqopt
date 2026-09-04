@echo off
REM seqopt Windows build.
REM Must run on a Windows PC - .exe files cannot be built on macOS/Linux.
setlocal
cd /d "%~dp0\.."

echo [1/4] creating the virtual environment
py -3.11 -m venv .venv || (echo Python 3.11 is required && exit /b 1)

echo [2/4] installing dependencies
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt PySide6 matplotlib pyinstaller || exit /b 1

echo [3/4] regression tests (a failure here stops the build)
.venv\Scripts\python -m pytest tests -q || (echo tests failed - aborting the build && exit /b 1)

echo [4/4] building the executable
.venv\Scripts\pyinstaller packaging\seqopt.spec --noconfirm --clean || exit /b 1

echo.
echo done: dist\seqopt\seqopt.exe
echo Copy the whole dist\seqopt folder - the exe needs the files next to it.
endlocal
