# -*- coding: utf-8 -*-
"""Keeps diagnostic computation off the screen thread.

**Why a thread** — LOOCV grows with the condition count into whole seconds
(39s at 178 conditions × 5 variables). Run the fast parts (surface, σ, EI) and
the slow part (learnability R²) as one lump and table input freezes. So they
are split, and the slow part runs here (SPEC_AMENDMENTS A2).

⚠ Do not speed this up with closed-form LOO — the verdict flips. Slow is correct.
"""
from __future__ import annotations

import time

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from core.diagnostics import discriminability, loocv_r2, nugget_ratio
from core.surrogate import fit


class _Signals(QObject):
    fast_done = Signal(object)      # dict: discriminability · nugget (immediate)
    slow_done = Signal(object)      # dict: learnability R² (background)
    failed = Signal(str)


def _warm_mathtext() -> None:
    """Warm the diagnosis screen's math renderer (matplotlib mathtext) **on the worker thread.**

    matplotlib's first import can take tens of seconds on Windows building its
    font cache. Paying that cost on the UI thread — the first time a formula is
    drawn — freezes the window. So it is paid here, in advance.
    """
    try:
        from matplotlib.mathtext import MathTextParser
        MathTextParser("agg").parse("$D$", dpi=72)
    except Exception:                                # noqa: BLE001
        pass


class DiagnosticsJob(QRunnable):
    """One diagnosis of one dataset. Results are discarded when cancelled."""

    def __init__(self, dataset, want_slow: bool = True):
        super().__init__()
        self.ds = dataset
        self.want_slow = want_slow
        self.signals = _Signals()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @Slot()
    def run(self) -> None:
        try:
            _warm_mathtext()
            t0 = time.perf_counter()
            disc = discriminability(self.ds.reps)
            nug = nugget_ratio(self.ds.XN, self.ds.y_mean, sigma_w=disc.sigma_w) \
                if len(self.ds.y_mean) >= 3 else None
            # The model the surface tab will use. One fit is 0.25s even at 200
            # conditions, so it belongs on the fast side (only LOOCV is slow —
            # SPEC_AMENDMENTS A2)
            model = fit(self.ds.XN, self.ds.y_mean) if len(self.ds.y_mean) >= 3 else None
            if self._cancelled:
                return
            self.signals.fast_done.emit(
                dict(disc=disc, nugget=nug, model=model,
                     elapsed=time.perf_counter() - t0))

            if not self.want_slow or len(self.ds.y_mean) < 3:
                return
            t1 = time.perf_counter()
            r = loocv_r2(self.ds.XN, self.ds.y_mean)
            if self._cancelled:
                return
            self.signals.slow_done.emit(dict(loocv=r, elapsed=time.perf_counter() - t1))
        except Exception as e:                       # noqa: BLE001
            if not self._cancelled:
                self.signals.failed.emit(str(e))


class DiagnosticsRunner(QObject):
    """Only **the most recent request** is ever valid.

    Type measurements in a row and every earlier computation is useless. Cancel
    it and start over — a stale result arriving late and rolling the screen
    back is the most confusing bug this program can have.
    """

    fast_done = Signal(object)
    slow_done = Signal(object)
    failed = Signal(str)
    started = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pool = QThreadPool.globalInstance()
        self._current: DiagnosticsJob | None = None

    def submit(self, dataset, want_slow: bool = True) -> None:
        if self._current is not None:
            self._current.cancel()
        job = DiagnosticsJob(dataset, want_slow)
        job.signals.fast_done.connect(self._on_fast)
        job.signals.slow_done.connect(self._on_slow)
        job.signals.failed.connect(self.failed)
        self._current = job
        self.started.emit()
        self.pool.start(job)

    def cancel(self) -> None:
        """Throw away what is still computing — the screen that asked for it is going away."""
        if self._current is not None:
            self._current.cancel()

    def _on_fast(self, payload):
        self.fast_done.emit(payload)

    def _on_slow(self, payload):
        self.slow_done.emit(payload)

    def wait(self, ms: int = 120_000) -> bool:
        """For tests — wait until the queue drains."""
        return self.pool.waitForDone(ms)
