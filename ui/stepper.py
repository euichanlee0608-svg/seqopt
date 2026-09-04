# -*- coding: utf-8 -*-
"""Progress assessment — how far you have come and what to do next (drawn by the step rail on the left).

**Why it exists**

With seven equally enabled tabs, a first-time user has no idea where to click.
They click, get an empty screen, and wonder whether the program is broken.

Borrowed from Design-Expert's left rail (linear steps, not-yet-possible ones
dimmed) and Minitab Assistant's habit of saying "what to do next" in a sentence.

**One rule** — block the steps that cannot run, but **always say why.**
A gray button with no reason is indistinguishable from a broken button.
"""
from __future__ import annotations

from dataclasses import dataclass

# Screen order and the conditions for each screen to open
SETUP, DATA, DIAG, MODEL, RECOMMEND, REPORT, HELP = range(7)

STEPS = [
    (SETUP, "Setup", "Define the variables and the objective"),
    (DATA, "Data", "Enter your measurements"),
    (DIAG, "Diagnose", "See whether this data can be used"),
    (RECOMMEND, "Recommend", "Get the next condition to measure"),
]


@dataclass
class Readiness:
    """Whether each screen can open right now — and if not, why."""

    ready: dict[int, bool]
    reason: dict[int, str]
    current: int
    next_action: str

    def blocked_reason(self, index: int) -> str:
        return "" if self.ready.get(index, True) else self.reason.get(index, "")


def assess(project, dataset, gate) -> Readiness:
    """One project state decides the availability of every screen.

    If each screen judged for itself they would disagree — the judgment lives
    in this one place only.
    """
    has_vars = bool(project.inputs)
    n_rows = sum(1 for m in project.measurements
                 if not m.get("excluded") and not m.get("pending"))
    n_cond = dataset.n_conditions if dataset is not None else 0
    unlocked = gate is not None and not gate.locked

    ready = {
        SETUP: True,
        DATA: has_vars,
        DIAG: n_cond >= 2,
        MODEL: n_cond >= 3,
        RECOMMEND: n_cond >= 2,
        REPORT: n_rows > 0,
        HELP: True,
    }
    reason = {
        DATA: "Define your input variables on the Setup tab first.",
        DIAG: "Diagnosis needs at least 2 conditions. Enter measurements on the Data tab.",
        MODEL: "Drawing the response surface needs at least 3 conditions.",
        RECOMMEND: "Recommendations become available once diagnosis has run.",
        REPORT: "A report needs at least one measurement.",
    }

    # Where the user should be right now, and what to do there
    if not has_vars:
        current, action = SETUP, "Define at least one input variable — \"+ Add variable\""
    elif n_rows == 0:
        current, action = DATA, "Enter measurements — import a file · Ctrl+V · add rows"
    elif n_cond < 2:
        current, action = DATA, "Diagnosis needs at least 2 conditions"
    elif gate is None:
        current, action = DIAG, "Diagnosing…"
    elif gate.locked:
        current, action = DIAG, "Requirements unmet — see the prescription on the Diagnose tab"
    elif not unlocked:
        current, action = DIAG, "Check the requirements"
    else:
        current, action = RECOMMEND, "Requirements met — get your next candidates"

    return Readiness(ready=ready, reason=reason, current=current, next_action=action)
