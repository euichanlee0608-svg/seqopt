# -*- coding: utf-8 -*-
"""core/boot — the startup log and child-process window hiding.

Regression test for the black console windows that flashed when the GUI build started
(see the core/boot.py header). Whether a window really stays hidden is checked by CI's
Windows runner reading the startup log
(.github/workflows/build-windows.yml "Were child-process windows hidden?").
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from core import boot


def test_mark_records_elapsed_seconds_and_appends_to_file(tmp_path):
    log = tmp_path / "seqopt.log"
    boot.start(log)
    line = boot.mark("one stage")
    assert line.startswith("  +") and line.endswith("s  one stage")
    text = log.read_text(encoding="utf-8")
    assert "seqopt start" in text and "one stage" in text
    assert line in boot.lines()


def test_oversized_log_is_emptied_before_writing(tmp_path):
    log = tmp_path / "seqopt.log"
    log.write_text("x" * (boot.MAX_LOG_BYTES + 1), encoding="utf-8")
    boot.start(log)
    assert log.stat().st_size < boot.MAX_LOG_BYTES
    assert "seqopt start" in log.read_text(encoding="utf-8")


def test_unwritable_log_does_not_stop_the_program(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")
    boot.start(blocker / "seqopt.log")           # the parent is a file, so the folder cannot be made
    assert boot.mark("keeps going").endswith("keeps going")


@pytest.mark.skipif(sys.platform == "win32", reason="the Windows behavior is covered by the test below")
def test_hide_child_windows_is_a_no_op_off_windows():
    assert boot.hide_child_windows() is False
    assert boot.hidden_spawns() == []


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
def test_hidden_children_still_run_and_are_logged_on_windows():
    boot.hide_child_windows()
    assert boot.hide_child_windows() is False        # never switched on twice

    # cause 1 verbatim — the `ver` that platform._syscmd_ver spawns (shell=True goes through cmd.exe)
    out = subprocess.check_output("ver", shell=True, text=True)
    assert "Windows" in out
    # the shape of cause 2 — a list argument
    run = subprocess.run(["cmd", "/c", "ver"], capture_output=True, text=True)
    assert run.returncode == 0 and "Windows" in run.stdout

    spawned = boot.hidden_spawns()
    assert any("ver" in s for s in spawned)
    assert not any("could not hide" in ln for ln in boot.lines())
