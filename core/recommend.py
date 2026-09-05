# -*- coding: utf-8 -*-
"""Recommendation — picks the next condition to measure (F-20 ~ F-25).

**The one and only path to a recommendation in this program is `recommend()`.**

The return type `Recommendation | Locked` is the central design decision. The
caller has to check which of the two it got, so no screen can ignore the lock
by accident — not because the UI is disciplined, but because **the structure
does not let it through.**

Surrogates and acquisitions are swappable (`SURROGATES` · `ACQUISITIONS`).
The gate is not. Refusing to optimize on data that cannot support it is this
tool's reason to exist, and making that replaceable would erase the tool.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .acquisition import (Pick, batch_picks, best_of, make_acquisition, maximise_continuous,
                          prepare, should_stop, unmeasured)
from .design import feasible_unit, maximin_lhs, snap_to_constraint
from .diagnostics import Gate
from .protocols import Acquisition, Surrogate
from .spec import Dataset, SumConstraint, VarSpec
from .surface import format_condition, to_real
from .surrogate import DEFAULT_SURROGATE, SURROGATES, fit

CANDIDATE_POOL = 4000
EXTRAPOLATION_TOL = 0.02        # declared range beyond the measured range by this much = extrapolation


# ══════════════════════════════════════════════════════════════════════
# Result types
# ══════════════════════════════════════════════════════════════════════
@dataclass
class Suggestion:
    """One suggestion. Screens, instructions and the report use these values verbatim."""

    x_norm: np.ndarray
    x_real: np.ndarray
    acq_value: float
    predicted_mean: float
    predicted_std: float
    label: str                       # "power 176 W · dwell 6 s"
    extrapolated: bool = False       # True when outside the measured range

    @property
    def suggested_reps(self) -> int:
        """Recommended replicate count. Goes into the instruction sheet (F-42)."""
        return self._reps

    _reps: int = 1


@dataclass
class Recommendation:
    """Only ever constructed after the gate has passed."""

    suggestions: list[Suggestion]
    acquisition_label: str
    surrogate_label: str
    best_measured: float
    response_range: float
    stop_advised: bool = False
    stop_reason: str = ""
    gate_bypassed: bool = False      # produced by a forced run (§10 risk table)
    warnings: list[str] = field(default_factory=list)

    @property
    def acq_max(self) -> float:
        return max((s.acq_value for s in self.suggestions), default=0.0)


@dataclass
class Locked:
    """Gate not passed. **Carries no suggestions** — nothing to take out by mistake."""

    gate: Gate
    reasons: list[str]

    @property
    def headline(self) -> str:
        return "The requirements were not met, so no recommendation is given."


RecommendResult = Recommendation | Locked


# ══════════════════════════════════════════════════════════════════════
# Building candidates
# ══════════════════════════════════════════════════════════════════════
def _axis_bounds(ds: Dataset, inputs: list[VarSpec]) -> np.ndarray:
    """Map the declared variable ranges into **measured-range normalized coordinates.**

    The model learned with the measured range as [0,1]. Where the declared range
    is wider, the outside is **extrapolation** — the model does not fail there,
    it produces plausibly wrong values. We do not block it (widening the range
    is sometimes the right answer) but we always mark it.
    """
    lo, span = ds.X.min(0), np.ptp(ds.X, axis=0)
    span = np.where(span > 0, span, 1.0)
    out = np.empty((len(inputs), 2))
    for k, v in enumerate(inputs):
        v_lo = v.lo if v.lo is not None else ds.X[:, k].min()
        v_hi = v.hi if v.hi is not None else ds.X[:, k].max()
        out[k] = [(v_lo - lo[k]) / span[k], (v_hi - lo[k]) / span[k]]
    return out


def _snap(x_real: np.ndarray, inputs: list[VarSpec],
          constraint: SumConstraint | None = None) -> np.ndarray:
    """Snap integer/categorical/stepped variables to values that can actually be measured.
    A fractional 3.7 seconds cannot go on an instruction sheet.

    With a sum constraint, the sum is restored after snapping to the grid.
    """
    out = x_real.copy()
    for k, v in enumerate(inputs):
        if v.type == "categorical":
            out[k] = np.round(out[k])
        else:
            out[k] = v.snap(out[k])
    if constraint is not None:
        out = snap_to_constraint(out, inputs, constraint)
    return out


def _gridded(inputs: list[VarSpec], constraint: SumConstraint | None) -> bool:
    """Must we enumerate candidates instead of optimizing continuously — yes if any integer, categorical, step or constraint is present."""
    return constraint is not None or any(v.type != "continuous" or v.step is not None
                                         for v in inputs)


def candidate_pool(ds: Dataset, inputs: list[VarSpec], size: int = CANDIDATE_POOL,
                   seed: int = 0, constraint: SumConstraint | None = None) -> np.ndarray:
    """Candidate grid (normalized coordinates). Integer/categorical/stepped axes sit only on measurable values.

    With a sum constraint, only points on the constraint surface are drawn.
    Conditions already measured are removed (principle P2 — before any
    lookahead concern, recommending a re-measurement is pointless).
    """
    lo, span = ds.X.min(0), np.ptp(ds.X, axis=0)
    span = np.where(span > 0, span, 1.0)

    if constraint is None:
        bounds = _axis_bounds(ds, inputs)
        unit = maximin_lhs(size, len(inputs), seed=seed, tries=1)
        pool = bounds[:, 0] + unit * (bounds[:, 1] - bounds[:, 0])
        real = np.array([_snap(row, inputs) for row in lo + pool * span])
    else:
        unit = feasible_unit(size, inputs, constraint, seed=seed)
        v_lo = np.array([v.lo if v.lo is not None else 0.0 for v in inputs])
        v_hi = np.array([v.hi if v.hi is not None else len(v.levels) - 1 for v in inputs])
        real = np.array([_snap(row, inputs, constraint) for row in v_lo + unit * (v_hi - v_lo)])
    pool = (real - lo) / span

    pool = np.unique(np.round(pool, 9), axis=0)
    return unmeasured(pool, ds.XN)


# ══════════════════════════════════════════════════════════════════════
# Recommendation
# ══════════════════════════════════════════════════════════════════════
def recommend(ds: Dataset, inputs: list[VarSpec], gate: Gate, *,
              acquisition: Acquisition | None = None,
              surrogate_name: str = DEFAULT_SURROGATE,
              model: Surrogate | None = None,
              batch: int = 1,
              acq_history: list[float] | None = None,
              rng: np.random.Generator | None = None,
              override: bool = False,
              constraint: SumConstraint | None = None) -> RecommendResult:
    """Pick the next candidates. **Returns `Locked` when the gate has not passed.**

    override=True means the user read the warnings and forced the run. The
    result carries the mark, and the report cover gets a "generated with
    requirements unmet" watermark (§10 risk table).
    With a constraint, every suggestion satisfies it.
    """
    if gate.locked and not override:
        return Locked(gate=gate, reasons=list(gate.reasons))

    acq = acquisition or make_acquisition()
    surrogate = model or fit(ds.XN, ds.y_mean, surrogate_name)
    best_measured = float(max(v.max() for v in ds.reps))
    response_range = float(np.ptp(ds.y_mean))

    bounds = _axis_bounds(ds, inputs)
    pool = candidate_pool(ds, inputs, constraint=constraint)
    prepare(acq, surrogate, pool if len(pool) else ds.XN, best_measured, rng)
    picks = _pick(surrogate, acq, inputs, pool, bounds, best_measured, batch,
                  surrogate_name, rng, gridded=_gridded(inputs, constraint))

    suggestions = [_to_suggestion(p, ds, inputs, constraint) for p in picks]
    warnings: list[str] = []
    if any(s.extrapolated for s in suggestions):
        warnings.append("A suggestion lies outside the measured range — the model has never learned what is out there.")
    if not pool.size:
        warnings.append("No unmeasured candidates remain. Widen the design range or close out the budget.")

    history = list(acq_history or [])
    acq_max = max((s.acq_value for s in suggestions), default=0.0)
    stop = should_stop(history + [acq_max], response_range)

    return Recommendation(
        suggestions=suggestions,
        acquisition_label=acq.describe(),
        surrogate_label=SURROGATES.label_of(surrogate_name),
        best_measured=best_measured,
        response_range=response_range,
        stop_advised=stop,
        stop_reason=("The maximum acquisition value has stayed below 1% of the response range "
                     "3 times in a row — there is almost nothing left to gain by measuring more."
                     if stop else ""),
        gate_bypassed=bool(gate.locked and override),
        warnings=warnings,
    )


def _pick(model: Surrogate, acq: Acquisition, inputs: list[VarSpec],
          pool: np.ndarray, bounds: np.ndarray, best: float, batch: int,
          surrogate_name: str, rng: np.random.Generator | None,
          gridded: bool | None = None) -> list[Pick]:
    """Maximize over continuous space when possible, by enumeration otherwise.

    Any integer/categorical/step/sum constraint forces enumeration — a
    continuous optimum like 3.7 seconds cannot go on an instruction sheet, and
    box optimization cannot stay on a constraint surface.
    """
    if gridded is None:
        gridded = _gridded(inputs, None)
    if batch > 1:
        return batch_picks(model, acq, pool, best, batch, surrogate_name, rng)
    if not gridded and acq.supports_continuous:
        return [maximise_continuous(model, acq, best, bounds, rng)]
    return [best_of(model, acq, pool, best, rng)] if len(pool) else []


def _to_suggestion(pick: Pick, ds: Dataset, inputs: list[VarSpec],
                   constraint: SumConstraint | None = None) -> Suggestion:
    lo, span = ds.X.min(0), np.ptp(ds.X, axis=0)
    span = np.where(span > 0, span, 1.0)
    x_real = _snap(lo + pick.x_norm * span, inputs, constraint)
    outside = bool(((pick.x_norm < -EXTRAPOLATION_TOL) |
                    (pick.x_norm > 1 + EXTRAPOLATION_TOL)).any())
    return Suggestion(
        x_norm=pick.x_norm, x_real=x_real, acq_value=pick.acq_value,
        predicted_mean=pick.mean, predicted_std=pick.std,
        label=format_condition(x_real, inputs), extrapolated=outside,
        _reps=recommended_reps(ds),
    )


def recommended_reps(ds: Dataset) -> int:
    """Recommended replicate count — follows the median of the current data.

    Measuring a new condition just once drags discriminability down and worsens
    the next verdict. Writing "measure it n times" on the instruction sheet is
    what makes it actually happen.
    """
    counts = [len(v) for v in ds.reps]
    return max(1, int(np.median(counts))) if counts else 1
