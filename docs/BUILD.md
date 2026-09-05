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
| black console windows flash at startup ("looks like a virus") | `platform` spawns `cmd /c ver`, joblib spawns `powershell`/`wmic` while numpy and scikit-learn are imported; a windowless process gets a new console per child | `core/boot.py: hide_child_windows()` adds `CREATE_NO_WINDOW` to every `subprocess.Popen` **before** the heavy imports; CI reads the boot log for the markers |
| CI capture hangs forever | a dialog opened with nobody to click it (see below) | no dialogs while `SEQOPT_SHOTS` / `SEQOPT_EXIT_AFTER_SHOW` is set; 300 s watchdog; tolerant stdout |

The regression tests run **before** packaging, in the batch file and in CI —
a program that misjudges must never get packaged.

## Startup: splash card + log, not a console window

Startup takes 3–8 seconds (scikit-learn alone is 2–3 s). Showing a terminal for
that would turn the app back into a console program, so instead `app.py` shows a
small splash card with the current stage ("Loading the math engine…", "Building
the screens…") and writes the same stages, with elapsed seconds, to
`~/.seqopt/seqopt.log` (`core/boot.py`, `boot.mark(...)`). The file is appended on
every launch and emptied once it exceeds 512 KB. A typical entry:

```
======================================================================
2026-09-05T10:12:03+09:00  seqopt start  frozen=True  python 3.11.9  win32
  +  0.01s  font cache location pinned
  +  0.01s  child-process window hiding on (CREATE_NO_WINDOW)
  +  0.62s  GUI engine (PySide6) loaded
  +  0.80s  Opening…
  +  0.81s  Loading the math engine… (numpy · scipy · scikit-learn)
  +  0.95s    hidden child process: ver
  +  3.40s  Building the screens…
  +  4.10s  window shown (2 child processes hidden)
```

`hide_child_windows()` only does real work on Windows; on macOS and Linux it is
a no-op and the log simply has no child-process lines. Unexpected errors go to
`~/.seqopt/error.log` (full traceback) and leave an `error …` line in
`seqopt.log`.

CI's Windows runner starts the built exe with `SEQOPT_EXIT_AFTER_SHOW=1`, then
checks that the log contains `window shown` and `child-process window hiding
on`, and does **not** contain `could not hide child process`. Those three strings
plus `hidden child process:` are the markers the workflow greps for — keep them
stable if you edit `core/boot.py`.

## CI screenshots: the `seqopt-windows-shots` artifact

Fonts, DPI scaling and the Qt platform plugin cannot be judged offscreen, so the
workflow also runs the exe with `SEQOPT_SHOTS=<dir>` on the runner's real
display. `ui/shots.py` captures the start screen plus every tab of every bundled
example (folders `ex1/`, `ex2/`, with `index.txt` saying which example is which)
and the workflow requires at least 19 PNGs of at least 10 KB each
(1 start screen + 2 examples × 9 tabs). The images are uploaded as
`seqopt-windows-shots` even when the step fails, and the last 60 lines of
`seqopt.log` (plus `error.log`, if any) are printed — every tab writes a
`capture ex1/05_model`-style line first, so the last line is where it stopped.

## Headless rules (learned from a 16-minute hang)

The first capture run finished every screenshot, then hung until the job timed
out: the final `print(... → ...)` hit the runner's cp1252 stdout pipe, raised
`UnicodeEncodeError`, the exception escaped `main()`, and `sys.excepthook` opened
a modal error dialog nobody could click. A GUI build (console=False) shows no
console, so there was no clue on screen either. The fences, all in `app.py`:

- `_tolerant_stdout()` — first line of `main()`; stdout is reconfigured with
  `errors="replace"`, so unencodable characters become `?` instead of a crash.
- `_headless()` — true when `SEQOPT_SHOTS` or `SEQOPT_EXIT_AFTER_SHOW` is set;
  the crash handler then only logs and never opens a `QMessageBox`. `ui/shots.py`
  also sets `win._dirty = False` before closing so no "save changes?" dialog
  appears.
- `SHOTS_TIMEOUT = 300` — a watchdog thread; if the capture is not done in
  5 minutes it writes a log line and `os._exit(3)`s (the workflow's
  `timeout-minutes: 10` is the safety net behind it). Exit code 2 means the
  capture itself raised; the traceback is in `seqopt.log`.
- `tests/test_shots.py` runs `python app.py` as a subprocess with
  `PYTHONIOENCODING=cp1252` and a temporary `HOME`, which reproduces the Windows
  console condition on a Mac (it failed before the fix), and checks with a
  driver script that the crash dialog is skipped in headless mode but still
  shown to a person.

Rule of thumb: a GUI running with nobody in front of it will eventually stop at
any code path that can open a dialog, and a `print` in a GUI build is not
"invisible" — it can kill the process.
