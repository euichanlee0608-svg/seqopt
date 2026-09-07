# -*- coding: utf-8 -*-
"""Reading tabular files (F-04).

xlsx is read directly as zip+XML with no external dependency — it keeps the
deployment to lab PCs light.

Two mandatory rules from §6-2 are handled here.
  · Merged/blank cells inherit the value above them (the common lab format
    where a condition is written only on the first row of its block)
  · Non-numeric cells like `#DIV/0!` become missing values, and the count is reported
"""
from __future__ import annotations

import collections
import csv as _csv
import re
import xml.etree.ElementTree as ET
import zipfile

from .i18n import tr

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def to_num(x) -> float | None:
    """float if numeric, else None. `#DIV/0!`, blanks and strings get filtered here."""
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def read_xlsx(path: str, sheet: int = 1) -> list[dict[str, str]]:
    """Read a worksheet as a list of rows keyed by column letter (A, B, ...).

    A cell with no value has no key at all. No inheritance happens here
    (that is read_conditions' job).
    """
    z = zipfile.ZipFile(path)
    sst: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")):
            sst.append("".join(t.text or "" for t in si.iter(NS + "t")))

    rows: list[dict[str, str]] = []
    ws = ET.fromstring(z.read(f"xl/worksheets/sheet{sheet}.xml"))
    for row in ws.iter(NS + "row"):
        cells: dict[str, str] = {}
        for cell in row.iter(NS + "c"):
            ref = re.match(r"([A-Z]+)", cell.get("r")).group(1)
            v = cell.find(NS + "v")
            if v is None:
                continue
            cells[ref] = sst[int(v.text)] if cell.get("t") == "s" else v.text
        rows.append(cells)
    return rows


def read_csv(path: str) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(_csv.DictReader(f))


def column_keys(rows: list[dict]) -> list[str]:
    """Every column key that appears, in table order. xlsx gives A,B,... / csv gives header names."""
    seen: dict[str, None] = {}
    for r in rows:
        for k in r:
            seen.setdefault(k, None)
    keys = list(seen)
    if keys and all(re.fullmatch(r"[A-Z]+", k) for k in keys):
        keys.sort(key=lambda k: (len(k), k))        # A, B, ... Z, AA
    return keys


def preview(path: str, kind: str, sheet: int = 1, limit: int = 200):
    """Read the raw table as-is — the material the mapping screen shows.

    Returns (keys, rows). No interpretation, inheritance or type conversion
    happens here, because the user has to assign roles while looking at
    **the original, untouched table.**
    """
    rows = read_xlsx(path, sheet) if kind == "xlsx" else read_csv(path)
    return column_keys(rows), rows[:limit]


def sheet_count(path: str) -> int:
    z = zipfile.ZipFile(path)
    return sum(1 for n in z.namelist()
               if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))


def apply_profile(rows: list[dict], profile) -> tuple[list[dict], dict]:
    """Interpret rows according to the profile and build the measurement list.

    Returns (measurements, report).
      measurements  [{inputs: [...], value: float, excluded: False, note: ""}, ...]
      report        rows read · missing count · skipped count (F-04 "report the counts")
    """
    ins = profile.input_columns
    resp = profile.response_column
    if not ins or resp is None:
        raise ValueError(tr("Assign the input and response columns first"))

    body = rows[profile.header_row:] if profile.header_row > 0 else rows
    out: list[dict] = []
    n_missing = n_skipped = 0
    current: list[float] | None = None

    for r in body:
        raw = [r.get(c.key) for c in ins]
        nums = [to_num(v) for v in raw]

        if all(v is not None for v in nums):
            current = [round(v, profile.round_digits) for v in nums]
        elif not profile.inherit_blank:
            current = None
        elif any(v is not None and str(v).strip() != "" for v in raw):
            current = None              # a non-numeric value → the block changed

        y = to_num(r.get(resp.key))
        if y is None:
            if r.get(resp.key) is not None and str(r.get(resp.key)).strip() != "":
                n_missing += 1          # value present but not a number, like `#DIV/0!`
            continue
        if current is None:
            n_skipped += 1
            continue
        out.append(dict(inputs=list(current), value=float(y), excluded=False, note=""))

    return out, dict(rows_read=len(body), measurements=len(out),
                     missing=n_missing, skipped=n_skipped)


def group_rows(rows: list[dict], input_cols: list[str], resp_col: str,
               inherit: bool = False) -> tuple[dict[tuple, list[float]], int]:
    """Row list → {condition tuple: [response values...]} plus the missing count.

    With inherit=True, rows whose input columns are blank inherit the previous
    condition. A **non-numeric value** in an input column breaks the
    inheritance — so a foreign block wedged into the table (a stray header or
    reference-sample row) never gets mixed into a condition.
    """
    groups: dict[tuple, list[float]] = collections.defaultdict(list)
    n_missing = 0
    current: tuple | None = None

    for r in rows:
        raw = [r.get(c) for c in input_cols]
        nums = [to_num(v) for v in raw]

        if all(v is not None for v in nums):
            current = tuple(round(v, 6) for v in nums)
        elif not inherit:
            current = None
        elif any(v is not None and str(v).strip() != "" for v in raw):
            current = None            # a row with a non-numeric value → the block changed

        y = to_num(r.get(resp_col))
        if y is None:
            if current is not None and r.get(resp_col) is not None:
                n_missing += 1
            continue
        if current is None:
            continue
        groups[current].append(y)

    return dict(groups), n_missing
