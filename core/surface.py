# -*- coding: utf-8 -*-
"""Response-surface and acquisition-grid computation (spec §3-4, F-30 ~ F-36).

The drawing code lives in `ui/`, but **what to draw is computed here.**
It has to be testable without the GUI, and the reproduction script (F-43)
calls these same functions.

Coordinate convention — everything inside is normalized [0,1]^d. Convert to
original units for display with `to_real()`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal

import numpy as np

from .i18n import tr
from .protocols import Acquisition, Surrogate
from .spec import Dataset, ObjSpec, VarSpec


def to_real(xn: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Normalized coordinates → original units. Inverts the same min-max that built Dataset.XN."""
    lo = X.min(0)
    span = np.ptp(X, axis=0)
    return lo + xn * span


def axis_ticks(X: np.ndarray, axis: int, n: int = 200) -> np.ndarray:
    """Tick values for one axis, in original units."""
    lo, hi = X[:, axis].min(), X[:, axis].max()
    return np.linspace(lo, hi, n)


@dataclass
class Curve1D:
    x_real: np.ndarray
    mu: np.ndarray
    sd: np.ndarray
    ei: np.ndarray
    best: float
    x_best_ei: float          # where EI peaks (original units)


def curve_1d(model: Surrogate, ds: Dataset, best: float, acquisition: Acquisition,
             n: int = 200) -> Curve1D:
    """One variable — μ±2σ curve plus the EI curve (F-30)."""
    xn = np.linspace(0, 1, n).reshape(-1, 1)
    mu, sd = model.predict(xn)
    ei = acquisition.score(model, xn, best)
    x_real = to_real(xn, ds.X)[:, 0]
    return Curve1D(x_real=x_real, mu=mu, sd=sd, ei=ei, best=best,
                   x_best_ei=float(x_real[int(np.argmax(ei))]))


@dataclass
class Grid2D:
    x_real: np.ndarray        # (n,) axis-i in original units
    y_real: np.ndarray        # (n,) axis-j in original units
    mu: np.ndarray            # (n, n)
    sd: np.ndarray
    ei: np.ndarray
    axis_i: int
    axis_j: int
    fixed: np.ndarray         # values the remaining axes are pinned to (normalized)


def grid_2d(model: Surrogate, ds: Dataset, best: float, acquisition: Acquisition,
            axis_i: int = 0, axis_j: int = 1, fixed: np.ndarray | None = None,
            n: int = 60) -> Grid2D:
    """Two-variable surface; with 3+ variables, a slice with the rest pinned (F-31 · F-32).

    When fixed is not given, pin to **the current best condition** — the default
    of spec §4-3. Slice anywhere else and the terrain you see has nothing to do
    with reality.
    """
    d = ds.XN.shape[1]
    if fixed is None:
        fixed = ds.XN[int(np.argmax(ds.y_mean))].copy()
    fixed = np.asarray(fixed, dtype=float).copy()

    g = np.linspace(0, 1, n)
    GI, GJ = np.meshgrid(g, g, indexing="xy")
    pts = np.tile(fixed, (n * n, 1))
    pts[:, axis_i] = GI.ravel()
    if d > 1:
        pts[:, axis_j] = GJ.ravel()

    mu, sd = model.predict(pts)
    ei = acquisition.score(model, pts, best)
    shape = (n, n)

    lo, span = ds.X.min(0), np.ptp(ds.X, axis=0)
    x_real = lo[axis_i] + g * span[axis_i]
    y_real = (lo[axis_j] + g * span[axis_j]) if d > 1 else g
    return Grid2D(x_real=x_real, y_real=y_real,
                  mu=mu.reshape(shape), sd=sd.reshape(shape), ei=ei.reshape(shape),
                  axis_i=axis_i, axis_j=axis_j, fixed=fixed)


def trajectory(measurements: list[dict], objective) -> tuple[np.ndarray, np.ndarray]:
    """Best **measured** value so far, against measurement count (F-34).

    Measured, not true — because that is the value a researcher will actually
    adopt (principle P3).
    """
    vals = [objective.to_internal(np.array([m["value"]]))[0]
            for m in measurements if not m.get("excluded")]
    if not vals:
        return np.array([]), np.array([])
    run = np.maximum.accumulate(np.asarray(vals, dtype=float))
    # the running best is found where bigger is better, then handed back in plot
    # space — a minimization goal must not show its own trajectory as negatives
    return np.arange(1, len(run) + 1), objective.to_plot(run)


def replicate_scatter(ds: Dataset) -> tuple[np.ndarray, list[np.ndarray], np.ndarray]:
    """Per-condition individual points and condition means (F-36), sorted by condition mean ascending."""
    order = np.argsort(ds.y_mean)
    return order, [ds.reps[i] for i in order], ds.y_mean[order]


def slice_defaults(ds: Dataset) -> np.ndarray:
    """Default slider position for the slice = the current best condition (§4-3)."""
    return ds.XN[int(np.argmax(ds.y_mean))].copy()


def nearest_measured(ds: Dataset, xn: np.ndarray) -> int:
    """Index of the measured condition closest to a normalized point. Tells you which real point the slice sits on."""
    return int(np.argmin(np.linalg.norm(ds.XN - np.asarray(xn), axis=1)))


def decimals(var: VarSpec) -> int:
    """How many decimals a value of this variable is shown with.

    The declared step decides (0.5 → 1, 0.25 → 2, 10 → 0); an integer or
    categorical variable gets none; otherwise the range does — three
    significant figures of the span (0–100 → 1, 0–1 → 3, 0–1000 → 0),
    capped at 6. A suggestion is shown at the precision the instrument can
    be set to, never as 89.0915 %.
    """
    if var.type != "continuous":
        return 0
    if var.step is not None:
        exponent = Decimal(f"{var.step:.10g}").normalize().as_tuple().exponent
        return int(min(6, max(0, -exponent)))
    return int(min(6, max(0, 3 - math.floor(math.log10(var.hi - var.lo)))))


def fmt_value(var: VarSpec, x: float) -> str:
    """One value in the precision of `decimals()`; a categorical shows its level name."""
    if var.type == "categorical":
        k = int(min(max(round(float(x)), 0), len(var.levels) - 1))
        return var.levels[k]
    return f"{float(x):.{decimals(var)}f}"


def fmt_response(obj: ObjSpec, v_internal: float) -> str:
    """One response value **in the user's own frame** — sign and log both undone, unit attached.

    Everything the model touches lives in internal coordinates (§5-1: log10 when
    asked for, negated for a minimization goal). Printing those raw said
    "best measured so far 2.931" for a project whose data table reads 853 S/cm.
    Four significant digits, because that is what an instrument reading is worth.
    """
    v = f"{float(obj.from_internal(float(v_internal))):.4g}"
    return f"{v} {obj.unit}" if obj.unit else v


def fmt_prediction(obj: ObjSpec, mean_internal: float, sd_internal: float) -> str:
    """A prediction and its uncertainty, in the user's frame.

    Without a log the σ is in the same units as the mean, so the familiar
    `0.9594 ± 0.017 a.u.` holds. With one it does not: the interval is symmetric
    in log space only, and 10**(μ±σ) is not μ' ± σ'. So the value is converted
    and the pair it came from is shown beside it, log said out loud.
    """
    m = float(obj.to_plot(float(mean_internal)))
    sd, unit = float(sd_internal), (f" {obj.unit}" if obj.unit else "")
    if not obj.log:
        return f"{m:.4g} ± {sd:.3g}{unit}"
    return tr("≈ {value} (log10 {mean} ± {sd})",
              value=f"{10.0 ** m:.4g}{unit}", mean=f"{m:.4g}", sd=f"{sd:.3g}")


def format_condition(x_real: np.ndarray, inputs: list[VarSpec]) -> str:
    parts = []
    for v, x in zip(inputs, x_real):
        parts.append(f"{v.name} {fmt_value(v, x)}{(' ' + v.unit) if v.unit else ''}")
    return " · ".join(parts)
