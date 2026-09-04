# -*- coding: utf-8 -*-
"""Contracts (Protocols) for the swappable parts.

Decide **what will change** first, and open only those seams.
Open everything and nothing is safe; close everything and the next
person cannot fix anything.

Will change (kept open)
  · Surrogate    — Random Forest or an NN ensemble could replace the GP
  · Acquisition  — UCB, Thompson or others could replace EI
  · Objective    — scalar maximization could grow into constraints / multi-objective

Will not change (kept closed)
  · **The gate** — refusing to optimize on data that cannot support it is
    this tool's reason to exist. The only path to a recommendation is
    `core.recommend`, and that function always passes through the gate.
    See the preamble of `core/recommend.py`.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class Surrogate(Protocol):
    """Surrogate model — tells you the value, and the uncertainty, where you have not measured.

    The core contract is that `predict` returns (mean, std) together.
    A model that cannot produce uncertainty cannot feed an acquisition
    function, so it does not qualify for this seat.
    """

    name: str
    label: str

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Surrogate":
        """Fit on normalized coordinates X(n, d) and condition means y(n,). Returns self."""
        ...

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """(mean, std). Both shape (n,)."""
        ...

    def sample(self, X: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        """Draw one function from the posterior (for Thompson sampling)."""
        ...

    def length_scales(self) -> np.ndarray | None:
        """Per-variable length scales. Feeds the sensitivity view (F-33). None if the model has none."""
        ...


@runtime_checkable
class Acquisition(Protocol):
    """Acquisition function — turns "where would the next measurement teach the most" into a score.

    `best` is always the **best measured value** (principle P3). Never pass a true value.
    """

    name: str
    label: str
    supports_continuous: bool      # if False, can only be maximized by candidate enumeration (Thompson)

    def score(self, model: Surrogate, X: np.ndarray, best: float,
              rng: np.random.Generator | None = None) -> np.ndarray:
        """Scores (n,) for candidate points X(n, d). Higher is a better candidate."""
        ...

    def describe(self) -> str:
        """One-line description for screens and reports (including parameter values)."""
        ...
