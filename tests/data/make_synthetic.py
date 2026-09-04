# -*- coding: utf-8 -*-
"""Generate the synthetic lab spreadsheet the regression tests anchor on.

    python tests/data/make_synthetic.py            # writes synthetic_raman.xlsx + synthetic_expect.json

**Why synthetic** — the original study anchored these tests on a real lab
dataset that is not distributed. This file reproduces the *structure* that the
loaders and diagnostics must handle, with values designed here:

  · 2 reference-sample text rows at the top that must never leak into conditions
  · 25 conditions (A=power · B=dwell), 10 of them all-zero (destroyed samples)
  · 69 measurement rows, 45 of them on the 15 live conditions
  · 2 `#DIV/0!` response cells that must be reported as missing, not read as 0
  · extra numeric columns C (D band) · D (G band) · F (Avg) that the role
    guesser must NOT mistake for inputs
  · replicates 1–6 per condition (median 3, 14/15 replicated)
  · one condition with inflated within-variance (the "dominant condition")
  · a weak, spatially unstructured signal → D lands between the gate (1) and
    the recommended mark (2), the bootstrap interval straddles 1.0, and
    LOOCV R² < 0 — the exact regime this tool exists to catch

**Independence** — this script never imports `core`. The expectations in
synthetic_expect.json are computed here with plain numpy from the designed
values, so the tests compare two independent implementations.
The seed is pinned; regenerating must be a deliberate act (never automatic).
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEED = 20260909

POWERS = [150, 160, 170, 180, 190]
DWELLS = [3, 4, 5, 6, 7]
# 25 conditions = 5×5 grid. The last 10 (power 190 rows + dwell 7 column tail)
# are "destroyed samples": every response is 0.
DEAD = {(190, d) for d in DWELLS} | {(p, 7) for p in POWERS}          # 5 + 5, overlap (190,7) → 9
DEAD.add((180, 3))                                                     # → 10 dead conditions
# replicate counts for the 15 live conditions, in grid order (median 3, one singleton)
REP_COUNTS = [3, 2, 3, 4, 1, 3, 5, 2, 3, 6, 2, 4, 3, 2, 2]            # sums to 45
DOMINANT = (180, 6)         # gets inflated within-condition variance
SIGMA_NOISE = 0.09          # within-condition wobble
SIGMA_TREND = 0.088         # weak unstructured between-condition signal
BASE = 1.15                 # typical response level


TOP_SHARE_TARGET = 0.48     # the dominant condition's share of within-condition variance


def design() -> tuple[list[tuple[int, int]], dict, dict]:
    rng = np.random.default_rng(SEED)
    live = [(p, d) for p in POWERS for d in DWELLS if (p, d) not in DEAD]
    assert len(live) == 15 and len(DEAD) == 10
    means = {c: BASE + rng.normal(0, SIGMA_TREND) for c in live}
    reps: dict[tuple, list[float]] = {}
    for c, n in zip(live, REP_COUNTS):
        reps[c] = [float(means[c] + rng.normal(0, SIGMA_NOISE)) for _ in range(n)]

    # Make the dominant condition deterministic: scale its deviations so its
    # (n−1)·var is exactly TOP_SHARE_TARGET of the total. Hoping a random draw
    # lands there is how fixtures go stale.
    rest = sum((len(v) - 1) * np.var(v, ddof=1)
               for c, v in reps.items() if len(v) > 1 and c != DOMINANT)
    dom = np.array(reps[DOMINANT])
    cur = (len(dom) - 1) * dom.var(ddof=1)
    target = TOP_SHARE_TARGET / (1 - TOP_SHARE_TARGET) * rest
    dom = dom.mean() + (dom - dom.mean()) * np.sqrt(target / cur)
    reps[DOMINANT] = list(dom)
    reps = {c: [round(v, 4) for v in vals] for c, vals in reps.items()}
    return live, means, reps


def expectations(reps: dict) -> dict:
    """σw · σb · D and friends, computed here with plain numpy (not core/)."""
    live = list(reps)
    arrs = [np.array(reps[c], dtype=float) for c in live]
    means = np.array([a.mean() for a in arrs])
    sigma_b = float(means.std(ddof=1))
    multi = [(c, a) for c, a in zip(live, arrs) if len(a) > 1]
    ss = float(sum((len(a) - 1) * a.var(ddof=1) for _, a in multi))
    df = int(sum(len(a) - 1 for _, a in multi))
    sigma_w = float(np.sqrt(ss / df))
    top_c, top_a = max(multi, key=lambda kv: (len(kv[1]) - 1) * kv[1].var(ddof=1))
    top_ss = float((len(top_a) - 1) * top_a.var(ddof=1))
    ss2, df2 = ss - top_ss, df - (len(top_a) - 1)
    m2 = np.array([a.mean() for c, a in zip(live, arrs) if c != top_c])
    sw2 = float(np.sqrt(ss2 / df2))
    sb2 = float(m2.std(ddof=1))
    rep_dist: dict[int, int] = {}
    for a in arrs:
        rep_dist[len(a)] = rep_dist.get(len(a), 0) + 1
    return {
        "conditions_all": 25, "conditions_live": 15, "conditions_dead": 10,
        "measurements": int(sum(len(a) for a in arrs)),
        "rep_dist": {str(k): v for k, v in sorted(rep_dist.items())},
        "n_median": float(np.median([len(a) for a in arrs])),
        "sigma_w": sigma_w, "sigma_b": sigma_b,
        "total_ss": ss, "total_df": df,
        "D": {str(n): sigma_b / (sigma_w / np.sqrt(n)) for n in (1, 2, 3, 4, 5, 6)},
        "top_cond": f"{top_c[0]}W-{top_c[1]}s",
        "top_share": top_ss / ss * 100,
        "sw_drop_top": sw2, "sb_drop_top": sb2, "D_drop_top": sb2 / sw2,
    }


# ── minimal xlsx writer (mirrors what core.importer reads) ─────────────
def _col(i: int) -> str:
    return chr(ord("A") + i)


def write_xlsx(path: Path, rows: list[list]) -> None:
    """rows: lists of cell values; str → shared string, float/int → number, None → empty."""
    sst: list[str] = []

    def cell(r: int, c: int, v):
        ref = f"{_col(c)}{r}"
        if v is None:
            return ""
        if isinstance(v, str):
            if v not in sst:
                sst.append(v)
            return f'<c r="{ref}" t="s"><v>{sst.index(v)}</v></c>'
        return f'<c r="{ref}"><v>{v}</v></c>'

    body = "".join(
        f'<row r="{ri}">' + "".join(cell(ri, ci, v) for ci, v in enumerate(row)) + "</row>"
        for ri, row in enumerate(rows, start=1))
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    sheet = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{ns}"><sheetData>{body}</sheetData></worksheet>'
    strings = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               f'<sst xmlns="{ns}" count="{len(sst)}" uniqueCount="{len(sst)}">'
               + "".join(f"<si><t>{s}</t></si>" for s in sst) + "</sst>")
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
          '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
          '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>')
    wb = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          f'<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
    wbrels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
              '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
              '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", wbrels)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
        z.writestr("xl/sharedStrings.xml", strings)


def main() -> None:
    rng = np.random.default_rng(SEED + 1)
    live, _means, reps = design()

    rows: list[list] = [["power", "dwell", "D band", "G band", "G/D", "Avg"]]
    # reference-sample rows — text in the input columns must break inheritance
    for k in (1, 2):
        rows.append(["pristine C paper", None, round(float(rng.uniform(900, 1100)), 1),
                     round(float(rng.uniform(1500, 1800)), 1), round(float(rng.uniform(1.4, 1.6)), 4), None])

    order = [(p, d) for p in POWERS for d in DWELLS]
    for c in order:
        p, d = c
        if c in DEAD:
            # zeros; still real rows in the sheet. (190,3) additionally carries the
            # two #DIV/0! cells — but keeps a numeric 0 row too, so the condition
            # itself still exists and only the cells count as missing.
            n_rows = 2 if c != (190, 7) else 3
            for i in range(n_rows):
                rows.append([p, d, 0, 0, 0, None])
            if c == (190, 3):
                rows.append([p, d, 0, 0, "#DIV/0!", None])
                rows.append([p, d, 0, 0, "#DIV/0!", None])
            continue
        vals = reps[c]
        for i, v in enumerate(vals):
            dband = round(float(rng.uniform(400, 700)), 1)
            rows.append([p, d, dband, round(dband * v, 1), v,
                         round(float(np.mean(vals)), 4) if i == len(vals) - 1 else None])

    write_xlsx(HERE / "synthetic_raman.xlsx", rows)
    exp = expectations(reps)
    # sheet rows minus header = measurement rows the importer sees
    exp["xlsx_rows"] = len(rows) - 1
    (HERE / "synthetic_expect.json").write_text(
        json.dumps(exp, indent=1), encoding="utf-8")
    print(f"rows(sheet)={len(rows) - 1}  live_measurements={exp['measurements']}")
    print(f"sigma_w={exp['sigma_w']:.4f}  sigma_b={exp['sigma_b']:.4f}  "
          f"D1={exp['D']['1']:.3f}  top_share={exp['top_share']:.1f}%  top={exp['top_cond']}")


if __name__ == "__main__":
    main()
