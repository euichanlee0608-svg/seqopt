# -*- coding: utf-8 -*-
"""Build the bundled example project from the public P3HT:CNT dataset.

    .venv/bin/python examples/make_example.py

Writes examples/p3ht_conductivity.seqopt — the project a first-time user opens
from the start screen.

Why a subset and not all 178 conditions: the learnability check (LOOCV) refits
one GP per condition, so the full dataset takes ~40 s in the background. The
example must show the gate passing within seconds of being opened. The subset
keeps the first N_CONDITIONS conditions in file order, replicates included —
enough to clear gate ① (candidates > budget) and to stay learnable (R² > 0,
verified when this script runs).

Data: Langner et al., Adv. Funct. Mater. 31, 2102606 (2021), via the public
repository github.com/PV-Lab/Benchmarking (tests/data/p3ht.csv).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.diagnostics import discriminability, gate, loocv_r2          # noqa: E402
from core.importer import group_rows, read_csv                          # noqa: E402
from core.profile import ColumnMap, ImportProfile                       # noqa: E402
from core.project import Project                                        # noqa: E402
from core.spec import ObjSpec, VarSpec                                  # noqa: E402

N_CONDITIONS = 48
BUDGET = 40
RESPONSE = "Conductivity (measured) (S/cm)"


def main() -> None:
    rows = read_csv(str(ROOT / "tests" / "data" / "p3ht.csv"))
    cols = [c for c in rows[0] if c != RESPONSE]
    groups, _ = group_rows(rows, cols, RESPONSE, inherit=False)

    # first N conditions in file order — deterministic, replicates kept
    keep: dict[tuple, list[float]] = {}
    for key, vals in groups.items():
        keep[key] = vals
        if len(keep) == N_CONDITIONS:
            break

    inputs = [VarSpec(c, "%", "continuous",
                      float(min(k[i] for k in keep)), float(max(k[i] for k in keep)))
              for i, c in enumerate(cols)]
    project = Project(
        name="Example — P3HT:CNT conductivity",
        inputs=inputs,
        objective=ObjSpec("Conductivity", "S/cm", "max", log=True),
        budget_total=BUDGET,
        import_profile=ImportProfile(
            kind="csv", header_row=1,
            columns=[ColumnMap(c, "input", c, "%") for c in cols]
            + [ColumnMap(RESPONSE, "response", "Conductivity", "S/cm")]),
    )
    for key, vals in keep.items():
        for v in vals:
            project.add([float(x) for x in key], float(v))

    # The example's whole point is a PASSING gate — verify before writing.
    ds = project.dataset()
    d = discriminability(ds.reps)
    r = loocv_r2(ds.XN, ds.y_mean)
    g = gate(ds.n_conditions, BUDGET, r.r2, d, ds.frac_with_reps)
    print(f"conditions={ds.n_conditions}  measurements={ds.n_measurements}  "
          f"D={d.D[1]:.2f} [{d.ci_lo:.2f},{d.ci_hi:.2f}]  R²={r.r2:+.3f}  locked={g.locked}")
    assert ds.n_conditions > BUDGET, "gate ① must pass"
    assert r.r2 > 0, "the example must be learnable"
    assert not g.locked, "the example must open the gate"

    out = ROOT / "examples" / "p3ht_conductivity.seqopt"
    project.save(str(out))
    print("wrote", out)


if __name__ == "__main__":
    main()
