# -*- coding: utf-8 -*-
"""Tab 4, Model — response surface · uncertainty · EI · sensitivity (F-30 ~ F-36).

The screen **adapts to the dimension automatically** (§4-3). The user is never
asked "how many variables, so which figure" — the data already decided.

  1 variable    μ±2σ curve with the EI curve below
  2 variables   a 3D surface plus three heatmaps (μ · σ · EI)
  3+ variables  three 2D slices + axis pickers + sliders for the rest (default = the current best condition)

**An unlearned surface is still drawn.** Hide it and nobody can see why it is
unusable. Instead, a stamp goes on the figure, so even a screenshot pasted
into a slide carries the warning.
"""
from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFrame, QGroupBox, QHBoxLayout,
                               QLabel, QScrollArea, QSlider, QTabWidget, QVBoxLayout, QWidget)

from core.acquisition import ACQUISITIONS, make_acquisition
from core.diagnostics import sensitivity
from core.i18n import tr
from . import theme
from .widgets.section import PageHeader, tell_true_height
from core.surface import (curve_1d, format_condition, grid_2d, nearest_measured,
                          replicate_scatter, slice_defaults, to_real, trajectory)
from .widgets.advanced import Advanced
from .widgets.plots import (C_AXIS, C_BAND, C_BEST, C_MEAN, C_POINT, C_RAW, C_RESIDUAL,
                            C_SUGGEST, CMAP_EI, CMAP_MU, CMAP_SD, Canvas, apply_style,
                            mark_best, mark_suggest, scatter_points, stamp_untrusted)

GRID_N = 60
DEBOUNCE_MS = 120



class ModelTab(QWidget):
    acquisition_changed = Signal()

    def __init__(self, project, parent=None):
        super().__init__(parent)
        apply_style()
        self.project = project
        self.ds = None
        self.model = None
        self.loocv = None
        self.nugget = None
        self._sliders: list[QSlider] = []
        self._stale = True          # draw only when visible — painting a hidden tab is waste
        self._acq = None
        self._build()

        self._timer = QTimer(self, singleShot=True)
        self._timer.timeout.connect(self._draw_surface)

    # ── screen ─────────────────────────────────────────────────────
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        head = PageHeader(tr("Model — the surface drawn from the current data"),
                          tr("The terrain as the model sees it, plus the validation figures "
                             "that say how far to trust it."))
        root.addWidget(head)

        self.banner = tell_true_height(QLabel())
        self.banner.setWordWrap(True)
        self.banner.setVisible(False)
        root.addWidget(self.banner)

        bar = QHBoxLayout()
        self.readout = tell_true_height(QLabel())
        self.readout.setWordWrap(True)
        self.readout.setStyleSheet(theme.muted())
        bar.addWidget(self.readout, 1)
        root.addLayout(bar)

        # The acquisition is not chosen here — the Recommend tab is the one place.
        # Touch the same setting in two places and nobody knows which applied.
        self.method_note = QLabel()
        self.method_note.setStyleSheet(theme.faint())
        root.addWidget(self.method_note)

        self.tabs = QTabWidget()

        # ── the surface ────────────────────────────────────────────
        surf = QWidget()
        sv = QHBoxLayout(surf)
        # The panel titles are single symbols (μ · σ · EI) because a figure title
        # cannot wrap and Korean and English need different widths. What each
        # panel means is said underneath, in a label that can.
        left = QVBoxLayout()
        self.canvas = Canvas(width=8.4, height=6.0)
        left.addWidget(self.canvas, 1)
        self.surface_caption = tell_true_height(QLabel())
        self.surface_caption.setWordWrap(True)
        self.surface_caption.setStyleSheet(theme.small())
        left.addWidget(self.surface_caption)
        sv.addLayout(left, 1)

        # The slice readout names every variable twice and the sensitivity note grows
        # with the variable count — at the 660 px minimum height this column does not
        # fit, so it scrolls rather than cutting its own text off.
        side_scroll = QScrollArea()
        side_scroll.setFixedWidth(320)
        side_scroll.setWidgetResizable(True)
        side_scroll.setFrameShape(QFrame.NoFrame)
        side_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        side = QWidget()
        sd = QVBoxLayout(side)
        sd.setContentsMargins(0, 0, 6, 0)
        side_scroll.setWidget(side)

        self.cut_box = QGroupBox(tr("Slice"))
        cv = QVBoxLayout(self.cut_box)
        row = QHBoxLayout()
        self.ax_i = QComboBox()
        self.ax_j = QComboBox()
        for w in (self.ax_i, self.ax_j):
            w.currentIndexChanged.connect(self._on_axis)
        row.addWidget(QLabel("x"))
        row.addWidget(self.ax_i, 1)
        row.addWidget(QLabel("y"))
        row.addWidget(self.ax_j, 1)
        cv.addLayout(row)
        self.slider_box = QVBoxLayout()
        cv.addLayout(self.slider_box)
        self.cut_hint = tell_true_height(QLabel())
        self.cut_hint.setWordWrap(True)
        self.cut_hint.setStyleSheet(theme.muted())
        cv.addWidget(self.cut_hint)
        sd.addWidget(self.cut_box)

        gs = QGroupBox(tr("Sensitivity — which knob bites hardest"))
        gsv = QVBoxLayout(gs)
        self.sens_canvas = Canvas(width=2.6, height=2.0, dpi=100)
        # squeeze this figure and matplotlib gives up on the layout, dropping the
        # x label off the bottom edge — it keeps the height its own figure asks for
        self.sens_canvas.setMinimumHeight(self.sens_canvas.sizeHint().height())
        gsv.addWidget(self.sens_canvas)
        self.sens_note = tell_true_height(QLabel())
        self.sens_note.setWordWrap(True)
        self.sens_note.setStyleSheet(theme.muted())
        gsv.addWidget(self.sens_note)
        sd.addWidget(gs)
        sd.addStretch(1)
        sv.addWidget(side_scroll)
        self.tabs.addTab(surf, tr("Surface"))

        # ── validation figures ─────────────────────────────────────
        check = QWidget()
        cvv = QVBoxLayout(check)
        self.check_canvas = Canvas(width=9.0, height=6.4)
        cvv.addWidget(self.check_canvas, 1)
        self.check_caption = tell_true_height(QLabel(tr(
            "Top left the trajectory, top right learnability (LOOCV), bottom left the replicate "
            "scatter — how far repeats of the same condition wobble — and bottom right the terrain "
            "roughness.")))
        self.check_caption.setWordWrap(True)
        self.check_caption.setStyleSheet(theme.small())
        cvv.addWidget(self.check_caption)
        self.tabs.addTab(check, tr("Validation"))

        root.addWidget(self.tabs, 1)

    # ── data injection ─────────────────────────────────────────────
    def set_model(self, ds, model, nugget) -> None:
        first = self.ds is None or (ds is not None and
                                    ds.XN.shape[1] != self.ds.XN.shape[1])
        self.ds = ds
        self.model = model
        self.nugget = nugget
        if first:
            self._rebuild_controls()
        self.redraw()

    def refresh_labels(self) -> None:
        """Rebuild the axis pickers and sliders after variable names/count change."""
        names = [v.name for v in self.project.inputs]
        if [self.ax_i.itemText(i) for i in range(self.ax_i.count())] != names:
            self._rebuild_controls()
        if self.ds is not None:
            self.redraw()

    def set_loocv(self, loocv) -> None:
        """R² arrives **later** than the surface (it runs in the background).

        When it lands, the surface is redrawn — otherwise the "unlearned" stamp
        never appears. A banner with a clean-looking figure underneath is the
        most dangerous state this screen has.
        """
        self.loocv = loocv
        self._update_banner()
        self._draw_surface()
        self._draw_checks()

    # ── slice controls ─────────────────────────────────────────────
    def _rebuild_controls(self) -> None:
        names = [v.name for v in self.project.inputs]
        d = len(names)
        for cb in (self.ax_i, self.ax_j):
            cb.blockSignals(True)
            cb.clear()
            cb.addItems(names)
            cb.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            cb.view().setMinimumWidth(220)         # the dropdown opens wide enough for full names
            cb.blockSignals(False)
        for cb in (self.ax_i, self.ax_j):
            cb.setToolTip(cb.currentText())
        if d > 1:
            self.ax_j.setCurrentIndex(self._default_axes(d)[1])
        self.ax_i.setCurrentIndex(self._default_axes(d)[0])
        self.cut_box.setVisible(d >= 3)

        while self.slider_box.count():
            item = self.slider_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._sliders = []
        if d < 3 or self.ds is None:
            return

        base = slice_defaults(self.ds)
        for k, v in enumerate(self.project.inputs):
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)
            lab = QLabel(v.name)
            lab.setFixedWidth(104)
            lab.setToolTip(v.name)                 # long names clip; the tooltip keeps the whole
            s = QSlider(Qt.Horizontal, minimum=0, maximum=1000)
            s.setValue(int(base[k] * 1000))
            s.valueChanged.connect(self._on_slider)
            val = QLabel()
            val.setFixedWidth(56)
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            h.addWidget(lab)
            h.addWidget(s, 1)
            h.addWidget(val)
            s._label = val                     # noqa: SLF001
            s._axis = k                        # noqa: SLF001
            self._sliders.append(s)
            self.slider_box.addWidget(row)
        self._sync_slider_state()

    def _default_axes(self, d: int) -> tuple[int, int]:
        """Default slice axes = **the two most sensitive ones**.

        With five variables, choosing which two to look at is work in itself.
        Never ask the user what the model already knows — the axes with the
        shortest (= most sensitive) length scales become the default.
        """
        if d < 2:
            return 0, 0
        if self.model is not None:
            ls = self.model.length_scales()
            if ls is not None and len(ls) == d:
                order = list(np.argsort(ls))            # shorter = more sensitive
                return int(order[0]), int(order[1])
        return 0, 1

    def _sync_slider_state(self) -> None:
        i, j = self.ax_i.currentIndex(), self.ax_j.currentIndex()
        lo, span = self.ds.X.min(0), np.ptp(self.ds.X, axis=0)
        for s in self._sliders:
            k = s._axis                        # noqa: SLF001
            frozen = k not in (i, j)
            s.parentWidget().setVisible(frozen)
            real = lo[k] + s.value() / 1000 * span[k]
            v = self.project.inputs[k]
            s._label.setText(f"{real:.0f}" if v.type == "integer" else f"{real:.3g}")  # noqa: SLF001

    def _fixed_vector(self) -> np.ndarray | None:
        if not self._sliders:
            return None
        x = slice_defaults(self.ds)
        for s in self._sliders:
            x[s._axis] = s.value() / 1000      # noqa: SLF001
        return x

    def _on_slider(self) -> None:
        self._sync_slider_state()
        self._timer.start(DEBOUNCE_MS)

    def _on_axis(self) -> None:
        for cb in (self.ax_i, self.ax_j):
            cb.setToolTip(cb.currentText())
        if self.ax_i.currentIndex() == self.ax_j.currentIndex() and self.ax_j.count() > 1:
            self.ax_j.blockSignals(True)
            self.ax_j.setCurrentIndex((self.ax_i.currentIndex() + 1) % self.ax_j.count())
            self.ax_j.blockSignals(False)
        if self._sliders:
            self._sync_slider_state()
        self.redraw()

    def set_acquisition(self, acq) -> None:
        """Receives the method chosen on the Recommend tab and reflects it in the figures."""
        self._acq = acq
        self.method_note.setText(tr("Next-candidate method: {method}  (change it on the Recommend tab)",
                                    method=acq.describe()))
        self.redraw()

    def acquisition(self):
        return getattr(self, "_acq", None) or make_acquisition()

    # ── drawing ────────────────────────────────────────────────────
    def redraw(self) -> None:
        """When not visible, only mark stale — never actually draw.

        Repainting hidden tabs on every edited value (surface 156ms · checks
        107ms) slows typing by exactly that much. Draw once, when the tab opens.
        """
        self._update_banner()
        if not self.isVisible():
            self._stale = True
            return
        self._stale = False
        self._draw_surface()
        self._draw_sensitivity()
        self._draw_checks()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._stale and self.ds is not None:
            self.redraw()

    def _update_banner(self) -> None:
        if self.loocv is None or self.loocv.r2 > 0:
            self.banner.setVisible(False)
            return
        self.banner.setVisible(True)
        self.banner.setText(tr(
            "⚠ This surface is <b>unlearned</b> (LOOCV R² = {r2} ≤ 0). Its shape comes from the "
            "kernel's default assumptions more than from the data. "
            "<b>Do not draw conclusions from the shape.</b>", r2=f"{self.loocv.r2:+.3f}"))
        self.banner.setStyleSheet(theme.card("fail"))

    def _best(self) -> float:
        return float(np.max([v.max() for v in self.ds.reps]))

    def _draw_surface(self) -> None:
        fig = self.canvas.clear()
        if self.ds is None or self.model is None:
            self.surface_caption.setText("")
            fig.text(0.5, 0.5, tr("The surface is drawn once there are at least 3 conditions."),
                     ha="center", va="center", color="#888")           # i18n: skip
            self.canvas.draw_idle()
            return

        d = self.ds.XN.shape[1]
        acq = self.acquisition()
        kind = acq.describe().split()[0]
        best = self._best()
        obj = self.project.objective          # the spec, not its name — the figures undo the sign

        if d == 1:
            self._plot_1d(fig, best, acq, kind, obj)
        else:
            self._plot_nd(fig, best, acq, kind, obj, d)

        if self.loocv is not None and self.loocv.r2 <= 0:
            stamp_untrusted(fig, tr("UNLEARNED  R² < 0"))
        self.canvas.draw_idle()

    def _plot_1d(self, fig, best, acq, kind, obj) -> None:
        self.surface_caption.setText("")
        c = curve_1d(self.model, self.ds, best, acq)
        ax1, ax2 = fig.subplots(2, 1, height_ratios=[2.2, 1], sharex=True)

        # everything on this axis is drawn in plot space: the sign is undone, the
        # log stays (the band is symmetric only there) and the label says so
        mu = obj.to_plot(c.mu)
        ax1.fill_between(c.x_real, mu - 2 * c.sd, mu + 2 * c.sd,
                         color=C_BAND, alpha=0.45, lw=0, label="μ ± 2σ")
        ax1.plot(c.x_real, mu, color=C_MEAN, lw=2, label=tr("predicted mean μ"))
        for x, v in zip(self.ds.X[:, 0], self.ds.reps):
            ax1.scatter([x] * len(v), obj.to_plot(v), s=26, c=C_POINT, edgecolors="white",
                        linewidths=0.6, zorder=5)
        bi = int(np.argmax(self.ds.y_mean))
        mark_best(ax1, self.ds.X[bi, 0], obj.to_plot(self.ds.y_mean[bi]))
        ax1.set_ylabel(obj.plot_label())
        ax1.set_title(tr("Response surface — measured points and the uncertainty around them"))
        ax1.legend(loc="best", ncols=2)

        ax2.fill_between(c.x_real, 0, c.ei, color=C_SUGGEST, alpha=0.3, lw=0)
        ax2.plot(c.x_real, c.ei, color=C_SUGGEST, lw=1.6)
        ax2.axvline(c.x_best_ei, color=C_SUGGEST, ls="--", lw=1)
        ax2.set_ylabel(kind)
        ax2.set_xlabel(self._axis_label(0))
        ax2.set_title(tr("{kind} — where the next measurement teaches the most", kind=kind))
        self._say_readout(kind, float(c.ei.max()), f"{self._axis_label(0)} = {c.x_best_ei:g}")

    def _plot_nd(self, fig, best, acq, kind, obj, d) -> None:
        i = self.ax_i.currentIndex()
        j = self.ax_j.currentIndex() if d > 1 else 0
        g = grid_2d(self.model, self.ds, best, acq, i, j, self._fixed_vector(), n=GRID_N)
        extent = [g.x_real[0], g.x_real[-1], g.y_real[0], g.y_real[-1]]

        if d == 2:
            gs = fig.add_gridspec(2, 2)
            ax3d = fig.add_subplot(gs[0, 0], projection="3d")
            self._plot_3d(ax3d, g, obj)
            axes = [fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 0]),
                    fig.add_subplot(gs[1, 1])]
        else:
            # A 1×3 row makes each panel narrow and tall — the terrain vanishes.
            # μ, the panel people stare at longest, goes wide on top; σ and EI sit below.
            gs = fig.add_gridspec(2, 2)
            axes = [fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, 0]),
                    fig.add_subplot(gs[1, 1])]

        # a title cannot wrap and these panels are ~100 px wide: the symbol names
        # the panel, the caption under the figure carries the sentence
        panels = [("μ", obj.to_plot(g.mu), CMAP_MU, obj.plot_label()),
                  ("σ", g.sd, CMAP_SD, None), (kind, g.ei, CMAP_EI, None)]
        caption = [tr("μ predicted mean · σ uncertainty, darker is less known · "
                      "{kind} where to measure next", kind=kind)]
        if d == 2:
            caption.insert(0, tr("Top left: the 3D surface with residual drop lines."))
        self.surface_caption.setText(" ".join(caption))
        on_slice = self._points_on_slice(i, j)

        for ax, (title, Z, cmap, bar_label) in zip(axes, panels):
            im = ax.imshow(Z, origin="lower", extent=extent, aspect="auto", cmap=cmap)
            bar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
            if bar_label:                       # only μ carries the response's own name
                bar.set_label(bar_label, fontsize=7)
            if len(on_slice):
                ax.scatter(self.ds.X[on_slice, i], self.ds.X[on_slice, j], s=22,
                           c=C_POINT, edgecolors="white", linewidths=0.6, zorder=5)
            ax.set_title(title)
            ax.set_xlabel(self._axis_label(i))
            ax.set_ylabel(self._axis_label(j))
            ax.grid(False)

        bi = int(np.argmax(self.ds.y_mean))
        axes[0].scatter([self.ds.X[bi, i]], [self.ds.X[bi, j]], s=150, marker="*",
                        c=C_BEST, edgecolors="white", linewidths=1.0, zorder=7)
        k = int(np.unravel_index(np.argmax(g.ei), g.ei.shape)[::-1][0])
        ky, kx = np.unravel_index(np.argmax(g.ei), g.ei.shape)
        axes[2].scatter([g.x_real[kx]], [g.y_real[ky]], s=90, marker="D",
                        c=C_SUGGEST, edgecolors="white", linewidths=1.0, zorder=7)

        self._say_readout(kind, float(g.ei.max()),
                          f"{self._axis_label(i)} {g.x_real[kx]:g} · "
                          f"{self._axis_label(j)} {g.y_real[ky]:g}")
        self._update_cut_hint(g)

    def _plot_3d(self, ax, g, obj) -> None:
        X, Y = np.meshgrid(g.x_real, g.y_real)
        ax.plot_surface(X, Y, obj.to_plot(g.mu), cmap=CMAP_MU, alpha=0.85, linewidth=0,
                        antialiased=True, rstride=2, cstride=2)
        i, j = g.axis_i, g.axis_j
        y_mean = obj.to_plot(self.ds.y_mean)
        ax.scatter(self.ds.X[:, i], self.ds.X[:, j], y_mean,
                   s=18, c=C_POINT, depthshade=False)
        # residual drop lines — how far each measured point sits off the surface (F-31)
        pred, _ = self.model.predict(self.ds.XN)
        for a, b, y, p in zip(self.ds.X[:, i], self.ds.X[:, j], y_mean, obj.to_plot(pred)):
            ax.plot([a, a], [b, b], [y, p], color=C_RESIDUAL, lw=0.7)
        ax.set_xlabel(self._axis_label(i), labelpad=-4)
        ax.set_ylabel(self._axis_label(j), labelpad=-4)
        # no title: constrained layout does not lay out a 3D axes, so a title here
        # lands outside the figure. The caption under the figure names this panel.
        ax.tick_params(labelsize=6)

    def _points_on_slice(self, i: int, j: int, tol: float = 0.08) -> np.ndarray:
        """Overlay only the measured points near the slice — points far away would be a lie."""
        fixed = self._fixed_vector()
        if fixed is None:
            return np.arange(len(self.ds.XN))
        others = [k for k in range(self.ds.XN.shape[1]) if k not in (i, j)]
        if not others:
            return np.arange(len(self.ds.XN))
        dist = np.abs(self.ds.XN[:, others] - fixed[others]).max(axis=1)
        return np.where(dist <= tol)[0]

    def _update_cut_hint(self, g) -> None:
        if not self._sliders:
            self.cut_hint.setText("")
            return
        real = to_real(g.fixed, self.ds.X)
        near = nearest_measured(self.ds, g.fixed)
        n_on = len(self._points_on_slice(g.axis_i, g.axis_j))
        self.cut_hint.setText(tr(
            "pinned at: {where}<br>{n} measured points near this slice · "
            "closest measured condition: {nearest}",
            where=format_condition(real, self.project.inputs), n=n_on,
            nearest=format_condition(self.ds.X[near], self.project.inputs)))

    def _say_readout(self, kind: str, ei_max: float, where: str) -> None:
        """When the acquisition value is effectively zero, say so.

        A tiny `1e-8` on a colorbar goes unseen by everyone. Yet it means "the
        next measurement teaches nothing" — the most important fact on the map.
        The yardstick matches the stopping rule (F-24): 1% of the response range.
        """
        rng = float(np.ptp(self.ds.y_mean)) if self.ds is not None else 0.0
        if rng > 0 and ei_max < 0.01 * rng:
            self.readout.setText(tr(
                "<span style='color:{c}'>{kind} max: {where} · value {value} = {pct}% of the "
                "response range — there is almost nothing left to learn anywhere</span>",
                c=theme.FAIL, kind=kind, where=where,
                value=f"{ei_max:.2g}", pct=f"{ei_max / rng * 100:.3f}"))
        else:
            self.readout.setText(tr("{kind} max: {where} · value {value}",
                                    kind=kind, where=where, value=f"{ei_max:.3g}"))

    def _axis_label(self, k: int) -> str:
        v = self.project.inputs[k]
        return f"{v.name} ({v.unit})" if v.unit else v.name

    # ── sensitivity ────────────────────────────────────────────────
    def _draw_sensitivity(self) -> None:
        fig = self.sens_canvas.clear()
        ax = fig.add_subplot(111)
        if self.model is None:
            ax.axis("off")
            self.sens_canvas.draw_idle()
            return
        names = [v.name for v in self.project.inputs]
        pairs = sensitivity(self.model, names)
        if not pairs:
            ax.axis("off")
            self.sens_canvas.draw_idle()
            self.sens_note.setText(tr("This surrogate has no length scales, so sensitivity cannot be computed."))
            return
        labels = [n for n, _ in pairs]
        vals = [p for _, p in pairs]
        y = np.arange(len(labels))
        ax.barh(y, vals, color=C_MEAN, height=0.55)
        ax.set_yticks(y, labels)
        ax.invert_yaxis()
        ax.set_xlabel(tr("influence [%]"))
        ax.set_xlim(0, max(100, max(vals) * 1.15) if vals else 100)
        for k, v in enumerate(vals):
            ax.text(v + 1.5, k, f"{v:.0f}", va="center", fontsize=7, color=C_AXIS)   # i18n: skip
        ax.grid(axis="y", visible=False)
        self.sens_canvas.draw_idle()

        zero = [n for n, p in pairs if p == 0.0]
        note = tr("A <b>longer bar is more sensitive</b> (1 / length scale).")
        if zero:
            note += " " + tr("No influence was detected for '{names}'.", names=", ".join(zero))
        self.sens_note.setText(note)

    # ── validation figures ─────────────────────────────────────────
    def _draw_checks(self) -> None:
        fig = self.check_canvas.clear()
        if self.ds is None:
            self.check_canvas.draw_idle()
            return
        axes = fig.subplots(2, 2).ravel()
        self._plot_trajectory(axes[0])
        self._plot_loocv(axes[1])
        self._plot_replicates(axes[2])
        self._plot_variogram(axes[3])
        self.check_canvas.draw_idle()

    def _plot_trajectory(self, ax) -> None:
        n, run = trajectory(self.project.measurements, self.project.objective)
        if len(n) == 0:
            ax.axis("off")
            return
        ax.step(n, run, where="post", color=C_MEAN, lw=1.8)
        ax.scatter(n, run, s=12, c=C_MEAN, zorder=4)
        ax.set_xlabel(tr("measurements (cumulative)"))
        ax.set_ylabel(self.project.objective.plot_label(stacked=True))
        ax.set_title(tr("Trajectory — best measured value so far"))

    def _plot_loocv(self, ax) -> None:
        if self.loocv is None:
            ax.text(0.5, 0.5, tr("Computing learnability…"),
                    ha="center", va="center", color="#888")            # i18n: skip
            ax.axis("off")
            return
        obj = self.project.objective
        y = obj.to_plot(self.ds.y_mean)
        p = obj.to_plot(self.loocv.pred)
        ax.scatter(y, p, s=30, c=C_POINT, edgecolors="white", linewidths=0.6, zorder=5)
        lim = [min(y.min(), p.min()), max(y.max(), p.max())]
        ax.plot(lim, lim, color=C_AXIS, lw=1, label=tr("perfect prediction"))
        ax.axhline(y.mean(), color=C_BEST, ls="--", lw=1.2, label=tr("always answer the mean"))
        ax.set_xlabel(tr("measured (condition mean)"))
        ax.set_ylabel(tr("LOOCV prediction"))
        ax.set_title(tr("Learnability R² = {r2}", r2=f"{self.loocv.r2:+.3f}"))
        ax.legend(loc="best")

    def _plot_replicates(self, ax) -> None:
        obj = self.project.objective
        order, reps, means = replicate_scatter(self.ds)
        for k, v in enumerate(reps):
            ax.scatter([k] * len(v), obj.to_plot(v), s=22, c=C_RAW, zorder=3)
        ax.plot(range(len(means)), obj.to_plot(means), color=C_MEAN, lw=1.4, zorder=4,
                label=tr("condition mean"))
        ax.set_xlabel(tr("condition (sorted by mean)"))
        ax.set_ylabel(obj.plot_label(stacked=True))
        ax.set_title(tr("Replicate scatter"))       # the sentence is in the caption below
        ax.legend(loc="best")

    def _plot_variogram(self, ax) -> None:
        n = self.nugget
        if n is None:
            ax.axis("off")
            return
        ax.plot(n.bin_centers, n.bin_gamma, "o-", color=C_MEAN, ms=4, lw=1.4)
        ax.axhline(n.sill, color=C_AXIS, ls="--", lw=1, label=tr("sill {v}", v=f"{n.sill:.2f}"))
        ax.axhline(n.nugget, color=C_BEST, ls=":", lw=1.2, label=tr("nugget {v}", v=f"{n.nugget:.2f}"))
        ax.set_xlabel(tr("distance between conditions (normalized)"))
        ax.set_ylabel(tr("semivariance γ"))
        ax.set_title(tr("Terrain roughness — nugget ratio {ratio}", ratio=f"{n.ratio:.3f}"))
        ax.legend(loc="best")
