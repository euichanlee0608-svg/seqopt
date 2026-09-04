# -*- coding: utf-8 -*-
"""Project file `.seqopt` (spec §6-1 · F-06).

**Raw data goes inside the file, whole.** No references to external CSV paths —
open the project half a year later with the original moved, and no number can
be traced back (principle P4). The import profile is stored too → re-reading
the same spreadsheet never repeats the mapping.
"""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime

from .dataset import from_measurements
from .profile import ImportProfile
from .spec import Dataset, ObjSpec, VarSpec

SCHEMA = 1
EXT = ".seqopt"


@dataclass
class Project:
    name: str = "New project"
    inputs: list[VarSpec] = field(default_factory=list)
    objective: ObjSpec = field(default_factory=lambda: ObjSpec("response"))
    budget_total: int = 40
    initial_design: int = 11
    acquisition: str = "EI"
    beta: float = 2.0
    batch: int = 1

    measurements: list[dict] = field(default_factory=list)
    exclude_zero: bool = False
    excluded_conditions: list[tuple] = field(default_factory=list)
    import_profile: ImportProfile | None = None

    created: str = ""
    path: str | None = None
    diagnostics_cache: dict = field(default_factory=dict)

    # ── derived ────────────────────────────────────────────────────
    @property
    def used(self) -> int:
        """Numerator of budget progress = actual measurement count (exclusions do not count)."""
        return sum(1 for m in self.measurements
                   if not m.get("excluded") and not m.get("pending"))

    @property
    def dim(self) -> int:
        return len(self.inputs)

    def dataset(self) -> Dataset:
        return from_measurements(self.measurements, self.inputs, self.objective,
                                 exclude_zero=self.exclude_zero,
                                 exclude_conditions=self.excluded_conditions)

    def next_id(self) -> int:
        return max((m.get("id", 0) for m in self.measurements), default=0) + 1

    def add(self, inputs: list[float], value: float, note: str = "") -> dict:
        m = dict(id=self.next_id(), inputs=list(inputs), value=float(value),
                 excluded=False, note=note)
        self.measurements.append(m)
        return m

    # ── save / load ────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "name": self.name,
            "created": self.created or datetime.now().astimezone().isoformat(timespec="seconds"),
            "objective": {"name": self.objective.name, "unit": self.objective.unit,
                          "goal": self.objective.goal, "log": self.objective.log},
            "inputs": [{"name": v.name, "unit": v.unit, "type": v.type,
                        "min": v.lo, "max": v.hi, "levels": list(v.levels)}
                       for v in self.inputs],
            "budget": {"total": self.budget_total, "used": self.used,
                       "initial_design": self.initial_design},
            "acquisition": {"kind": self.acquisition, "beta": self.beta, "batch": self.batch},
            "measurements": self.measurements,
            "exclusions": {"zero": self.exclude_zero,
                           "conditions": [list(c) for c in self.excluded_conditions]},
            "import_profile": self.import_profile.to_dict() if self.import_profile else None,
            "diagnostics_cache": self.diagnostics_cache,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Project":
        if d.get("schema") != SCHEMA:
            raise ValueError(f"Unknown schema version: {d.get('schema')} (this program is {SCHEMA})")
        o = d["objective"]
        inputs = [VarSpec(name=v["name"], unit=v.get("unit", ""), type=v.get("type", "continuous"),
                          lo=v.get("min"), hi=v.get("max"), levels=tuple(v.get("levels") or ()))
                  for v in d["inputs"]]
        ex = d.get("exclusions", {})
        prof = d.get("import_profile")
        return cls(
            name=d.get("name", "New project"),
            inputs=inputs,
            objective=ObjSpec(o["name"], o.get("unit", ""), o.get("goal", "max"), o.get("log", False)),
            budget_total=d.get("budget", {}).get("total", 40),
            initial_design=d.get("budget", {}).get("initial_design", 11),
            acquisition=d.get("acquisition", {}).get("kind", "EI"),
            beta=d.get("acquisition", {}).get("beta", 2.0),
            batch=d.get("acquisition", {}).get("batch", 1),
            measurements=d.get("measurements", []),
            exclude_zero=ex.get("zero", False),
            excluded_conditions=[tuple(c) for c in ex.get("conditions", [])],
            import_profile=ImportProfile.from_dict(prof) if prof else None,
            created=d.get("created", ""),
            diagnostics_cache=d.get("diagnostics_cache", {}),
        )

    def save(self, path: str | None = None) -> str:
        """Write atomically — dying mid-save leaves the previous file intact."""
        path = path or self.path
        if not path:
            raise ValueError("No save path")
        if not self.created:
            self.created = datetime.now().astimezone().isoformat(timespec="seconds")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=1)
        if os.path.exists(path):
            shutil.copy2(path, path + ".bak")       # keep exactly one previous version
        os.replace(tmp, path)
        self.path = path
        return path

    @classmethod
    def load(cls, path: str) -> "Project":
        with open(path, encoding="utf-8") as f:
            p = cls.from_dict(json.load(f))
        p.path = path
        return p


def autosave_path(path: str | None) -> str:
    """Autosave location. A lab PC can die and the last state is still recoverable."""
    if path:
        return path + ".autosave"
    return os.path.join(os.path.expanduser("~"), ".seqopt_autosave")
