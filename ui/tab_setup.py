# -*- coding: utf-8 -*-
"""Tab 1, Setup — variable definitions · objective · budget (F-01 · F-02 · F-22).

Everything defined here is the premise of every other tab. So the screen
**makes wrong values impossible to enter** — instead of warning after the
fact, it blocks them and writes the reason next to the field.
"""
from __future__ import annotations

import csv

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox,
                               QFileDialog, QFormLayout, QFrame, QHBoxLayout, QHeaderView,
                               QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea,
                               QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from core.design import initial_design, suggest_initial_size
from core.spec import ObjSpec, VarSpec, suggest_log_transform
from . import theme
from .widgets.advanced import Advanced
from .widgets.section import PageHeader, Section

TYPES = [("continuous", "continuous"), ("integer", "integer"), ("categorical", "categorical")]


class SetupTab(QWidget):
    changed = Signal()

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self._loading = False
        self._build()
        self.reload()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        head = PageHeader("Setup — what you can turn, and what should improve",
                          "Everything defined here is the premise of every other screen. "
                          "Invalid values never get in.")
        head.add_right(QLabel("Project name"))
        self.name = QLineEdit()
        self.name.setMinimumWidth(260)
        self.name.textChanged.connect(self._push)
        head.add_right(self.name)
        root.addWidget(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        cols = QHBoxLayout(body)
        cols.setContentsMargins(0, 0, 6, 0)
        cols.setSpacing(12)
        left = QVBoxLayout()
        left.setSpacing(12)
        right = QVBoxLayout()
        right.setSpacing(12)
        cols.addLayout(left, 3)
        cols.addLayout(right, 2)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        # ── input variables ────────────────────────────────────────
        gin = Section("Input variables — the knobs you can turn",
                      "Design variables only. Loads and ambient values a device merely "
                      "experiences are not knobs.")

        self.empty_hint = QLabel(
            "No variables yet.  Press <b>\"+ Add variable\"</b> to start.<br>"
            "e.g. — name <b>power</b> · unit <b>W</b> · type <b>continuous</b> · "
            "min <b>150</b> · max <b>200</b>")
        self.empty_hint.setWordWrap(True)
        self.empty_hint.setStyleSheet(theme.card("info"))
        gin.add(self.empty_hint)

        self.vars = QTableWidget(0, 5)
        self.vars.setHorizontalHeaderLabels(["name", "unit", "type", "min", "max"])
        for col, tip in enumerate([
                "Variable name. Tables, figures and reports use this name.",
                "Unit. May be left empty.",
                "continuous = any value · integer = 3, 4, 5… · categorical = a fixed set",
                "The smallest value this knob can be set to",
                "The largest value this knob can be set to"]):
            it = self.vars.horizontalHeaderItem(col)
            if it is not None:
                it.setToolTip(tip)
        head = self.vars.horizontalHeader()
        head.setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, 5):
            head.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        head.setMinimumSectionSize(84)
        # a cramped row clips the text inside cell editors
        self.vars.verticalHeader().setDefaultSectionSize(theme.ROW_HEIGHT)
        self.vars.verticalHeader().setVisible(False)
        self.vars.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.vars.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.vars.itemChanged.connect(self._push)
        gin.add(self.vars)

        row = QHBoxLayout()
        add = QPushButton("+ Add variable")
        add.clicked.connect(self._add_var)
        rm = QPushButton("− Remove selected")
        rm.clicked.connect(self._del_var)
        self.autofill = QPushButton("Fill ranges from data")
        self.autofill.setToolTip("Fills min/max from the measurements you already entered.\n"
                                 "Typing them by hand is tedious, and a typo sends the\n"
                                 "recommendation somewhere absurd.")
        self.autofill.clicked.connect(self._autofill_ranges)
        self.var_msg = QLabel()
        self.var_msg.setWordWrap(True)
        self.var_msg.setStyleSheet(f"color:{theme.FAIL};")
        row.addWidget(add)
        row.addWidget(rm)
        row.addWidget(self.autofill)
        row.addWidget(self.var_msg, 1)
        gin.add_layout(row)
        left.addWidget(gin)
        left.addStretch(1)

        # ── objective ──────────────────────────────────────────────
        gout = Section("Response — the value you want to improve",
                       "Exactly one. Improving several values at once is outside this tool.")
        of = QFormLayout()
        of.setHorizontalSpacing(14)
        of.setVerticalSpacing(10)
        self.obj_name = QLineEdit()
        self.obj_unit = QLineEdit()
        self.goal = QComboBox()
        self.goal.addItem("Maximize — bigger is better", "max")
        self.goal.addItem("Minimize — smaller is better", "min")
        self.log = QCheckBox("Work in log scale")
        self.log.setToolTip("Turn on when the response spans orders of magnitude (say 1e-4 to 1e2).\n"
                            "The setting is saved with the project and written into the report — "
                            "it changes the verdicts.")
        self.log_hint = QLabel()
        self.log_hint.setWordWrap(True)
        self.log_hint.setStyleSheet(theme.muted())
        for w in (self.obj_name, self.obj_unit):
            w.textChanged.connect(self._push)
        self.goal.currentIndexChanged.connect(self._push)
        self.log.stateChanged.connect(self._push)
        self.log.stateChanged.connect(self._update_log_hint)
        of.addRow("Name", self.obj_name)
        of.addRow("Unit", self.obj_unit)
        of.addRow("Goal", self.goal)
        gout.add_layout(of)
        gout.add(self.log_hint)
        adv_obj = Advanced()
        adv_obj.add(self.log)
        gout.add(adv_obj)
        right.addWidget(gout)

        # ── budget ─────────────────────────────────────────────────
        gb = Section("Budget — how many measurements in total",
                     "This count against the condition count decides whether optimization "
                     "means anything at all.")
        bf = QFormLayout()
        bf.setHorizontalSpacing(14)
        bf.setVerticalSpacing(10)
        self.budget = QSpinBox(minimum=1, maximum=100000, value=40)
        self.budget.valueChanged.connect(self._on_budget)
        self.init_n = QSpinBox(minimum=1, maximum=100000, value=11)
        self.init_n.valueChanged.connect(self._push)
        self.init_hint = QLabel()
        self.init_hint.setWordWrap(True)
        self.init_hint.setStyleSheet(theme.muted())

        gen = QPushButton("Generate initial design → export CSV")
        gen.setProperty("primary", True)
        gen.setToolTip("Draws the first measurement points space-filling (maximin LHS).\n"
                       "Measured on a grid, curved terrain looks flat — and more replicates "
                       "do not fix that.")
        gen.clicked.connect(self._make_initial)

        bf.addRow("Total measurements", self.budget)
        gb.add_layout(bf)
        gb.add(self.init_hint)
        gb.add(gen)
        self.adv_budget = Advanced()
        row_init = QHBoxLayout()
        row_init.addWidget(QLabel("Initial design points"))
        row_init.addWidget(self.init_n)
        row_init.addStretch(1)
        self.adv_budget.add_layout(row_init)
        gb.add(self.adv_budget)
        right.addWidget(gb)
        right.addStretch(1)

    def _fit_vars(self) -> None:
        """The page scrolls, so the table grows only to its content (3 to 12 rows)."""
        rows = min(max(self.vars.rowCount(), 3), 12)
        h = self.vars.horizontalHeader().sizeHint().height() + rows * theme.ROW_HEIGHT
        self.vars.setFixedHeight(h + 2 * self.vars.frameWidth() + 2)

    # ── project ↔ screen ───────────────────────────────────────────
    def reload(self) -> None:
        p = self.project
        self._loading = True
        self.name.setText(p.name)
        self.obj_name.setText(p.objective.name)
        self.obj_unit.setText(p.objective.unit)
        self.goal.setCurrentIndex(0 if p.objective.goal == "max" else 1)
        self.log.setChecked(p.objective.log)
        self.budget.setValue(p.budget_total)
        self.init_n.setValue(p.initial_design)

        self.vars.setRowCount(len(p.inputs))
        for i, v in enumerate(p.inputs):
            self._set_var_row(i, v)
        self.empty_hint.setVisible(not p.inputs)
        self.vars.setVisible(bool(p.inputs))
        self._fit_vars()
        self._loading = False
        self._update_hint()
        self._update_log_hint()
        self._validate()

    def _set_var_row(self, i: int, v: VarSpec) -> None:
        self.vars.setItem(i, 0, QTableWidgetItem(v.name))
        self.vars.setItem(i, 1, QTableWidgetItem(v.unit))
        cb = QComboBox()
        for key, label in TYPES:
            cb.addItem(label, key)
        cb.setCurrentIndex([k for k, _ in TYPES].index(v.type))
        cb.currentIndexChanged.connect(self._push)
        self.vars.setCellWidget(i, 2, cb)
        self.vars.setItem(i, 3, QTableWidgetItem("" if v.lo is None else f"{v.lo:g}"))
        self.vars.setItem(i, 4, QTableWidgetItem("" if v.hi is None else f"{v.hi:g}"))

    def _autofill_ranges(self) -> None:
        """Fill ranges from the measurements' min/max. No margin is added —
        outside the measured range the model has learned nothing, so widening
        is the user's decision to make."""
        ms = [m for m in self.project.measurements
              if not m.get("excluded") and not m.get("pending")]
        if not ms:
            QMessageBox.information(self, "No measurements",
                                    "Enter values on the Data tab first, then the ranges can be filled.")
            return
        cols = list(zip(*[m["inputs"] for m in ms]))
        self._loading = True
        for i in range(min(self.vars.rowCount(), len(cols))):
            lo, hi = min(cols[i]), max(cols[i])
            if lo == hi:
                hi = lo + 1.0
            self.vars.setItem(i, 3, QTableWidgetItem(f"{lo:g}"))
            self.vars.setItem(i, 4, QTableWidgetItem(f"{hi:g}"))
        self._loading = False
        self._push()

    def _add_var(self) -> None:
        self.empty_hint.setVisible(False)
        self.vars.setVisible(True)
        i = self.vars.rowCount()
        self.vars.insertRow(i)
        self._set_var_row(i, VarSpec(f"var{i + 1}", "", "continuous", 0.0, 1.0))
        self._fit_vars()
        self._push()

    def _del_var(self) -> None:
        rows = sorted({x.row() for x in self.vars.selectedIndexes()}, reverse=True)
        for r in rows:
            self.vars.removeRow(r)
        self._fit_vars()
        self._push()

    def collect(self) -> tuple[list[VarSpec], list[str]]:
        """Screen → VarSpec list. The second return value is the error messages."""
        out, errs = [], []
        names = []
        for i in range(self.vars.rowCount()):
            name = (self.vars.item(i, 0).text() if self.vars.item(i, 0) else "").strip()
            unit = (self.vars.item(i, 1).text() if self.vars.item(i, 1) else "").strip()
            w = self.vars.cellWidget(i, 2)
            vtype = w.currentData() if w else "continuous"
            lo_s = (self.vars.item(i, 3).text() if self.vars.item(i, 3) else "").strip()
            hi_s = (self.vars.item(i, 4).text() if self.vars.item(i, 4) else "").strip()
            if not name:
                errs.append(f"row {i + 1}: the name is empty")
                continue
            names.append(name)
            try:
                lo, hi = float(lo_s), float(hi_s)
            except ValueError:
                errs.append(f"{name}: min/max is not a number")
                continue
            if not lo < hi:
                errs.append(f"{name}: min ({lo:g}) must be < max ({hi:g})")
                continue
            out.append(VarSpec(name, unit, vtype, lo, hi))
        dup = {n for n in names if names.count(n) > 1}
        if dup:
            errs.append(f"duplicate names: {', '.join(sorted(dup))}")
        if not out and self.vars.rowCount():
            errs.append("define at least one input variable")
        if len(out) > 10:
            errs.append(f"at most 10 input variables (currently {len(out)})")
        return out, errs

    def _push(self) -> None:
        if self._loading:
            return
        p = self.project
        p.name = self.name.text() or "New project"
        p.objective = ObjSpec(self.obj_name.text() or "response", self.obj_unit.text(),
                              self.goal.currentData(), self.log.isChecked())
        p.budget_total = self.budget.value()
        p.initial_design = self.init_n.value()
        inputs, _ = self.collect()
        if inputs:
            p.inputs = inputs
        self._validate()
        self.changed.emit()

    def _validate(self) -> None:
        _, errs = self.collect()
        self.var_msg.setText("  ·  ".join(errs))

    def _on_budget(self) -> None:
        # Changing the budget moves the initial size to its recommended value —
        # so the user never has to decide the same thing twice
        if not self._loading:
            self._loading = True
            self.init_n.setValue(suggest_initial_size(self.budget.value()))
            self._loading = False
        self._update_hint()
        self._push()

    def _update_log_hint(self) -> None:
        """Never asks — looks at the data, decides, and says so in a sentence."""
        vals = [m["value"] for m in self.project.measurements
                if not m.get("excluded") and not m.get("pending")]
        if len(vals) < 3:
            self.log_hint.setText("")
            return
        import numpy as np
        want = suggest_log_transform(np.array(vals, dtype=float))
        if want and not self.log.isChecked():
            self.log_hint.setText(
                "The response spans two or more orders of magnitude — "
                "<b>turning on the log scale is the better choice</b> (Advanced).")
        elif self.log.isChecked():
            self.log_hint.setText("Working in log10 scale. The report says so too.")
        else:
            self.log_hint.setText("")

    def _update_hint(self) -> None:
        rec = suggest_initial_size(self.budget.value())
        if not self._loading and self.init_n.value() != rec:
            pass                       # the user set it in Advanced — respect that
        self.init_hint.setText(
            f"The first batch draws <b>{self.init_n.value()} points</b> space-filling "
            f"({rec} points — 25–30% of the budget — recommended).")
        self.adv_budget.set_summary(f"initial design: {self.init_n.value()} points")

    def _make_initial(self) -> None:
        inputs, errs = self.collect()
        if errs:
            QMessageBox.warning(self, "Finish the variable definitions first", "\n".join(errs))
            return
        k = self.init_n.value()
        X = initial_design(k, inputs, seed=0)
        fn, _ = QFileDialog.getSaveFileName(self, "Export initial design",
                                            "initial_design.csv", "CSV (*.csv)")
        if not fn:
            return
        with open(fn, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow([f"{v.name} ({v.unit})" if v.unit else v.name for v in inputs]
                       + [self.obj_name.text() or "response"])
            for row in X:
                w.writerow([f"{x:g}" for x in row] + [""])
        QMessageBox.information(self, "Exported",
                                f"Saved {k} points.\nMeasure them, then fill in the values on the Data tab.")
