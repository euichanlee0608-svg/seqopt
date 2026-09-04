# -*- coding: utf-8 -*-
"""Import profile — "how should this spreadsheet be read" stored as a value.

The spec (F-04) only asked for a column-mapping UI, but in a lab **every
instrument and every person has their own spreadsheet format, and the same
format keeps coming back.** So the mapping is factored out into a profile,
instead of being redone by hand every time.

  · Saved inside the project file (.seqopt) → reopening reads the same way
  · Exportable as a preset (.seqmap) → reusable for other files from the same instrument
  · When the format changes, only the profile changes. Data and diagnostics code stay put.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Literal

Role = Literal["ignore", "input", "response"]


@dataclass
class ColumnMap:
    """What role one original column plays."""

    key: str                          # original column id (xlsx: "A", csv: header name)
    role: Role = "ignore"
    name: str = ""                    # variable name (falls back to key when empty)
    unit: str = ""
    type: Literal["continuous", "integer", "categorical"] = "continuous"

    @property
    def label(self) -> str:
        return self.name or self.key


@dataclass
class ImportProfile:
    """The full rule set that turns a file into a list of measurement rows."""

    kind: Literal["xlsx", "csv"] = "xlsx"
    sheet: int = 1
    header_row: int = 1               # 1-based. 0 means no header
    columns: list[ColumnMap] = field(default_factory=list)

    inherit_blank: bool = False       # merged/blank cells inherit the previous condition (§6-2, mandatory)
    exclude_zero: bool = False        # conditions whose response is 0 become exclusion candidates (F-05)
    round_digits: int = 6             # grouping precision for conditions (§5-1 item 1)

    name: str = ""                    # preset name
    note: str = ""

    # ── access by role ─────────────────────────────────────────────
    @property
    def input_columns(self) -> list[ColumnMap]:
        return [c for c in self.columns if c.role == "input"]

    @property
    def response_column(self) -> ColumnMap | None:
        for c in self.columns:
            if c.role == "response":
                return c
        return None

    def validate(self) -> list[str]:
        """Is the configuration coherent? An empty list means yes."""
        errs = []
        ins = self.input_columns
        if not ins:
            errs.append("Assign at least one input variable")
        if len(ins) > 10:
            errs.append(f"At most 10 input variables (currently {len(ins)})")
        if self.response_column is None:
            errs.append("Assign exactly one response variable")
        if sum(1 for c in self.columns if c.role == "response") > 1:
            errs.append("Only one response variable can be assigned (multi-objective is out of scope)")
        labels = [c.label for c in self.columns if c.role != "ignore"]
        dup = {n for n in labels if labels.count(n) > 1}
        if dup:
            errs.append(f"Duplicate names: {', '.join(sorted(dup))}")
        return errs

    # ── save / load ────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ImportProfile":
        d = dict(d)
        d["columns"] = [ColumnMap(**c) for c in d.get("columns", [])]
        return cls(**d)

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=1)

    @classmethod
    def load(cls, path: str) -> "ImportProfile":
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


def guess_profile(kind: str, header: list[str], sample_rows: list[dict],
                  keys: list[str]) -> ImportProfile:
    """Guess column roles as initial values. **It is a guess, and the user always confirms.**

    The rules stay simple — when a clever guess is wrong, the user cannot find why.

      · only mostly-numeric columns are candidates
      · **a numeric column with few distinct values = a design variable (input).**
        Experiments repeat a handful of levels, so design axes recycle values,
        while measurement columns differ on almost every row. This one rule
        keeps intermediate-measurement columns (raw band intensities and the
        like) from being mistaken for inputs.
      · of the remaining numeric columns, **the last one** becomes the response
        (table convention)

    ⚠ Still a guess. The screen shows the resulting condition count alongside,
    and the user confirms before proceeding.
    """
    from .importer import to_num

    LEVEL_RATIO = 0.5          # distinct/rows below this = "an axis that recycles levels"
    LEVEL_MAX = 30             # more distinct values than this is not a design axis

    values: dict[str, list[float]] = {}
    for k in keys:
        vals = [to_num(r.get(k)) for r in sample_rows]
        got = [v for v in vals if v is not None]
        if got and len(got) >= max(1, len(vals) // 2):
            values[k] = got

    n = max(1, len(sample_rows))
    design = [k for k, v in values.items()
              if len(set(v)) <= min(LEVEL_MAX, max(2, n * LEVEL_RATIO))]
    rest = [k for k in values if k not in design]
    response = rest[-1] if rest else (design.pop() if len(design) > 1 else None)

    cols: list[ColumnMap] = []
    for i, k in enumerate(keys):
        label = header[i] if i < len(header) and header[i] else k
        if k == response:
            role: Role = "response"
        elif k in design:
            role = "input"
        else:
            role = "ignore"
        vals = values.get(k, [])
        integral = bool(vals) and all(float(v).is_integer() for v in vals)
        vtype = "integer" if (role == "input" and integral) else "continuous"
        cols.append(ColumnMap(key=k, role=role, name=label, type=vtype))

    return ImportProfile(kind=kind, columns=cols)
