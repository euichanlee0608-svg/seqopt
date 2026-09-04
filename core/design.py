# -*- coding: utf-8 -*-
"""Initial design — maximin LHS (spec §2-2 item 5 · F-22).

Space-filling instead of a grid, for a reason that came out of the validation
study: measured on a grid, curved terrain looks flat, and **more replicates do
not fix that** (raising replicates 3→5 moved the worst-case loss only
0.2403→0.2409).
"""
from __future__ import annotations

import numpy as np

from .spec import VarSpec

INITIAL_FRACTION = (0.25, 0.30)      # recommended initial fraction of the budget (F-22)


def suggest_initial_size(budget: int) -> int:
    """Suggest 25–30% of the budget. Never fewer than 3 points."""
    lo, hi = INITIAL_FRACTION
    return max(3, int(round(budget * (lo + hi) / 2)))


def maximin_lhs(k: int, dim: int, seed: int = 0, tries: int = 200) -> np.ndarray:
    """Pick the LHS in [0,1]^dim whose nearest-neighbor distance is largest.

    Draw several candidates and keep the one with the largest minimum pairwise
    distance (maximin).
    """
    if k < 1:
        raise ValueError("k must be ≥ 1")
    rng = np.random.default_rng(seed)
    best, best_score = None, -np.inf
    for _ in range(tries):
        cand = np.empty((k, dim))
        for j in range(dim):
            cand[:, j] = (rng.permutation(k) + rng.random(k)) / k
        if k == 1:
            return cand
        d = np.linalg.norm(cand[:, None, :] - cand[None, :, :], axis=2)
        score = d[np.triu_indices(k, 1)].min()
        if score > best_score:
            best, best_score = cand, score
    return best


def initial_design(k: int, inputs: list[VarSpec], seed: int = 0) -> np.ndarray:
    """Initial design points (original units) honoring integer/categorical constraints.

    Integer variables are rounded. If rounding creates duplicates, they stay —
    **a duplicate is a replicate measurement**, and replicates raise
    discriminability.
    """
    unit = maximin_lhs(k, len(inputs), seed=seed)
    out = np.empty_like(unit)
    for j, v in enumerate(inputs):
        if v.type == "categorical":
            idx = np.minimum((unit[:, j] * len(v.levels)).astype(int), len(v.levels) - 1)
            out[:, j] = idx
        else:
            out[:, j] = v.lo + unit[:, j] * (v.hi - v.lo)
            if v.type == "integer":
                out[:, j] = np.round(out[:, j])
    return out
