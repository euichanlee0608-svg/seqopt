# -*- coding: utf-8 -*-
"""Initial design — maximin LHS (spec §2-2 item 5 · F-22).

Space-filling instead of a grid, for a reason that came out of the validation
study: measured on a grid, curved terrain looks flat, and **more replicates do
not fix that** (raising replicates 3→5 moved the worst-case loss only
0.2403→0.2409).
"""
from __future__ import annotations

import numpy as np

from .spec import SumConstraint, VarSpec

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


def initial_design(k: int, inputs: list[VarSpec], seed: int = 0,
                   constraint: SumConstraint | None = None) -> np.ndarray:
    """Initial design points (original units) honoring integer/categorical/step/sum constraints.

    Integer variables are rounded and a continuous variable with a step snaps
    to its grid. If snapping creates duplicates, they stay — **a duplicate is a
    replicate measurement**, and replicates raise discriminability.
    With a sum constraint, the space-filling (maximin) points are picked on the
    constraint surface.
    """
    if constraint is None:
        unit = maximin_lhs(k, len(inputs), seed=seed)
    else:
        unit = feasible_maximin(k, inputs, constraint, seed=seed)
    return to_real(unit, inputs, constraint)


def to_real(unit: np.ndarray, inputs: list[VarSpec],
            constraint: SumConstraint | None = None) -> np.ndarray:
    """[0,1] coordinates → measurable values in original units (categorical → index, integer/step snapped, sum constraint kept)."""
    unit = np.atleast_2d(np.asarray(unit, dtype=float))
    out = np.empty_like(unit)
    for j, v in enumerate(inputs):
        if v.type == "categorical":
            idx = np.minimum((unit[:, j] * len(v.levels)).astype(int), len(v.levels) - 1)
            out[:, j] = idx
        else:
            raw = v.lo + unit[:, j] * (v.hi - v.lo)
            out[:, j] = [v.snap(x) for x in raw]
    if constraint is not None:
        out = np.array([snap_to_constraint(row, inputs, constraint) for row in out])
    return out


# ══════════════════════════════════════════════════════════════════════
# Sum constraint — sample on the constraint surface, snap to the grid but keep the sum
# ══════════════════════════════════════════════════════════════════════
def _grid_step(v: VarSpec) -> float | None:
    if v.type == "integer":
        return 1.0
    return v.step


def snap_to_constraint(x_real: np.ndarray, inputs: list[VarSpec],
                       constraint: SumConstraint) -> np.ndarray:
    """Snap to the grid, then if the sum is off, move **in step units** until the sum is restored (largest-remainder style).

    Among variables without a step, the later ones absorb the remainder.
    """
    x = np.asarray(x_real, dtype=float).copy()
    idx = constraint.indices(inputs)
    vs = [inputs[k] for k in idx]
    steps = [_grid_step(v) for v in vs]
    for k in idx:
        x[k] = inputs[k].snap(x[k])
    total = float(np.sum(x[idx]))
    if constraint.kind == "le" and total <= constraint.total + 1e-9:
        return x
    if constraint.kind == "eq" and abs(total - constraint.total) <= 1e-9 * max(1.0, abs(constraint.total)):
        return x

    if any(h is None for h in steps):
        # with a step-less variable, put the remainder on it (within its range)
        free = [k for k, h in zip(idx, steps) if h is None]
        need = constraint.total - total
        for k in free:
            v = inputs[k]
            room = (v.hi - x[k]) if need > 0 else (x[k] - v.lo)
            move = float(np.sign(need) * min(abs(need), room))
            x[k] += move
            need -= move
            if abs(need) < 1e-12:
                break
        return x

    h = steps[0]                                   # validate() guarantees a shared step
    need = constraint.total - total
    n_moves = int(round(abs(need) / h))
    direction = 1.0 if need > 0 else -1.0
    for _ in range(n_moves):
        # among the variables that can move, move the one that drifts least from its original value
        cand = [k for k in idx if inputs[k].lo - 1e-9 <= x[k] + direction * h <= inputs[k].hi + 1e-9]
        if not cand:
            break
        k = min(cand, key=lambda i: abs(x[i] + direction * h - x_real[i]))
        x[k] += direction * h
    return x


def feasible_unit(n: int, inputs: list[VarSpec], constraint: SumConstraint,
                  seed: int = 0) -> np.ndarray:
    """n samples in [0,1] coordinates that satisfy the constraint (spread evenly over the constraint surface).

    The constrained variables are drawn with a Dirichlet so their sum is K, and
    points outside the ranges are discarded (rejection). When the sum exceeds
    half of the range sum, the complement (w − z) is drawn instead to lower the
    rejection rate. A ≤ constraint combines two routes: box sampling with
    rejection, and a Dirichlet with a slack component.
    """
    rng = np.random.default_rng(seed)
    d = len(inputs)
    idx = constraint.indices(inputs)
    w = np.array([inputs[k].hi - inputs[k].lo for k in idx])
    lo = np.array([inputs[k].lo for k in idx])
    K = constraint.total - lo.sum()                 # the sum of z = x − lo
    m = len(idx)
    out: list[np.ndarray] = []
    got = 0
    for _ in range(60):
        draw = max(4 * (n - got), 2000)
        z_list = []
        if constraint.kind == "eq":
            flip = K > w.sum() / 2
            target = w.sum() - K if flip else K
            z = rng.dirichlet(np.ones(m), draw) * target
            if flip:
                z = w - z
            z_list.append(z)
        else:
            box = rng.random((draw, m)) * w
            z_list.append(box[box.sum(1) <= K + 1e-12])
            z = rng.dirichlet(np.ones(m + 1), draw)[:, :m] * K
            z_list.append(z)
        for z in z_list:
            ok = np.all((z >= -1e-12) & (z <= w + 1e-12), axis=1)
            z = z[ok]
            if not len(z):
                continue
            u = rng.random((len(z), d))
            u[:, idx] = np.where(w > 0, z / np.where(w > 0, w, 1.0), 0.0)
            out.append(np.clip(u, 0.0, 1.0))
            got += len(z)
        if got >= n:
            break
    if not out:
        raise ValueError(f"No point satisfying constraint {constraint.describe()} could be found")
    allu = np.vstack(out)
    return allu[rng.permutation(len(allu))[:n]] if len(allu) >= n else allu


def feasible_maximin(k: int, inputs: list[VarSpec], constraint: SumConstraint,
                     seed: int = 0, pool: int = 60) -> np.ndarray:
    """The k candidates on the constraint surface that are farthest from each other (greedy maximin)."""
    cand = feasible_unit(max(pool * k, 500), inputs, constraint, seed=seed)
    chosen = [int(np.argmin(np.sum((cand - cand.mean(0)) ** 2, axis=1)))]   # start from the center
    dist = np.linalg.norm(cand - cand[chosen[0]], axis=1)
    while len(chosen) < min(k, len(cand)):
        nxt = int(np.argmax(dist))
        chosen.append(nxt)
        dist = np.minimum(dist, np.linalg.norm(cand - cand[nxt], axis=1))
    return cand[chosen]
