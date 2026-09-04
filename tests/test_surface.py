# -*- coding: utf-8 -*-
"""M3 — the visualization math and the screen transitions (F-30 ~ F-36).

No pixel checks. What gets checked is **what the program decided to draw** —
how many axes, where the slice sits, whether the warning is attached.
"""
from __future__ import annotations

import numpy as np
import pytest

from core.acquisition import ExpectedImprovement
from core.dataset import build
from core.diagnostics import loocv_r2
from core.spec import ObjSpec, VarSpec
from core.surface import (curve_1d, format_condition, grid_2d, nearest_measured,
                          replicate_scatter, slice_defaults, to_real, trajectory)
from core.surrogate import fit
from tests.loaders import external, synthetic


@pytest.fixture(scope="module")
def syn():
    return synthetic()


@pytest.fixture(scope="module")
def syn_model(syn):
    return fit(syn.XN, syn.y_mean)


def _ds_1d():
    groups = {(float(x),): [float(np.sin(x) + 1.5), float(np.sin(x) + 1.52)]
              for x in np.linspace(0, 6, 9)}
    return build(groups, [VarSpec("x", "", "continuous", 0, 6)], ObjSpec("y"))


# ══════════════════════════════════════════════════════════════════════
# coordinate transforms
# ══════════════════════════════════════════════════════════════════════
def test_to_real_inverts_normalisation(syn):
    """Undoing the normalization returns the original conditions — false axis ticks make everything false."""
    back = to_real(syn.XN, syn.X)
    assert np.allclose(back, syn.X)


def test_format_condition_respects_type(syn):
    txt = format_condition(syn.X[0], syn.inputs)
    assert "power" in txt and "W" in txt
    assert "dwell" in txt and "s" in txt
    # integers get no decimal point
    assert ".0" not in txt.split("dwell")[1]


# ══════════════════════════════════════════════════════════════════════
# one variable (F-30)
# ══════════════════════════════════════════════════════════════════════
def test_curve_1d_shapes_and_band():
    ds = _ds_1d()
    m = fit(ds.XN, ds.y_mean)
    best = float(max(v.max() for v in ds.reps))
    c = curve_1d(m, ds, best, ExpectedImprovement(), n=120)
    assert c.mu.shape == c.sd.shape == c.ei.shape == (120,)
    assert (c.sd >= 0).all()
    assert (c.ei >= -1e-12).all()
    assert ds.X[:, 0].min() <= c.x_best_ei <= ds.X[:, 0].max()
    assert c.x_real[0] == pytest.approx(ds.X[:, 0].min())
    assert c.x_real[-1] == pytest.approx(ds.X[:, 0].max())


# ══════════════════════════════════════════════════════════════════════
# slices (F-31 · F-32)
# ══════════════════════════════════════════════════════════════════════
def test_grid_2d_defaults_to_current_best(syn, syn_model):
    """The default slice position is **the current best condition** (§4-3). Slice anywhere else and the terrain is false."""
    best = float(max(v.max() for v in syn.reps))
    g = grid_2d(syn_model, syn, best, ExpectedImprovement(), 0, 1, None, n=20)
    assert np.allclose(g.fixed, slice_defaults(syn))
    bi = int(np.argmax(syn.y_mean))
    assert np.allclose(g.fixed, syn.XN[bi])


def test_grid_2d_axes_are_in_real_units(syn, syn_model):
    best = float(max(v.max() for v in syn.reps))
    g = grid_2d(syn_model, syn, best, ExpectedImprovement(), 0, 1, None, n=25)
    assert g.mu.shape == g.sd.shape == g.ei.shape == (25, 25)
    assert g.x_real[0] == pytest.approx(syn.X[:, 0].min())
    assert g.x_real[-1] == pytest.approx(syn.X[:, 0].max())
    assert g.y_real[0] == pytest.approx(syn.X[:, 1].min())
    assert g.y_real[-1] == pytest.approx(syn.X[:, 1].max())


def test_slice_position_changes_the_surface():
    """Moving the pinned values must actually change the slice (what the sliders do)."""
    ds = external("p3ht")
    m = fit(ds.XN, ds.y_mean)
    best = float(max(v.max() for v in ds.reps))
    a = grid_2d(m, ds, best, ExpectedImprovement(), 0, 1, slice_defaults(ds), n=15)
    far = slice_defaults(ds).copy()
    far[2] = 1.0 - far[2]
    b = grid_2d(m, ds, best, ExpectedImprovement(), 0, 1, far, n=15)
    assert not np.allclose(a.mu, b.mu)


def test_nearest_measured_finds_the_point_itself(syn):
    for i in (0, 5, 14):
        assert nearest_measured(syn, syn.XN[i]) == i


# ══════════════════════════════════════════════════════════════════════
# trajectory · replicate scatter (F-34 · F-36)
# ══════════════════════════════════════════════════════════════════════
def test_trajectory_is_running_best_of_measured_values():
    """Measured values, never true ones (principle P3)."""
    obj = ObjSpec("y", goal="max")
    ms = [dict(inputs=[0], value=v, excluded=False) for v in (1.0, 0.5, 1.4, 1.2, 2.0)]
    n, run = trajectory(ms, obj)
    assert list(n) == [1, 2, 3, 4, 5]
    assert list(run) == [1.0, 1.0, 1.4, 1.4, 2.0]
    assert all(run[i] <= run[i + 1] for i in range(len(run) - 1))


def test_trajectory_skips_excluded_rows():
    obj = ObjSpec("y", goal="max")
    ms = [dict(inputs=[0], value=1.0, excluded=False),
          dict(inputs=[0], value=9.0, excluded=True),
          dict(inputs=[0], value=1.2, excluded=False)]
    _, run = trajectory(ms, obj)
    assert list(run) == [1.0, 1.2]          # the excluded 9.0 must never surface as the best


def test_trajectory_follows_minimisation_goal():
    """A minimization goal flips the internal sign, so "smaller is better" shows in the trajectory."""
    obj = ObjSpec("loss", goal="min")
    ms = [dict(inputs=[0], value=v, excluded=False) for v in (5.0, 3.0, 4.0, 1.0)]
    _, run = trajectory(ms, obj)
    assert list(run) == [-5.0, -3.0, -3.0, -1.0]


def test_replicate_scatter_is_sorted_by_condition_mean(syn):
    order, reps, means = replicate_scatter(syn)
    assert list(means) == sorted(means)
    assert len(reps) == syn.n_conditions
    assert len(reps[0]) == len(syn.reps[order[0]])


# ══════════════════════════════════════════════════════════════════════
# screen transitions — automatic per dimension (§4-3)
# ══════════════════════════════════════════════════════════════════════
def shown(w) -> bool:
    """In tests with no shown window, isVisible() is always False.

    The question is "did the program hide this widget", so isHidden() is the check.
    """
    return not w.isHidden()


def _model_tab(qapp, ds, project):
    """Put the tab into an actually-shown state.

    The Model tab draws **only when visible** (painting hidden tabs slows
    typing). Built without show(), an empty figure is correct — so showing it
    is a precondition of the check.
    """
    from ui.tab_model import ModelTab
    tab = ModelTab(project)
    tab.show()
    qapp.processEvents()
    tab.set_model(ds, fit(ds.XN, ds.y_mean), None)
    qapp.processEvents()
    return tab


def test_hidden_tab_is_not_drawn(qapp, syn):
    """Repainting a hidden tab slows typing by exactly that much.

    One of the causes behind the measured 972ms per edited cell.
    """
    from core.project import Project
    from ui.tab_model import ModelTab

    p = Project(inputs=[VarSpec("power", "W", "continuous", 150, 190),
                        VarSpec("dwell", "s", "integer", 3, 7)],
                objective=ObjSpec("G/D"))
    tab = ModelTab(p)                       # no show()
    tab.set_model(syn, fit(syn.XN, syn.y_mean), None)
    assert tab.canvas.fig.axes == [], "a hidden tab was drawn"
    assert tab._stale, "it must be marked for drawing later"

    tab.show()
    qapp.processEvents()
    assert tab.canvas.fig.axes, "showing it must draw it"


def test_one_variable_draws_curve_and_ei(qapp):
    from core.project import Project
    ds = _ds_1d()
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 6)], objective=ObjSpec("y"))
    tab = _model_tab(qapp, ds, p)
    assert len(tab.canvas.fig.axes) == 2          # μ±2σ on top · EI below
    assert not shown(tab.cut_box)                  # no slice controls needed
    assert tab._sliders == []


def test_two_variables_draw_3d_and_three_maps(qapp, syn):
    from core.project import Project
    p = Project(inputs=[VarSpec("power", "W", "continuous", 150, 190),
                        VarSpec("dwell", "s", "integer", 3, 7)],
                objective=ObjSpec("G/D"))
    tab = _model_tab(qapp, syn, p)
    axes = tab.canvas.fig.axes
    assert any(getattr(a, "name", "") == "3d" for a in axes), "the 3D surface must exist"
    assert len([a for a in axes if getattr(a, "name", "") != "3d"]) >= 3   # μ·σ·EI (+colorbars)
    assert not shown(tab.cut_box)


def test_five_variables_make_sliders_for_frozen_axes(qapp):
    from core.project import Project
    ds = external("p3ht")
    p = Project(inputs=[VarSpec(f"x{i}", "", "continuous",
                                float(ds.X[:, i].min()), float(ds.X[:, i].max()))
                        for i in range(ds.X.shape[1])],
                objective=ObjSpec("y"))
    tab = _model_tab(qapp, ds, p)
    assert shown(tab.cut_box)
    assert len(tab._sliders) == 5
    # the two slice axes hide their sliders; only the other three show
    visible = [s for s in tab._sliders if shown(s.parentWidget())]
    assert len(visible) == 3
    assert np.allclose(tab._fixed_vector(), slice_defaults(ds), atol=1e-3)


def test_default_cut_axes_are_the_two_most_sensitive(qapp):
    """With five variables, choosing which two to look at is work in itself.

    Never ask the user what the model already knows (the length scales) —
    the two most sensitive axes open by default.
    """
    from core.project import Project
    ds = external("p3ht")
    p = Project(inputs=[VarSpec(f"x{i}", "", "continuous",
                                float(ds.X[:, i].min()), float(ds.X[:, i].max()))
                        for i in range(ds.X.shape[1])],
                objective=ObjSpec("y"))
    tab = _model_tab(qapp, ds, p)
    ls = tab.model.length_scales()
    expected = sorted(range(len(ls)), key=lambda k: ls[k])[:2]
    assert {tab.ax_i.currentIndex(), tab.ax_j.currentIndex()} == set(expected)


def test_changing_cut_axis_hides_that_slider(qapp):
    from core.project import Project
    ds = external("p3ht")
    p = Project(inputs=[VarSpec(f"x{i}", "", "continuous",
                                float(ds.X[:, i].min()), float(ds.X[:, i].max()))
                        for i in range(ds.X.shape[1])],
                objective=ObjSpec("y"))
    tab = _model_tab(qapp, ds, p)
    tab.ax_i.setCurrentIndex(0)
    tab.ax_j.setCurrentIndex(4)                   # x-axis x0 · y-axis x4
    frozen = {s._axis for s in tab._sliders if shown(s.parentWidget())}
    assert frozen == {1, 2, 3}, "only the two slice axes may hide their sliders"


# ══════════════════════════════════════════════════════════════════════
# the unlearned surface — stamped, not hidden
# ══════════════════════════════════════════════════════════════════════
def _figure_texts(fig) -> str:
    out = [t.get_text() for t in fig.texts]
    for ax in fig.axes:
        out += [t.get_text() for t in ax.texts]
    return " ".join(out)


def test_untrusted_surface_gets_stamped_when_r2_arrives(qapp, syn):
    """R² arrives after the surface. When it lands, the tab must **redraw** and stamp.

    (A bug once missed — the banner showed while the figure still looked fine.)
    """
    from core.project import Project
    p = Project(inputs=[VarSpec("power", "W", "continuous", 150, 190),
                        VarSpec("dwell", "s", "integer", 3, 7)],
                objective=ObjSpec("G/D"))
    tab = _model_tab(qapp, syn, p)
    assert "UNLEARNED" not in _figure_texts(tab.canvas.fig)     # R² still unknown
    assert not shown(tab.banner)

    tab.set_loocv(loocv_r2(syn.XN, syn.y_mean))                 # R² < 0 by design
    assert shown(tab.banner)
    assert "UNLEARNED" in _figure_texts(tab.canvas.fig)


def test_learnable_surface_is_not_stamped(qapp):
    """p3ht is learnable (R² > 0). Warnings on healthy figures dull the warning."""
    from core.project import Project
    ds = external("p3ht")
    p = Project(inputs=[VarSpec(f"x{i}", "", "continuous",
                                float(ds.X[:, i].min()), float(ds.X[:, i].max()))
                        for i in range(ds.X.shape[1])],
                objective=ObjSpec("y"))
    tab = _model_tab(qapp, ds, p)

    class _R:
        r2, low_sample_warning = 0.58, False
        pred = ds.y_mean
    tab.set_loocv(_R())
    assert not shown(tab.banner)
    assert "UNLEARNED" not in _figure_texts(tab.canvas.fig)


def test_negligible_ei_is_called_out(qapp, syn):
    """A near-zero EI hides in a colorbar's tiny `1e-8` — the screen must say it in a sentence."""
    from core.project import Project
    p = Project(inputs=[VarSpec("power", "W", "continuous", 150, 190),
                        VarSpec("dwell", "s", "integer", 3, 7)],
                objective=ObjSpec("G/D"))
    tab = _model_tab(qapp, syn, p)
    assert "nothing left to learn" in tab.readout.text()


# ══════════════════════════════════════════════════════════════════════
# sensitivity direction (F-33) — the screen shows 'bigger = more sensitive'
# ══════════════════════════════════════════════════════════════════════

