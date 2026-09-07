# -*- coding: utf-8 -*-
"""Tab 5, Recommend — next candidates · batch · instruction sheet (F-20 ~ F-25 · F-42).

This screen **only displays** what `core.recommend.recommend()` returned.
All judgment ends in the core — if a screen could lift the lock or pick
conditions itself, this project's original mistake ("running optimization on
data that cannot support it") would move inside the tool.

Receive `Locked` and the suggestions **are simply not in the object.**
Nothing to take out by mistake.

**Why the first suggestion is a card and the rest a table**

One table of everything put five variables × four-decimal values side by side,
and at 1024 px the row ran off the screen — the one thing the user has to copy
onto the instrument was the thing that got cut. The suggestion to act on is now
a card (one line per variable, the value large and right-aligned), and the
runners-up stay a table, which may elide because nobody types from it.
Values are shown at the precision the variable declares (`core.surface.decimals`),
never as `89.0915 %`.
"""
from __future__ import annotations

import csv

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox,
                               QFileDialog, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
                               QLabel, QMessageBox, QPushButton, QScrollArea, QSpinBox,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from core.acquisition import ACQUISITIONS, make_acquisition
from core.i18n import tr
from core.recommend import Locked, Recommendation, RecommendResult, recommend
from core.surface import fmt_value
from . import theme
from .widgets.advanced import Advanced
from .widgets.section import PageHeader, Section, link_button, wrapping

MAX_BATCH = 10



class _AltTable(QTableWidget):
    """The runners-up table. It re-fits its columns whenever its viewport changes size.

    A vertical scroll bar appearing narrows the viewport without resizing the
    table, so the viewport — not the table — is what has to be watched.
    """

    def __init__(self, fit, parent=None):
        super().__init__(0, 0, parent)
        self._fit = fit
        self.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.viewport() and event.type() == QEvent.Resize:
            self._fit()
        return super().eventFilter(obj, event)


class RecommendTab(QWidget):
    """Shows recommendations; accepting them inserts gray rows into the data table."""

    points_accepted = Signal(list)          # [(inputs, note), ...]
    help_requested = Signal(str)
    acquisition_changed = Signal()          # the one and only place where it is chosen
    override_changed = Signal(bool)         # forced run → leaves its mark on the report

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.dataset = None
        self.gate = None
        self.model = None
        self.result: RecommendResult | None = None
        self.acq_history: list[float] = []
        self._card_rows: list[tuple[QLabel, QLabel]] = []
        self._alt_headers: list[tuple[str, str]] = []       # (header text, tooltip)
        self._fitting = False
        self._build()

    # ── screen ─────────────────────────────────────────────────────
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        head = PageHeader(tr("Recommend — the next condition to measure"),
                          tr("Opens only after the diagnostic requirements pass. A recommendation "
                             "comes as condition values, a suggested replicate count, and its evidence."))
        why = link_button(tr("It is locked — can I not just use it anyway?"))
        why.clicked.connect(lambda: self.help_requested.emit("locked"))
        head.add_right(why)
        root.addWidget(head)

        # The page is taller than the 1024×660 minimum window once five variables
        # are on the card — it scrolls vertically instead of squeezing its labels.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        page = QWidget()
        body = QVBoxLayout(page)
        body.setContentsMargins(0, 0, 6, 0)
        body.setSpacing(12)
        scroll.setWidget(page)
        root.addWidget(scroll, 1)

        self.status = wrapping(QLabel())
        self.status.setStyleSheet(theme.card())
        body.addWidget(self.status)

        bar = QHBoxLayout()
        self.run = QPushButton(tr("Recommend next candidates"))
        self.run.setProperty("primary", True)
        self.run.clicked.connect(self.request)
        bar.addWidget(self.run)

        bar.addSpacing(12)
        self.override = QCheckBox(tr("Force a recommendation despite unmet requirements"))
        self.override.setToolTip(tr("Only after reading the warnings.\n"
                                    "Reports built in this state carry a "
                                    "\"generated with requirements unmet\" stamp."))
        self.override.stateChanged.connect(self._on_override)
        bar.addWidget(self.override)
        bar.addStretch(1)
        body.addLayout(bar)

        # EI, one at a time, is the default — the method and the batch size fold
        # away so the first thing under the button is the condition to measure.
        # (Whether batches beat sequential picking has not been validated.)
        self.adv = Advanced()
        prow = QHBoxLayout()
        prow.addWidget(QLabel(tr("Picking method")))
        self.method = QComboBox()
        for name, cls in ACQUISITIONS:
            self.method.addItem(tr(getattr(cls, "label", name)), name)
        self.method.setMinimumWidth(280)
        self.method.currentIndexChanged.connect(self._on_method)
        prow.addWidget(self.method)
        prow.addStretch(1)
        self.adv.add_layout(prow)
        self.method_why = wrapping(QLabel())
        self.method_why.setStyleSheet(theme.muted())
        self.adv.add(self.method_why)
        brow = QHBoxLayout()
        brow.addWidget(QLabel(tr("At a time")))
        self.batch = QSpinBox(minimum=1, maximum=MAX_BATCH, value=1)
        self.batch.setToolTip(tr("Receive several at once. Each picked point assumes its predicted\n"
                                 "mean as if observed, then the next is chosen (kriging believer).\n"
                                 "Whether batches beat sequential picking has not been validated."))
        self.batch.valueChanged.connect(lambda _: self.adv.set_summary(self._summary_text()))
        brow.addWidget(self.batch)
        brow.addStretch(1)
        self.adv.add_layout(brow)

        self.beta_row = QWidget()
        bl = QHBoxLayout(self.beta_row)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(QLabel(tr("Exploration strength b")))
        self.beta = QDoubleSpinBox(minimum=0.5, maximum=4.0, singleStep=0.5, value=2.0)
        self.beta.setToolTip(tr("Larger pushes further into uncertainty. Do not casually raise the default 2.0."))
        self.beta.valueChanged.connect(self._on_method)
        bl.addWidget(self.beta)
        bl.addStretch(1)
        self.adv.add(self.beta_row)
        self.adv.set_summary(self._summary_text())
        body.addWidget(self.adv)

        # ── the one to act on ──────────────────────────────────────
        self.card = Section(tr("Measure this next"))
        self.card_grid = QGridLayout()
        self.card_grid.setHorizontalSpacing(24)
        self.card_grid.setVerticalSpacing(4)
        self.card_grid.setColumnStretch(0, 1)
        # the grid keeps its natural width instead of stretching across a wide
        # window — a name at the far left and its value at the far right is not
        # a pair anyone can read
        card_row = QHBoxLayout()
        card_row.addLayout(self.card_grid)
        card_row.addStretch(1)
        self.card.add_layout(card_row)
        self.card_meta = wrapping(QLabel())
        theme.set_role(self.card_meta, "muted")
        self.card.add(self.card_meta)
        self.card_flag = wrapping(QLabel())
        self.card_flag.setStyleSheet(f"color:{theme.WARN};")
        self.card_flag.setVisible(False)
        self.card.add(self.card_flag)
        self.card.setVisible(False)
        body.addWidget(self.card)

        # ── the runners-up ─────────────────────────────────────────
        self.alt_title = QLabel(tr("Other candidates"))
        theme.set_role(self.alt_title, "h2")
        self.alt_title.setVisible(False)
        body.addWidget(self.alt_title)

        self.table = _AltTable(self._fit_columns)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        # the widths are set from font metrics below — no floor of the style's own
        self.table.horizontalHeader().setMinimumSectionSize(1)
        self.table.setVisible(False)
        body.addWidget(self.table)

        self.note = wrapping(QLabel())
        self.note.setStyleSheet(theme.muted())
        body.addWidget(self.note)

        out = QHBoxLayout()
        self.accept = QPushButton(tr("Insert into the data table"))
        self.accept.setToolTip(tr("Pre-fills the suggested conditions as gray rows on the Data tab.\n"
                                  "They become real once you enter the measured values."))
        self.accept.clicked.connect(self._accept)
        self.export = QPushButton(tr("Export instruction sheet (CSV)"))
        self.export.setToolTip(tr("Saves condition values + suggested replicates + the evidence, as a table."))
        self.export.clicked.connect(self._export)
        out.addWidget(self.accept)
        out.addWidget(self.export)
        out.addStretch(1)
        body.addStretch(1)
        root.addLayout(out)

        self._set_enabled(False)
        self._on_method()
        self._say_idle()

    def _on_method(self) -> None:
        name = self.method.currentData() or "EI"
        cls = dict(ACQUISITIONS)[name]
        when = getattr(cls, "when", "")
        self.method_why.setText(tr(when) if when else "")
        self.beta_row.setVisible(name == "UCB")
        self.adv.set_summary(self._summary_text())
        self.acquisition_changed.emit()

    def _summary_text(self) -> str:
        n = self.batch.value()
        parts = [self.method.currentText(),
                 tr("1 suggestion at a time") if n == 1 else tr("{n} suggestions at a time", n=n)]
        if self.method.currentData() == "UCB":
            parts.append(f"b = {self.beta.value():g}")
        return " · ".join(parts)

    def acquisition(self):
        """The currently chosen method. The Model tab uses this too — it must be set in one place."""
        name = self.method.currentData() or "EI"
        kwargs = {"beta": self.beta.value()} if name == "UCB" else {}
        return make_acquisition(name, **kwargs)

    # ── wiring to the core ─────────────────────────────────────────
    def set_context(self, dataset, gate, model, acquisition=None) -> None:
        """Called by the main window every time diagnosis finishes.

        No acquisition is passed in — **this tab is where it is chosen**, so
        this tab is the original. (An attribute `self.acquisition = ...` once
        shadowed the method of the same name and blew up the screen.)
        """
        self.dataset = dataset
        self.gate = gate
        self.model = model
        self.run.setEnabled(dataset is not None and gate is not None)
        # While locked there is nothing to choose — pull the eye to the verdict instead
        locked = gate is not None and gate.locked
        self.adv.setEnabled(not locked or self.override.isChecked())
        if gate is not None and not gate.locked:
            self.override.setChecked(False)
        self.override.setVisible(bool(gate is not None and gate.locked))
        if self.result is None:
            self._say_idle()

    def request(self) -> None:
        """Ask for a recommendation. **The core judges** — the gate is not re-interpreted here."""
        if self.dataset is None or self.gate is None:
            return
        result = recommend(
            self.dataset, self.project.inputs, self.gate,
            acquisition=self.acquisition(),
            model=self.model,
            batch=self.batch.value(),
            acq_history=self.acq_history,
            override=self.override.isChecked(),
            constraint=self.project.constraint,
        )
        self.result = result
        if isinstance(result, Recommendation):
            self.acq_history.append(result.acq_max)
        self._render(result)

    # ── rendering ──────────────────────────────────────────────────
    def _render(self, result: RecommendResult) -> None:
        if isinstance(result, Locked):
            self._render_locked(result)
        else:
            self._render_suggestions(result)

    def _hide_results(self) -> None:
        self.card.setVisible(False)
        self.alt_title.setVisible(False)
        self.table.setRowCount(0)
        self.table.setVisible(False)      # an empty table hogging the screen buries the reasons

    def _render_locked(self, locked: Locked) -> None:
        self._hide_results()
        self._set_enabled(False)
        self.status.setText(tr(
            "<b style='color:{c}'>{headline}</b><ul style='margin:6px 0'>{reasons}</ul>"
            "Follow the prescription on the Diagnose tab first. If you must proceed anyway, "
            "turn on \"Force a recommendation\" above — the result will carry the mark.",
            c=theme.FAIL, headline=locked.headline,
            reasons="".join(f"<li>{r}</li>" for r in locked.reasons)))
        self.status.setStyleSheet(theme.card("fail"))
        self.note.setText("")

    # the card ─────────────────────────────────────────────────────
    def _card_labels(self) -> list[tuple[QLabel, QLabel]]:
        """One (name, value) label pair per variable, rebuilt when the variables change."""
        inputs = self.project.inputs
        if len(self._card_rows) == len(inputs) and \
                all(n.text() == v.name for (n, _), v in zip(self._card_rows, inputs)):
            return self._card_rows
        while self.card_grid.count():
            w = self.card_grid.takeAt(0).widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._card_rows = []
        for r, v in enumerate(inputs):
            name = QLabel(v.name)
            theme.set_role(name, "muted")
            value = QLabel()
            theme.set_role(value, "h2")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.card_grid.addWidget(name, r, 0)
            self.card_grid.addWidget(value, r, 1)
            self._card_rows.append((name, value))
        return self._card_rows

    def _fill_card(self, top, rec: Recommendation) -> None:
        for (_, value), v, x in zip(self._card_labels(), self.project.inputs, top.x_real):
            value.setText(fmt_value(v, x) + (f" {v.unit}" if v.unit else ""))
        self.card_meta.setText(tr(
            "predicted {mean} ± {sd} · acquisition {acq} · suggested reps ×{n}",
            mean=f"{top.predicted_mean:.4g}", sd=f"{top.predicted_std:.3g}",
            acq=f"{top.acq_value:.4g}", n=top.suggested_reps))
        self.card_flag.setText(tr("outside measured range") if top.extrapolated else "")
        self.card_flag.setVisible(top.extrapolated)
        self.card.setVisible(True)

    # the runners-up ───────────────────────────────────────────────
    def _fill_alternatives(self, rest: list) -> None:
        self._alt_headers = [(v.name, f"{v.name} ({v.unit})" if v.unit else v.name)
                             for v in self.project.inputs]
        self._alt_headers += [(tr("predicted"), tr("predicted mean")),
                              ("σ", tr("uncertainty σ")),      # a symbol, not text — the scanner does not see it either
                              (tr("acq."), tr("acq. value"))]
        self.table.setColumnCount(len(self._alt_headers))
        self.table.setHorizontalHeaderLabels([h for h, _ in self._alt_headers])
        self.table.setRowCount(len(rest))
        d = len(self.project.inputs)
        for r, s in enumerate(rest):
            for c, x in enumerate(s.x_real):
                self.table.setItem(r, c, QTableWidgetItem(fmt_value(self.project.inputs[c], x)))
            self.table.setItem(r, d, QTableWidgetItem(f"{s.predicted_mean:.4g}"))
            self.table.setItem(r, d + 1, QTableWidgetItem(f"{s.predicted_std:.4g}"))
            self.table.setItem(r, d + 2, QTableWidgetItem(f"{s.acq_value:.4g}"))
            if s.extrapolated:
                self.table.item(r, 0).setToolTip(tr("outside measured range"))
        # a single suggestion has no runners-up — an empty table would only take room
        self.alt_title.setVisible(bool(rest))
        self.table.setVisible(bool(rest))
        # exactly as tall as its rows: the page scrolls, the table does not
        self.table.setFixedHeight(self.table.horizontalHeader().sizeHint().height()
                                  + sum(self.table.rowHeight(r) for r in range(len(rest)))
                                  + 2 * self.table.frameWidth())
        self._fit_columns()

    def _fit_columns(self) -> None:
        """Share the viewport out between the columns, then shrink each header to the width it got.

        The widths add up to exactly the viewport, so the table can never grow a
        horizontal scroll bar, and each column gets a share in proportion to what
        its own header needs. A header too long for its share is elided — measured
        against the header's real size hint rather than a guessed padding — and
        keeps its full text, unit included, in the tooltip.
        """
        n = self.table.columnCount()
        total = self.table.viewport().width()
        if self._fitting or not n or n != len(self._alt_headers) or total < 4 * n:
            return
        self._fitting = True
        try:
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Fixed)
            for i, (text, tip) in enumerate(self._alt_headers):
                item = self.table.horizontalHeaderItem(i)
                item.setText(text)
                item.setToolTip(tip)
            # what the column would like: its header, or its widest cell
            hints = [max(1, header.sectionSizeHint(i), self.table.sizeHintForColumn(i))
                     for i in range(n)]
            want = sum(hints)
            widths = [max(1, h * total // want) for h in hints]
            widest = hints.index(max(hints))
            widths[widest] = max(1, widths[widest] + total - sum(widths))    # the rounding remainder
            metrics = header.fontMetrics()
            for i, (text, _tip) in enumerate(self._alt_headers):
                item = self.table.horizontalHeaderItem(i)
                budget = widths[i]
                while True:
                    item.setText(metrics.elidedText(text, Qt.ElideRight, budget))
                    if budget <= 4 or header.sectionSizeHint(i) <= widths[i]:
                        break
                    budget -= 6                      # the style's own padding, walked off
                header.resizeSection(i, widths[i])
        finally:
            self._fitting = False

    def _render_suggestions(self, rec: Recommendation) -> None:
        self._fill_card(rec.suggestions[0], rec)
        self._fill_alternatives(rec.suggestions[1:])
        self._set_enabled(bool(rec.suggestions))

        n = len(rec.suggestions)
        head = [tr("<b>1 condition suggested.</b>") if n == 1
                else tr("<b>{n} conditions suggested.</b>", n=n),
                rec.acquisition_label, rec.surrogate_label,
                tr("best measured so far {best}", best=f"{rec.best_measured:.4g}")]
        text = " · ".join(head)
        if rec.gate_bypassed:
            text = tr("<b style='color:{c}'>This recommendation was forced with requirements "
                      "unmet.</b> The report will say so.", c=theme.FAIL) + "<br>" + text
        self.status.setText(text)
        self.status.setStyleSheet(theme.card("fail" if rec.gate_bypassed else "ok"))

        notes = list(rec.warnings)
        if rec.stop_advised:
            notes.append(tr("<b style='color:{c}'>Stopping advised</b> — {why}",
                            c=theme.WARN, why=rec.stop_reason))
        notes.append(tr("\"Insert into the data table\" pre-fills these as gray rows on the "
                        "Data tab. Enter the measured values to make them real."))
        self.note.setText("<br>".join(notes))

    def _say_idle(self) -> None:
        self.status.setText(
            tr("Press \"Recommend next candidates\" to pick what to measure next from the current data."))
        self.status.setStyleSheet(theme.card())

    def _set_enabled(self, on: bool) -> None:
        self.accept.setEnabled(on)
        self.export.setEnabled(on)

    def _on_override(self) -> None:
        self.adv.setEnabled(
            self.gate is None or not self.gate.locked or self.override.isChecked())
        self.override_changed.emit(self.override.isChecked())
        if self.override.isChecked():
            QMessageBox.warning(
                self, tr("Requirements are unmet"),
                tr("There is no evidence this data can support a recommendation.\n\n"
                   "Proceed anyway and the results and the report will be marked "
                   "\"generated with requirements unmet\"."))

    # ── export ─────────────────────────────────────────────────────
    def _accept(self) -> None:
        if not isinstance(self.result, Recommendation):
            return
        payload = [(list(s.x_real),
                    tr("suggested · {acq} · predicted {mean}±{sd}",
                       acq=self.result.acquisition_label,
                       mean=f"{s.predicted_mean:.4g}", sd=f"{s.predicted_std:.3g}"))
                   for s in self.result.suggestions]
        self.points_accepted.emit(payload)

    def _export(self) -> None:
        """The instruction sheet (F-42) — condition values + suggested replicates + evidence."""
        if not isinstance(self.result, Recommendation):
            return
        fn, _ = QFileDialog.getSaveFileName(self, tr("Export instruction sheet"),
                                            "next_measurements.csv",        # i18n: skip
                                            tr("CSV (*.csv)"))
        if not fn:
            return
        with open(fn, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow([f"{v.name} ({v.unit})" if v.unit else v.name
                        for v in self.project.inputs]
                       + [tr("suggested reps"), tr("predicted mean"), tr("uncertainty σ"),
                          tr("acq. value"), tr("note")])
            for s in self.result.suggestions:
                w.writerow([fmt_value(v, x) for v, x in zip(self.project.inputs, s.x_real)]
                           + [s.suggested_reps, f"{s.predicted_mean:.6g}",
                              f"{s.predicted_std:.6g}", f"{s.acq_value:.6g}",
                              tr("outside measured range") if s.extrapolated else ""])
            w.writerow([])
            w.writerow([tr("evidence"), self.result.acquisition_label, self.result.surrogate_label])
            if self.result.gate_bypassed:
                w.writerow([tr("caution"), tr("generated with requirements unmet")])
        QMessageBox.information(self, tr("Exported"),
                                tr("{path}\n\nFill in the values after measuring.", path=fn))
