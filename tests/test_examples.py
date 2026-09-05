# -*- coding: utf-8 -*-
"""Shipped examples — does the passing example (synthetic annealing) pass with the real core,
and do the generator and the file agree.

The locked example's numbers are covered by test_diagnostics · test_report. This is the
other side: does the example that shows "what this tool gives" really yield a recommendation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from core.diagnostics import discriminability, gate, loocv_r2
from core.project import Project
from core.recommend import Recommendation, recommend
from core.spec import count_candidates
from ui.start_screen import example_files

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packaging"))          # 'packaging' clashes with a PyPI module name

import make_examples  # noqa: E402


@pytest.fixture(scope="module")
def success():
    return Project.load(str(example_files()[0]))


@pytest.fixture(scope="module")
def judged(success):
    ds = success.dataset()
    r2 = loocv_r2(ds.XN, ds.y_mean).r2
    d = discriminability(ds.reps)
    g = gate(count_candidates(success.inputs, success.constraint), success.budget_total,
             r2, d, ds.frac_with_reps)
    return ds, g, r2


def test_success_example_is_labelled_as_simulated(success):
    assert "simulated" in success.name.lower() and "synthetic" in Path(success.path).name
    assert all(m["note"].lower() in ("simulated", "synthetic") for m in success.measurements)


def test_success_example_passes_all_four_gates(judged):
    ds, g, r2 = judged
    assert (g.cond_count, g.learnable, g.discrim, g.replicates) == ("OK",) * 4
    assert not g.locked and g.reasons == []
    assert r2 > 0.8                                  # 0.911 when generated
    assert ds.n_conditions == 14 and ds.frac_with_reps == 1.0


def test_success_example_yields_a_recommendation_on_the_grid(success, judged):
    ds, g, _ = judged
    rec = recommend(ds, success.inputs, g, constraint=success.constraint)
    assert isinstance(rec, Recommendation) and rec.suggestions and not rec.warnings
    s = rec.suggestions[0]
    T, t = s.x_real
    assert T % 10 == 0 and t % 5 == 0 and 150 <= T <= 350 and 5 <= t <= 60
    assert not s.extrapolated
    # The simulated function's true peak (290 °C, 40 min) has not been measured yet, and the
    # model points there. Data and seed are fixed, so this is deterministic — if it changes,
    # the kernel or the candidate grid changed.
    assert s.label == "temperature 290 °C · time 40 min"


def test_generator_and_shipped_file_agree(success):
    """Re-running make_examples.py gives the same file — change the generator, regenerate the file."""
    fresh = make_examples.make()
    assert fresh.to_dict()["measurements"] == success.to_dict()["measurements"]
    assert [v.name for v in fresh.inputs] == [v.name for v in success.inputs]
    assert fresh.budget_total == success.budget_total == 60


def test_success_example_has_room_to_optimise(success):
    """252 candidates > budget 60 — a problem of choosing, not of measuring everything."""
    assert count_candidates(success.inputs, success.constraint) == 252
    assert success.used == 42 < success.budget_total
