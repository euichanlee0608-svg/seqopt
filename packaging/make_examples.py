# -*- coding: utf-8 -*-
"""Example project generator — a simulated example that **passes the gate and yields a recommendation**.

    .venv/bin/python packaging/make_examples.py          # rewrites examples/synthetic_annealing.seqopt

Two examples ship with the program.
  · P3HT:CNT conductivity — real public data (examples/make_example.py): what the tool does
    with a measured dataset whose continuous inputs have no instrument grid.
  · Synthetic annealing — made by this file. Simulated data on an instrument grid that
    passes every requirement, so the tool **gives a recommendation** near a known optimum
    (what the tool delivers).

That the data is simulated is stated three times — file name, project name and notes.
It must never be mistaken for a real measurement. The values come from a seeded random
generator, so regenerating yields the same file every time (verifiable with git diff).

**Simulated function** — a crystallinity index (0–1) of annealing temperature T (°C) and
time t (min). The peak sits near (290 °C, 40 min); too high a temperature degrades the
sample, and time is gentle. A single peak lets gate ② learn it, and the noise (3 % of the
range) is suppressed enough by 3 replicates for ③ to pass as well.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.design import initial_design                      # noqa: E402
from core.diagnostics import discriminability, gate, loocv_r2  # noqa: E402
from core.project import Project                            # noqa: E402
from core.spec import ObjSpec, VarSpec, count_candidates    # noqa: E402

OUT = ROOT / "examples" / "synthetic_annealing.seqopt"
INPUTS = [VarSpec("temperature", "°C", "continuous", 150.0, 350.0, step=10.0),   # 21 levels
          VarSpec("time", "min", "continuous", 5.0, 60.0, step=5.0)]            # 12 levels → 252 candidates
OBJECTIVE = ObjSpec("crystallinity index", "a.u.", "max")
BUDGET, INITIAL, REPS = 60, 11, 3
NOISE = 0.03                                               # σ = 3 % of the range (≈1)
SEED = 20260905


def truth(T: float, t: float) -> float:
    """Simulated ground truth — the noise-free crystallinity index."""
    u, v = (T - 290.0) / 55.0, (t - 40.0) / 22.0
    peak = np.exp(-(u * u + 0.6 * v * v))
    return float(0.12 + 0.85 * peak - 0.05 * max(0.0, u) ** 2)


def make() -> Project:
    rng = np.random.default_rng(SEED)
    p = Project(name="Synthetic annealing — crystallinity (simulated data)", inputs=list(INPUTS),
                objective=OBJECTIVE, budget_total=BUDGET, initial_design=INITIAL,
                created="2026-09-05T00:00:00+09:00")
    conds = [tuple(row) for row in initial_design(INITIAL, INPUTS, seed=3)]
    conds += [(280.0, 35.0), (300.0, 45.0), (270.0, 50.0)]   # 3 points as if measured in the sequential stage
    for T, t in conds:
        for _ in range(REPS):
            p.add([T, t], round(truth(T, t) + rng.normal(0, NOISE), 4), note="simulated")
    return p


def check(p: Project) -> dict:
    """Judge the four requirements with the real core — only an example that passes ships."""
    ds = p.dataset()
    r2 = loocv_r2(ds.XN, ds.y_mean).r2
    d = discriminability(ds.reps)
    g = gate(count_candidates(p.inputs, p.constraint), p.budget_total, r2, d, ds.frac_with_reps)
    return {"gate": g, "r2": r2, "n_conditions": ds.n_conditions, "used": p.used,
            "candidates": count_candidates(p.inputs, p.constraint)}


def main() -> int:
    warnings.filterwarnings("ignore")
    p = make()
    info = check(p)
    g = info["gate"]
    print(f"{info['n_conditions']} conditions · {info['used']} measurements / budget {p.budget_total} · "
          f"{info['candidates']} candidates · LOOCV R² {info['r2']:.3f}")
    print(f"gate ① {g.cond_count} ② {g.learnable} ③ {g.discrim} ④ {g.replicates} → "
          f"{'LOCKED' if g.locked else 'open'}")
    if g.locked:
        print("An example that fails the requirements is not shipped:", g.reasons)
        return 1
    p.save(str(OUT))
    print(f"→ {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
