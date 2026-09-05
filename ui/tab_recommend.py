# -*- coding: utf-8 -*-
"""Tab 5, Recommend — next candidates · batch · instruction sheet (F-20 ~ F-25 · F-42).

This screen **only displays** what `core.recommend.recommend()` returned.
All judgment ends in the core — if a screen could lift the lock or pick
conditions itself, this project's original mistake ("running optimization on
data that cannot support it") would move inside the tool.

Receive `Locked` and the suggestions **are simply not in the object.**
Nothing to take out by mistake.
"""
from __future__ import annotations

import csv

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox,
                               QFileDialog, QHBoxLayout, QHeaderView, QLabel,
                               QMessageBox, QPushButton, QSpinBox, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from core.acquisition import ACQUISITIONS, make_acquisition
from core.recommend import Locked, Recommendation, RecommendResult, recommend
from . import theme
from .widgets.advanced import Advanced
from .widgets.section import PageHeader, Section, link_button

MAX_BATCH = 10


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
        self._build()

    # ── screen ─────────────────────────────────────────────────────
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        head = PageHeader("Recommend — the next condition to measure",
                          "Opens only after the diagnostic requirements pass. A recommendation "
                          "comes as condition values, a suggested replicate count, and its evidence.")
        why = link_button("It is locked — can I not just use it anyway?")
        why.clicked.connect(lambda: self.help_requested.emit("locked"))
        head.add_right(why)
        root.addWidget(head)

        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setStyleSheet(theme.card())
        root.addWidget(self.status)

        # The picking method — not hidden. Named plainly so the single default suffices.
        pick = Section("How the next candidate is chosen")
        pv = pick.body
        prow = QHBoxLayout()
        self.method = QComboBox()
        for name, cls in ACQUISITIONS:
            self.method.addItem(getattr(cls, "label", name), name)
        self.method.setMinimumWidth(280)
        self.method.currentIndexChanged.connect(self._on_method)
        prow.addWidget(self.method)
        prow.addStretch(1)
        pv.addLayout(prow)
        self.method_why = QLabel()
        self.method_why.setWordWrap(True)
        self.method_why.setStyleSheet(theme.muted())
        pv.addWidget(self.method_why)
        self.pick_box = pick
        root.addWidget(pick)

        bar = QHBoxLayout()
        self.run = QPushButton("Recommend next candidates")
        self.run.setProperty("primary", True)
        self.run.clicked.connect(self.request)
        bar.addWidget(self.run)

        bar.addSpacing(12)
        self.override = QCheckBox("Force a recommendation despite unmet requirements")
        self.override.setToolTip("Only after reading the warnings.\n"
                                 "Reports built in this state carry a "
                                 "\"generated with requirements unmet\" stamp.")
        self.override.stateChanged.connect(self._on_override)
        bar.addWidget(self.override)
        bar.addStretch(1)
        root.addLayout(bar)

        # One at a time is the default. Whether batches beat sequential picking
        # has not been validated — so it does not get a prominent spot.
        self.adv = Advanced(summary="1 suggestion at a time")
        brow = QHBoxLayout()
        brow.addWidget(QLabel("At a time"))
        self.batch = QSpinBox(minimum=1, maximum=MAX_BATCH, value=1)
        self.batch.setToolTip("Receive several at once. Each picked point assumes its predicted\n"
                              "mean as if observed, then the next is chosen (kriging believer).\n"
                              "Whether batches beat sequential picking has not been validated.")
        self.batch.valueChanged.connect(lambda _: self.adv.set_summary(self._summary_text()))
        brow.addWidget(self.batch)
        brow.addStretch(1)
        self.adv.add_layout(brow)

        self.beta_row = QWidget()
        bl = QHBoxLayout(self.beta_row)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(QLabel("Exploration strength b"))
        self.beta = QDoubleSpinBox(minimum=0.5, maximum=4.0, singleStep=0.5, value=2.0)
        self.beta.setToolTip("Larger pushes further into uncertainty. Do not casually raise the default 2.0.")
        self.beta.valueChanged.connect(self._on_method)
        bl.addWidget(self.beta)
        bl.addStretch(1)
        self.adv.add(self.beta_row)
        root.addWidget(self.adv)

        self.table = QTableWidget(0, 0)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table, 1)

        self.note = QLabel()
        self.note.setWordWrap(True)
        self.note.setStyleSheet(theme.muted())
        root.addWidget(self.note)

        out = QHBoxLayout()
        self.accept = QPushButton("Insert into the data table")
        self.accept.setToolTip("Pre-fills the suggested conditions as gray rows on the Data tab.\n"
                               "They become real once you enter the measured values.")
        self.accept.clicked.connect(self._accept)
        self.export = QPushButton("Export instruction sheet (CSV)")
        self.export.setToolTip("Saves condition values + suggested replicates + the evidence, as a table.")
        self.export.clicked.connect(self._export)
        out.addWidget(self.accept)
        out.addWidget(self.export)
        out.addStretch(1)
        root.addLayout(out)

        self._set_enabled(False)
        self.table.setVisible(False)
        self._on_method()
        self._say_idle()

    def _on_method(self) -> None:
        name = self.method.currentData() or "EI"
        cls = dict(ACQUISITIONS)[name]
        self.method_why.setText(getattr(cls, "when", ""))
        self.beta_row.setVisible(name == "UCB")
        self.adv.set_summary(self._summary_text())
        self.acquisition_changed.emit()

    def _summary_text(self) -> str:
        n = self.batch.value()
        return f"{n} suggestion{'s' if n > 1 else ''} at a time" + (
            f" · b = {self.beta.value():g}" if self.method.currentData() == "UCB" else "")

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
        self.pick_box.setEnabled(not locked or self.override.isChecked())
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

    def _render_locked(self, locked: Locked) -> None:
        self.table.setRowCount(0)
        self.table.setVisible(False)          # an empty table hogging the screen buries the reasons
        self._set_enabled(False)
        reasons = "".join(f"<li>{r}</li>" for r in locked.reasons)
        self.status.setText(
            f"<b style='color:{theme.FAIL}'>{locked.headline}</b>"
            f"<ul style='margin:6px 0'>{reasons}</ul>"
            "Follow the prescription on the Diagnose tab first. If you must proceed anyway, "
            "turn on \"Force a recommendation\" above — the result will carry the mark.")
        self.status.setStyleSheet(theme.card("fail"))
        self.note.setText("")

    def _render_suggestions(self, rec: Recommendation) -> None:
        headers = [f"{v.name} ({v.unit})" if v.unit else v.name for v in self.project.inputs]
        headers += ["suggested reps", "predicted mean", "uncertainty σ", "acq. value", "note"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rec.suggestions))
        d = len(self.project.inputs)

        for r, s in enumerate(rec.suggestions):
            for c, v in enumerate(s.x_real):
                spec = self.project.inputs[c]
                txt = f"{v:.0f}" if spec.type == "integer" else f"{v:g}"
                self.table.setItem(r, c, QTableWidgetItem(txt))
            self.table.setItem(r, d, QTableWidgetItem(f"×{s.suggested_reps}"))
            self.table.setItem(r, d + 1, QTableWidgetItem(f"{s.predicted_mean:.4g}"))
            self.table.setItem(r, d + 2, QTableWidgetItem(f"{s.predicted_std:.4g}"))
            self.table.setItem(r, d + 3, QTableWidgetItem(f"{s.acq_value:.4g}"))
            self.table.setItem(r, d + 4, QTableWidgetItem(
                "outside measured range" if s.extrapolated else ""))
        self.table.setVisible(True)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(
            self.table.columnCount() - 1, QHeaderView.Stretch)
        self._set_enabled(bool(rec.suggestions))

        head = (f"<b>Suggesting {len(rec.suggestions)} condition"
                f"{'s' if len(rec.suggestions) > 1 else ''}.</b>  "
                f"{rec.acquisition_label} · {rec.surrogate_label} · "
                f"best measured so far {rec.best_measured:.4g}")
        if rec.gate_bypassed:
            head = (f"<b style='color:{theme.FAIL}'>This recommendation was forced with "
                    "requirements unmet.</b> The report will say so.<br>") + head
        self.status.setText(head)
        self.status.setStyleSheet(theme.card("fail" if rec.gate_bypassed else "ok"))

        notes = list(rec.warnings)
        if rec.stop_advised:
            notes.append(f"<b style='color:{theme.WARN}'>Stopping advised</b> — {rec.stop_reason}")
        notes.append("\"Insert into the data table\" pre-fills these as gray rows on the "
                     "Data tab. Enter the measured values to make them real.")
        self.note.setText("<br>".join(notes))

    def _say_idle(self) -> None:
        self.status.setText("Press \"Recommend next candidates\" to pick what to measure next from the current data.")
        self.status.setStyleSheet(theme.card())

    def _set_enabled(self, on: bool) -> None:
        self.accept.setEnabled(on)
        self.export.setEnabled(on)

    def _on_override(self) -> None:
        self.pick_box.setEnabled(
            self.gate is None or not self.gate.locked or self.override.isChecked())
        self.override_changed.emit(self.override.isChecked())
        if self.override.isChecked():
            QMessageBox.warning(
                self, "Requirements are unmet",
                "There is no evidence this data can support a recommendation.\n\n"
                "Proceed anyway and the results and the report will be marked "
                "\"generated with requirements unmet\".")

    # ── export ─────────────────────────────────────────────────────
    def _accept(self) -> None:
        if not isinstance(self.result, Recommendation):
            return
        payload = [(list(s.x_real), f"suggested · {self.result.acquisition_label} · "
                                    f"predicted {s.predicted_mean:.4g}±{s.predicted_std:.3g}")
                   for s in self.result.suggestions]
        self.points_accepted.emit(payload)

    def _export(self) -> None:
        """The instruction sheet (F-42) — condition values + suggested replicates + evidence."""
        if not isinstance(self.result, Recommendation):
            return
        fn, _ = QFileDialog.getSaveFileName(self, "Export instruction sheet",
                                            "next_measurements.csv", "CSV (*.csv)")
        if not fn:
            return
        with open(fn, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow([f"{v.name} ({v.unit})" if v.unit else v.name
                        for v in self.project.inputs]
                       + ["suggested reps", "predicted mean", "uncertainty σ",
                          "acq. value", "note"])
            for s in self.result.suggestions:
                w.writerow([f"{v:g}" for v in s.x_real]
                           + [s.suggested_reps, f"{s.predicted_mean:.6g}",
                              f"{s.predicted_std:.6g}", f"{s.acq_value:.6g}",
                              "outside measured range" if s.extrapolated else ""])
            w.writerow([])
            w.writerow(["evidence", self.result.acquisition_label, self.result.surrogate_label])
            if self.result.gate_bypassed:
                w.writerow(["caution", "generated with requirements unmet"])
        QMessageBox.information(self, "Exported", f"{fn}\n\nFill in the values after measuring.")
