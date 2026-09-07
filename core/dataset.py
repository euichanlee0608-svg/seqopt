# -*- coding: utf-8 -*-
"""Condition grouping · exclusions · normalization (spec §5-1).

`build()` turns a row list into a per-condition `Dataset`. In the state flow
(§7-3), every added measurement **re-runs from here.** No partial updates.
"""
from __future__ import annotations

import numpy as np

from .spec import Dataset, ObjSpec, VarSpec


def group_measurements(measurements: list[dict], round_digits: int = 6
                       ) -> dict[tuple, list[float]]:
    """Measurement rows → {condition: [values...]}.

    **Entering the same condition on several rows is automatically read as
    replicates** (F-03). Rows with `excluded=True` are dropped here — the user
    checked them off in the table.
    """
    groups: dict[tuple, list[float]] = {}
    for m in measurements:
        # excluded: rows the user removed · pending: rows pre-filled from a
        # recommendation but not yet measured. Feeding a pending row as 0 would
        # wreck the response surface and the gate verdict wholesale.
        if m.get("excluded") or m.get("pending"):
            continue
        key = tuple(round(float(v), round_digits) for v in m["inputs"])
        groups.setdefault(key, []).append(float(m["value"]))
    return groups


def from_measurements(measurements: list[dict], inputs: list[VarSpec], objective: ObjSpec,
                      exclude_zero: bool = False,
                      exclude_conditions: list[tuple] | None = None,
                      round_digits: int = 6) -> Dataset:
    """Build a Dataset straight from the row list (the start of the §7-3 state flow)."""
    groups = group_measurements(measurements, round_digits)
    if not groups:
        raise ValueError("There are no measurements")            # i18n: skip (main_window catches it and writes its own line)
    return build(groups, inputs, objective, exclude_zero, exclude_conditions)


def build(groups: dict[tuple, list[float]], inputs: list[VarSpec], objective: ObjSpec,
          exclude_zero: bool = False,
          exclude_conditions: list[tuple] | None = None) -> Dataset:
    """Per-condition response groups → Dataset.

    exclude_zero          drop conditions whose responses are all 0 (F-05 — e.g. destroyed samples)
    exclude_conditions    conditions the user checked off
    """
    manual = set(exclude_conditions or ())
    keys_all = sorted(groups)

    live, dead = [], []
    for k in keys_all:
        v = groups[k]
        dropped = k in manual or (exclude_zero and max(v) <= 0)
        (dead if dropped else live).append(k)

    if not live:
        raise ValueError("No usable conditions remain — check the exclusion rules")   # i18n: skip (caught, never shown)

    X = np.array(live, dtype=float)
    reps = [objective.to_internal(np.asarray(groups[k], dtype=float)) for k in live]
    y_mean = np.array([v.mean() for v in reps])

    span = np.ptp(X, axis=0)
    XN = (X - X.min(0)) / (span + 1e-12)

    return Dataset(
        X=X, XN=XN, y_mean=y_mean, reps=reps,
        inputs=inputs, objective=objective,
        n_excluded_rows=int(sum(len(groups[k]) for k in dead)),
        n_excluded_conditions=len(dead),
        n_conditions_all=len(keys_all),
        excluded_conditions=dead,
    )
