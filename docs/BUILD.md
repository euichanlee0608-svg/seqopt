# Building seqopt

PyInstaller builds **only for the OS it runs on** — no cross-compiling.

## Windows (.exe)

- Easiest: push to `main` (or trigger **windows-build** in Actions) and
  download the `seqopt-windows` artifact.
- Locally: double-click `packaging\build_windows.bat` on a Windows PC with
  Python 3.11. It creates a venv, installs dependencies, **runs the tests**,
  then builds `dist\seqopt\seqopt.exe`. A test failure stops the build.

## macOS (.app)

```bash
bash packaging/build_macos.sh          # → dist/seqopt.app
```

## Things that break, and how they are fenced

| symptom | cause | fence |
|---|---|---|
| crashes on a clean PC, works in CI | `vcomp140.dll` found on the runner's PATH but missing from the bundle | CI checks the file exists at `_internal\` **root** (PyInstaller's ctypes hook looks there by basename only) |
| window never shows on user PCs | `qwindows.dll` platform plugin missing; offscreen tests can't notice | CI checks the plugin file exists |
| 60+ seconds to first window | onefile unpacking / matplotlib font-cache scan | onedir build; `MPLCONFIGDIR` pinned to the home folder; CI measures real time-to-window and fails above 25 s |
| broken bundle ships silently | examples or fonts dropped during packaging | `seqopt.exe --selftest` runs in CI; it also writes `selftest.txt` on user machines |
| antivirus flags the exe | UPX compression | UPX disabled |

The regression tests run **before** packaging, in the batch file and in CI —
a program that misjudges must never get packaged.
