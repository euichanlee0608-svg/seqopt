# -*- coding: utf-8 -*-
"""Variable/objective definitions and the per-condition data structure.

Never imports the GUI (spec §7-2). Everything here runs from the CLI.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from .i18n import tr

VarType = Literal["continuous", "integer", "categorical"]
CANDIDATE_CAP = 10_000_000       # candidates are not counted beyond this — enough to compare with a budget


@dataclass(frozen=True)
class VarSpec:
    """Definition of one input variable (F-01 · F-02)."""

    name: str
    unit: str = ""
    type: VarType = "continuous"
    lo: float | None = None
    hi: float | None = None
    levels: tuple[str, ...] = ()          # categorical only
    step: float | None = None             # continuous only — the grid the instrument can actually set

    def __post_init__(self):
        if self.type == "categorical":
            if not self.levels:
                raise ValueError(tr("{name}: a categorical variable needs levels", name=self.name))
        else:
            if self.lo is None or self.hi is None:
                raise ValueError(tr("{name}: min and max are required", name=self.name))
            if not self.lo < self.hi:
                raise ValueError(tr("{name}: min ({lo}) must be < max ({hi})",
                                    name=self.name, lo=self.lo, hi=self.hi))
        if self.step is not None:
            if self.type != "continuous":
                raise ValueError(tr("{name}: a step is only for continuous variables", name=self.name))
            if not self.step > 0:
                raise ValueError(tr("{name}: the step must be > 0", name=self.name))
            if self.step > self.hi - self.lo:
                raise ValueError(tr("{name}: step ({step}) is larger than the range ({span})",
                                    name=self.name, step=f"{self.step:g}", span=f"{self.hi - self.lo:g}"))

    def n_levels(self) -> int | None:
        """Number of values that can actually be chosen. None (infinite) for a continuous variable without a step.

        Gate ① uses this to count candidates (SPEC_AMENDMENTS A6).
        """
        if self.type == "categorical":
            return len(self.levels)
        if self.type == "integer":
            return int(math.floor(self.hi) - math.ceil(self.lo)) + 1
        if self.step is not None:
            return int(math.floor((self.hi - self.lo) / self.step + 1e-9)) + 1
        return None

    def snap(self, value: float) -> float:
        """Move to a value that can be measured — integers round, a step snaps to the nearest grid point."""
        if self.type == "integer":
            return float(np.round(value))
        if self.type == "continuous" and self.step is not None:
            k = np.round((value - self.lo) / self.step)
            return float(np.clip(self.lo + k * self.step, self.lo, self.hi))
        return float(value)


@dataclass(frozen=True)
class SumConstraint:
    """Linear sum constraint — e.g. composition A+B+C = 100 %, or additives ≤ 5 wt%.

    The variables in `names` (continuous · integer) must sum to `total` (eq) or
    to at most `total` (le). Initial design, candidate generation and the
    recommendation all pick points only inside this constraint, and gate ①
    counts only the candidates that satisfy it.
    """

    names: tuple[str, ...]
    total: float
    kind: Literal["eq", "le"] = "eq"

    def __post_init__(self):
        if len(self.names) < 2:
            raise ValueError(tr("A sum constraint needs at least 2 variables"))
        if len(set(self.names)) != len(self.names):
            raise ValueError(tr("The same variable appears twice in the sum constraint"))
        if self.kind not in ("eq", "le"):
            raise ValueError(f"Unknown constraint kind: {self.kind}")   # i18n: skip (a programming mistake)

    @property
    def symbol(self) -> str:
        return "=" if self.kind == "eq" else "≤"

    def describe(self) -> str:
        return f"{' + '.join(self.names)} {self.symbol} {self.total:g}"

    def indices(self, inputs: list["VarSpec"]) -> list[int]:
        by_name = {v.name: k for k, v in enumerate(inputs)}
        missing = [n for n in self.names if n not in by_name]
        if missing:
            raise ValueError(tr("The constraint names variables that do not exist: {names}",
                                names=", ".join(missing)))
        return [by_name[n] for n in self.names]

    def satisfied(self, x_real: np.ndarray, inputs: list["VarSpec"],
                  tol: float = 1e-6) -> bool:
        s = float(np.sum(np.asarray(x_real, dtype=float)[self.indices(inputs)]))
        eps = tol * max(1.0, abs(self.total))
        return abs(s - self.total) <= eps if self.kind == "eq" else s <= self.total + eps

    def validate(self, inputs: list["VarSpec"]) -> None:
        """Check it fits the design definition — no categoricals, a reachable total, matching steps."""
        idx = self.indices(inputs)
        vs = [inputs[k] for k in idx]
        bad = [v.name for v in vs if v.type == "categorical"]
        if bad:
            raise ValueError(tr("A sum constraint cannot include categorical variables: {names}",
                                names=", ".join(bad)))
        lo_sum, hi_sum = sum(v.lo for v in vs), sum(v.hi for v in vs)
        if self.kind == "eq" and not (lo_sum - 1e-9 <= self.total <= hi_sum + 1e-9):
            raise ValueError(tr("A sum of {total} cannot be made from these ranges "
                                "(minimum sum {lo} ~ maximum sum {hi})",
                                total=f"{self.total:g}", lo=f"{lo_sum:g}", hi=f"{hi_sum:g}"))
        if self.kind == "le" and self.total < lo_sum - 1e-9:
            raise ValueError(tr("Sum ≤ {total} cannot be made from these ranges (minimum sum {lo})",
                                total=f"{self.total:g}", lo=f"{lo_sum:g}"))
        steps = {v.step if v.type == "continuous" else 1.0 for v in vs}
        if self.kind == "eq" and None not in steps:
            if len(steps) > 1:
                raise ValueError(tr("The variables of a sum = constraint must share the same step"))
            h = next(iter(steps))
            k = (self.total - lo_sum) / h
            if abs(k - round(k)) > 1e-6:
                raise ValueError(tr("A sum of {total} cannot be made with step {step} "
                                    "(it must be a whole number of steps above the minimum sum {lo})",
                                    total=f"{self.total:g}", step=f"{h:g}", lo=f"{lo_sum:g}"))


def count_candidates(inputs: list[VarSpec], constraint: SumConstraint | None = None
                     ) -> int | None:
    """Number of conditions that can actually be chosen in the design space. None when infinite.

    Gate ① compares **this value** with the budget — not the number of
    conditions already measured — because the rule means "if there are fewer
    candidates to choose from than budget, measuring everything is better".
    With a constraint only the grid points satisfying it are counted
    (subset-sum dynamic programming).
    """
    levels = [v.n_levels() for v in inputs]
    if constraint is None:
        if any(n is None for n in levels):
            return None
        total = 1
        for n in levels:
            total *= n
            if total >= CANDIDATE_CAP:
                return CANDIDATE_CAP
        return total

    idx = constraint.indices(inputs)
    free = [levels[k] for k in range(len(inputs)) if k not in idx]
    if any(n is None for n in free):
        return None
    if any(levels[k] is None for k in idx):
        return None                                 # a continuous hyperplane — infinite
    n_free = 1
    for n in free:
        n_free *= n

    # lift the constrained variables' grid values to integer units and count the partial sums
    grids = []
    for k in idx:
        v = inputs[k]
        if v.type == "integer":
            grids.append([float(i) for i in range(math.ceil(v.lo), math.floor(v.hi) + 1)])
        else:
            grids.append([v.lo + i * v.step for i in range(levels[k])])
    unit = min(min(abs(g - grids[i][0]) for g in grids[i][1:]) for i in range(len(grids))
               if len(grids[i]) > 1) if any(len(g) > 1 for g in grids) else 1.0
    unit = unit / 1000.0                            # 1/1000 of a step as the integer unit
    to_int = lambda x: int(round(x / unit))
    counts: dict[int, int] = {0: 1}
    for g in grids:
        nxt: dict[int, int] = {}
        for s, c in counts.items():
            for val in g:
                key = s + to_int(val)
                nxt[key] = nxt.get(key, 0) + c
        counts = nxt
        if len(counts) > 2_000_000:
            return CANDIDATE_CAP
    target = to_int(constraint.total)
    tol = max(1, to_int(1e-6 * max(1.0, abs(constraint.total))))
    if constraint.kind == "eq":
        n_con = sum(c for s, c in counts.items() if abs(s - target) <= tol)
    else:
        n_con = sum(c for s, c in counts.items() if s <= target + tol)
    return min(n_con * n_free, CANDIDATE_CAP)


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

    def to_plot(self, v: np.ndarray) -> np.ndarray:
        """Internal coordinates → what a figure may show. **Undoes the sign only.**

        The log stays, because the model — and therefore the ±2σ band, the LOOCV
        residuals and the surface itself — lives in log space. Squeezing it back
        would bend those distances. The axis says so instead (`plot_label`).
        """
        return v * self.sign

    def from_internal(self, v: np.ndarray) -> np.ndarray:
        """Internal coordinates → **the user's own number.** The full inverse of `to_internal`."""
        v = v * self.sign
        return 10.0 ** v if self.log else v

    def plot_label(self, stacked: bool = False) -> str:
        """The axis label for a figure drawn in plot space — the log is said out loud.

        `stacked` puts the log on its own line: rotated along a small validation panel,
        "log10 Conductivity" in one line is longer than the panel is tall.
        """
        if not self.log:
            return self.name
        return tr("log10\n{name}", name=self.name) if stacked else tr("log10 {name}", name=self.name)


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


def candidate_summary(inputs: list[VarSpec], constraint: SumConstraint | None = None) -> str:
    """The sentence behind gate ①. "30 candidate conditions (power 6 × dwell 5)" or "infinitely many candidates …"."""
    n = count_candidates(inputs, constraint)
    parts = []
    for v in inputs:
        k = v.n_levels()
        parts.append(f"{v.name} {k}" if k is not None else f"{v.name} ∞")
    if n is None:
        free = [v.name for v in inputs if v.n_levels() is None]
        return (tr("infinitely many candidates — continuous variable(s) {names} have no step",
                   names=", ".join(free))
                + (tr(" (constraint {what})", what=constraint.describe()) if constraint else ""))
    if n >= CANDIDATE_CAP:
        return tr("{cap} candidate conditions or more ({parts})",
                  cap=f"{CANDIDATE_CAP:,}", parts=" × ".join(parts))
    body = " × ".join(parts)
    if constraint is not None:
        body += tr(", within constraint {what}", what=constraint.describe())
    return tr("{n} candidate conditions ({parts})", n=f"{n:,}", parts=body)
