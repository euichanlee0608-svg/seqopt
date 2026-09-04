# -*- coding: utf-8 -*-
"""Variable/objective definitions and the per-condition data structure.

Never imports the GUI (spec §7-2). Everything here runs from the CLI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

VarType = Literal["continuous", "integer", "categorical"]


@dataclass(frozen=True)
class VarSpec:
    """Definition of one input variable (F-01 · F-02)."""

    name: str
    unit: str = ""
    type: VarType = "continuous"
    lo: float | None = None
    hi: float | None = None
    levels: tuple[str, ...] = ()          # categorical only

    def __post_init__(self):
        if self.type == "categorical":
            if not self.levels:
                raise ValueError(f"{self.name}: a categorical variable needs levels")
        else:
            if self.lo is None or self.hi is None:
                raise ValueError(f"{self.name}: min and max are required")
            if not self.lo < self.hi:
                raise ValueError(f"{self.name}: min ({self.lo}) must be < max ({self.hi})")


@dataclass(frozen=True)
class ObjSpec:
    """Objective definition. goal='min' flips the sign internally so we always maximize (§5-1)."""

    name: str
    unit: str = ""
    goal: Literal["max", "min"] = "max"
    log: bool = False

    @property
    def sign(self) -> int:
        return 1 if self.goal == "max" else -1

    def to_internal(self, v: np.ndarray) -> np.ndarray:
        """Raw data → internal coordinates (bigger is better). log is §5-1 item 4, sign is item 6."""
        if self.log:
            v = np.log10(np.maximum(v, 1e-12))
        return v * self.sign


def suggest_log_transform(values: np.ndarray) -> bool:
    """Recommend a log transform when the response spans orders of magnitude (§5-1 item 4).

    Instead of asking the user "log transform?", decide from the data.
    The rationale is written out on screen as a sentence so the user can
    overrule it.
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v) & (v > 0)]
    if len(v) < 3:
        return False
    return float(v.max() / v.min()) >= 100.0        # spans two orders of magnitude or more


@dataclass
class Dataset:
    """Data grouped by condition (the result of §5-1 preprocessing).

    X       per-condition inputs (original units)      shape (n_cond, d)
    XN      min-max normalized inputs                   shape (n_cond, d)   — required to compare length scales
    y_mean  condition means (internal coordinates)      shape (n_cond,)
    reps    per-condition replicate values (internal)   list of 1-D array
    """

    X: np.ndarray
    XN: np.ndarray
    y_mean: np.ndarray
    reps: list[np.ndarray]
    inputs: list[VarSpec]
    objective: ObjSpec
    n_excluded_rows: int = 0
    n_excluded_conditions: int = 0
    n_conditions_all: int = 0
    excluded_conditions: list[tuple] = field(default_factory=list)

    @property
    def n_conditions(self) -> int:
        """Number of usable conditions. Gate ① reads this (SPEC_AMENDMENTS A4)."""
        return len(self.y_mean)

    @property
    def n_measurements(self) -> int:
        return int(sum(len(v) for v in self.reps))

    @property
    def frac_with_reps(self) -> float:
        """Fraction of conditions with replicates (n≥2). Gate ④."""
        if not self.reps:
            return 0.0
        return sum(1 for v in self.reps if len(v) > 1) / len(self.reps)

    @property
    def rep_distribution(self) -> dict[int, int]:
        out: dict[int, int] = {}
        for v in self.reps:
            out[len(v)] = out.get(len(v), 0) + 1
        return dict(sorted(out.items()))
