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
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
                               QPushButton, QScrollArea, QSpinBox, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from core.design import initial_design, suggest_initial_size
from core.i18n import tr
from core.project import default_name
from core.spec import (ObjSpec, SumConstraint, VarSpec, candidate_summary, count_candidates,
                       suggest_log_transform)
from . import theme
from .widgets.advanced import Advanced
from .widgets.section import PageHeader, Section, tell_true_height

TYPE_KEYS = ("continuous", "integer", "categorical")        # i18n: key


def type_labels() -> list[tuple[str, str]]:
    """(key, label) for the variable-type combo — translated per call, never at import."""
    return [(k, tr(k)) for k in TYPE_KEYS]



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

        head = PageHeader(tr("Setup — what you can turn, and what should improve"),
                          tr("Everything defined here is the premise of every other screen. "
                             "Invalid values never get in."))
        head.add_right(QLabel(tr("Project name")))
        self.name = QLineEdit()
        self.name.setMinimumWidth(self.name.fontMetrics().averageCharWidth() * 22)
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
        gin = Section(tr("Input variables — the knobs you can turn"),
                      tr("Design variables only. Loads and ambient values a device merely "
                         "experiences are not knobs."))

        self.empty_hint = QLabel(tr(
            "No variables yet.  Press <b>\"+ Add variable\"</b> to start.<br>"
            "e.g. — name <b>power</b> · unit <b>W</b> · type <b>continuous</b> · "
            "min <b>150</b> · max <b>200</b>"))
        self.empty_hint.setWordWrap(True)
        tell_true_height(self.empty_hint)
        self.empty_hint.setStyleSheet(theme.card("info"))
        gin.add(self.empty_hint)

        self.vars = QTableWidget(0, 6)
        self.vars.setHorizontalHeaderLabels([tr("name"), tr("unit"), tr("type"),
                                             tr("min"), tr("max"), tr("step")])
        for col, tip in enumerate([
                tr("Variable name. Tables, figures and reports use this name."),
                tr("Unit. May be left empty."),
                tr("continuous = any value · integer = 3, 4, 5… · categorical = a fixed set"),
                tr("The smallest value this knob can be set to"),
                tr("The largest value this knob can be set to"),
                tr("The spacing the instrument can actually be set to (continuous only). "
                   "e.g. 10 if the power supply only moves in 10 W steps.\n"
                   "Leave it empty and any value can be chosen (infinitely many candidates).\n"
                   "Requirement ① compares the candidate count on this grid with the budget.")]):
            it = self.vars.horizontalHeaderItem(col)
            if it is not None:
                it.setToolTip(tip)
        head = self.vars.horizontalHeader()
        for c in range(6):
            head.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        # A stretched name column was squeezed to nothing at 1024 and elided the names away.
        # Every column is sized to what it holds; the last one takes up whatever slack is left.
        head.setStretchLastSection(True)
        fm = self.vars.fontMetrics()
        # 84px was a floor measured on the English headers; six of them do not fit the card at
        # 1024, and min/max/step were pushed off the right edge where nobody could reach them.
        # The floor is what a number needs to be readable, in whichever font is on.
        head.setMinimumSectionSize(fm.horizontalAdvance("000000") + 16)
        # ResizeToContents measures the header, not the combo inside the cell — the type
        # column has to hold the widest label of whichever language is on
        head.setSectionResizeMode(2, QHeaderView.Fixed)
        self.vars.setColumnWidth(2, max(fm.horizontalAdvance(lbl)
                                        for _, lbl in type_labels()) + 64)   # combo arrow + cell padding
        # a cramped row clips the text inside cell editors
        self.vars.verticalHeader().setDefaultSectionSize(theme.ROW_HEIGHT)
        self.vars.verticalHeader().setVisible(False)
        self.vars.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Six editable columns do not fit the card at 1024 wide. Scrolling to min/max/step
        # beats hiding them, so the table opts out of the width check the way the Data grid does.
        self.vars.setProperty("clip_ok", True)
        self.vars.itemChanged.connect(self._push)
        gin.add(self.vars)

        row = QHBoxLayout()
        add = QPushButton(tr("+ Add variable"))
        add.clicked.connect(self._add_var)
        rm = QPushButton(tr("− Remove"))
        rm.clicked.connect(self._del_var)
        self.autofill = QPushButton(tr("Fill ranges"))
        self.autofill.setToolTip(tr("Fills min/max from the measurements you already entered.\n"
                                    "Typing them by hand is tedious, and a typo sends the\n"
                                    "recommendation somewhere absurd."))
        self.autofill.clicked.connect(self._autofill_ranges)
        self.var_msg = QLabel()
        self.var_msg.setWordWrap(True)
        tell_true_height(self.var_msg)
        self.var_msg.setStyleSheet(f"color:{theme.FAIL};")
        row.addWidget(add)
        row.addWidget(rm)
        row.addWidget(self.autofill)
        row.addStretch(1)
        gin.add_layout(row)
        gin.add(self.var_msg)
        # candidate count — shown right where requirement ①'s input is defined
        self.cand_hint = QLabel()
        self.cand_hint.setWordWrap(True)
        tell_true_height(self.cand_hint)
        self.cand_hint.setStyleSheet(theme.muted())
        gin.add(self.cand_hint)
        left.addWidget(gin)

        # ── sum constraint ─────────────────────────────────────────
        gcon = Section(tr("Sum constraint — variables with a fixed total (optional)"),
                       tr("Turn on when a few variables must add up to a fixed total, as a "
                          "composition does. The initial design, the candidates and the "
                          "recommendations all stay inside it."))
        self.con_on = QCheckBox(tr("Use a sum constraint"))
        self.con_on.setToolTip(tr("e.g. A + B + C = 100 (%)  ·  additive1 + additive2 ≤ 5 (wt%)"))
        self.con_on.toggled.connect(self._on_constraint_toggled)
        gcon.add(self.con_on)
        self.con_body = QWidget()
        cb = QVBoxLayout(self.con_body)
        cb.setContentsMargins(0, 0, 0, 0)
        cb.setSpacing(8)
        cb.addWidget(QLabel(tr("Variables in the sum (2 or more)")))
        self.con_vars = QListWidget()
        self.con_vars.setToolTip(tr("The constraint applies to the sum of the checked variables. "
                                    "Categorical variables cannot take part."))
        self.con_vars.setMaximumHeight(theme.ROW_HEIGHT * 4)
        self.con_vars.itemChanged.connect(self._push)
        cb.addWidget(self.con_vars)
        row_c = QHBoxLayout()
        row_c.addWidget(QLabel(tr("The sum is")))
        self.con_kind = QComboBox()
        self.con_kind.addItem(tr("= exactly"), "eq")       # i18n: skip
        self.con_kind.addItem(tr("≤ at most"), "le")       # i18n: skip
        self.con_kind.currentIndexChanged.connect(self._push)
        row_c.addWidget(self.con_kind)
        self.con_total = QDoubleSpinBox(minimum=-1e9, maximum=1e9, decimals=4, value=100.0)
        self.con_total.setToolTip(tr("The total. For a composition, 100 (%) or 1."))
        # The range gives the box a sixteen-digit size hint, which at 1024 wide (Windows fonts)
        # pushes the page past the viewport. A total is "100" or "1": the box may shrink to
        # that and grows back to its hint wherever there is room.
        self.con_total.setMinimumWidth(theme.CONTROL_H * 4)
        self.con_total.valueChanged.connect(self._push)
        row_c.addWidget(self.con_total)
        row_c.addStretch(1)
        cb.addLayout(row_c)
        self.con_msg = QLabel()
        self.con_msg.setWordWrap(True)
        tell_true_height(self.con_msg)
        cb.addWidget(self.con_msg)
        self.con_body.setVisible(False)
        gcon.add(self.con_body)
        left.addWidget(gcon)
        left.addStretch(1)

        # ── objective ──────────────────────────────────────────────
        gout = Section(tr("Response — the value you want to improve"),
                       tr("Exactly one. Improving several values at once is outside this tool."))
        of = QFormLayout()
        of.setHorizontalSpacing(14)
        of.setVerticalSpacing(10)
        self.obj_name = QLineEdit()
        self.obj_unit = QLineEdit()
        self.goal = QComboBox()
        self.goal.addItem(tr("Maximize — bigger is better"), "max")     # i18n: skip
        self.goal.addItem(tr("Minimize — smaller is better"), "min")    # i18n: skip
        self.log = QCheckBox(tr("Work in log scale"))
        self.log.setToolTip(tr("Turn on when the response spans orders of magnitude (say 1e-4 to 1e2).\n"
                               "The setting is saved with the project and written into the report — "
                               "it changes the verdicts."))
        self.log_hint = QLabel()
        self.log_hint.setWordWrap(True)
        tell_true_height(self.log_hint)
        self.log_hint.setStyleSheet(theme.muted())
        for w in (self.obj_name, self.obj_unit):
            w.textChanged.connect(self._push)
        self.goal.currentIndexChanged.connect(self._push)
        self.log.stateChanged.connect(self._push)
        self.log.stateChanged.connect(self._update_log_hint)
        of.addRow(tr("Name"), self.obj_name)
        of.addRow(tr("Unit"), self.obj_unit)
        of.addRow(tr("Goal"), self.goal)
        gout.add_layout(of)
        gout.add(self.log_hint)
        adv_obj = Advanced()
        adv_obj.add(self.log)
        gout.add(adv_obj)
        right.addWidget(gout)

        # ── budget ─────────────────────────────────────────────────
        gb = Section(tr("Budget — how many measurements in total"),
                     tr("This count against the condition count decides whether optimization "
                        "means anything at all."))
        bf = QFormLayout()
        bf.setHorizontalSpacing(14)
        bf.setVerticalSpacing(10)
        self.budget = QSpinBox(minimum=1, maximum=100000, value=40)
        self.budget.valueChanged.connect(self._on_budget)
        self.init_n = QSpinBox(minimum=1, maximum=100000, value=11)
        self.init_n.valueChanged.connect(self._push)
        self.init_hint = QLabel()
        self.init_hint.setWordWrap(True)
        tell_true_height(self.init_hint)
        self.init_hint.setStyleSheet(theme.muted())

        gen = QPushButton(tr("Generate initial design → export CSV"))
        gen.setProperty("primary", True)
        gen.setToolTip(tr("Draws the first measurement points space-filling (maximin LHS).\n"
                          "Measured on a grid, curved terrain looks flat — and more replicates "
                          "do not fix that."))
        gen.clicked.connect(self._make_initial)

        bf.addRow(tr("Total measurements"), self.budget)
        gb.add_layout(bf)
        gb.add(self.init_hint)
        gb.add(gen)
        self.adv_budget = Advanced()
        row_init = QHBoxLayout()
        row_init.addWidget(QLabel(tr("Initial design points")))
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
        if self.vars.horizontalHeader().length() > self.vars.viewport().width():
            h += self.vars.horizontalScrollBar().sizeHint().height()   # or it eats the last row
        self.vars.setFixedHeight(h + 2 * self.vars.frameWidth() + 2)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._fit_vars()          # a narrower window means a scroll bar, which needs its own row

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
        c = p.constraint
        self.con_on.setChecked(c is not None)
        self.con_body.setVisible(c is not None)
        if c is not None:
            self.con_kind.setCurrentIndex(0 if c.kind == "eq" else 1)
            self.con_total.setValue(c.total)
        self._sync_constraint_vars(p.inputs, set(c.names) if c else set())
        self._loading = False
        self._update_hint()
        self._update_log_hint()
        self._validate()

    def _set_var_row(self, i: int, v: VarSpec) -> None:
        self.vars.setItem(i, 0, QTableWidgetItem(v.name))
        self.vars.setItem(i, 1, QTableWidgetItem(v.unit))
        cb = QComboBox()
        for key, label in type_labels():
            cb.addItem(label, key)
        cb.setCurrentIndex(TYPE_KEYS.index(v.type))
        cb.currentIndexChanged.connect(self._push)
        self.vars.setCellWidget(i, 2, cb)
        self.vars.setItem(i, 3, QTableWidgetItem("" if v.lo is None else f"{v.lo:g}"))
        self.vars.setItem(i, 4, QTableWidgetItem("" if v.hi is None else f"{v.hi:g}"))
        self.vars.setItem(i, 5, QTableWidgetItem("" if v.step is None else f"{v.step:g}"))

    def _sync_constraint_vars(self, inputs: list[VarSpec], checked: set[str]) -> None:
        """Rebuild the constraint's variable list from the current names (checks carry over by name)."""
        was = self._loading
        self._loading = True
        self.con_vars.clear()
        for v in inputs:
            it = QListWidgetItem(f"{v.name} ({v.unit})" if v.unit else v.name)
            it.setData(Qt.UserRole, v.name)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if v.name in checked else Qt.Unchecked)
            self.con_vars.addItem(it)
        self._loading = was

    def _checked_constraint_names(self) -> tuple[str, ...]:
        return tuple(self.con_vars.item(i).data(Qt.UserRole)
                     for i in range(self.con_vars.count())
                     if self.con_vars.item(i).checkState() == Qt.Checked)

    def _on_constraint_toggled(self, on: bool) -> None:
        self.con_body.setVisible(on)
        self._push()

    def collect_constraint(self, inputs: list[VarSpec]) -> tuple[SumConstraint | None, str]:
        """Screen → sum constraint. The second return value is the error message (empty = fine)."""
        if not self.con_on.isChecked():
            return None, ""
        names = self._checked_constraint_names()
        if len(names) < 2:
            return None, tr("check at least 2 variables to put in the sum")
        try:
            c = SumConstraint(names, self.con_total.value(), self.con_kind.currentData())
            c.validate(inputs)
        except ValueError as e:
            return None, str(e)
        return c, ""

    def _autofill_ranges(self) -> None:
        """Fill ranges from the measurements' min/max. No margin is added —
        outside the measured range the model has learned nothing, so widening
        is the user's decision to make."""
        ms = [m for m in self.project.measurements
              if not m.get("excluded") and not m.get("pending")]
        if not ms:
            QMessageBox.information(
                self, tr("No measurements"),
                tr("Enter values on the Data tab first, then the ranges can be filled."))
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
                errs.append(tr("row {row}: the name is empty", row=i + 1))
                continue
            names.append(name)
            if vtype == "categorical":          # there is no level editor yet
                errs.append(tr("{name}: categorical variables cannot be built on this screen yet "
                               "— use continuous or integer", name=name))
                continue
            try:
                lo, hi = float(lo_s), float(hi_s)
            except ValueError:
                errs.append(tr("{name}: min/max is not a number", name=name))
                continue
            if not lo < hi:
                errs.append(tr("{name}: min ({lo}) must be < max ({hi})",
                               name=name, lo=f"{lo:g}", hi=f"{hi:g}"))
                continue
            step_s = (self.vars.item(i, 5).text() if self.vars.item(i, 5) else "").strip()
            step = None
            if step_s and vtype == "continuous":
                try:
                    step = float(step_s)
                except ValueError:
                    errs.append(tr("{name}: the step is not a number", name=name))
                    continue
            try:
                out.append(VarSpec(name, unit, vtype, lo, hi, step=step))
            except ValueError as e:
                errs.append(str(e))
        dup = {n for n in names if names.count(n) > 1}
        if dup:
            errs.append(tr("duplicate names: {names}", names=", ".join(sorted(dup))))
        if not out and self.vars.rowCount():
            errs.append(tr("define at least one input variable"))
        if len(out) > 10:
            errs.append(tr("at most 10 input variables (currently {n})", n=len(out)))
        return out, errs

    def _push(self) -> None:
        if self._loading:
            return
        p = self.project
        p.name = self.name.text() or default_name()
        p.objective = ObjSpec(self.obj_name.text() or "response",           # i18n: skip — data
                              self.obj_unit.text(),
                              self.goal.currentData(), self.log.isChecked())
        p.budget_total = self.budget.value()
        p.initial_design = self.init_n.value()
        inputs, _ = self.collect()
        if inputs:
            p.inputs = inputs
        if [v.name for v in p.inputs] != [self.con_vars.item(i).data(Qt.UserRole)
                                          for i in range(self.con_vars.count())]:
            self._sync_constraint_vars(p.inputs, set(self._checked_constraint_names()))
        p.constraint, _ = self.collect_constraint(p.inputs)
        self._validate()
        self.changed.emit()

    def _validate(self) -> None:
        inputs, errs = self.collect()
        self.var_msg.setText("  ·  ".join(errs))
        constraint, cerr = self.collect_constraint(inputs)
        self.con_msg.setStyleSheet(f"color:{theme.FAIL};" if cerr else theme.muted())
        self.con_msg.setText(cerr or (self._constraint_status(constraint, inputs) if constraint else ""))
        self._update_candidates(inputs, constraint if not cerr else None)

    def _constraint_status(self, c: SumConstraint, inputs: list[VarSpec]) -> str:
        """The constraint as a sentence — plus a warning if measured rows already violate it."""
        txt = tr("constraint: <b>{rule}</b>", rule=c.describe())
        rows = [m for m in self.project.measurements
                if not m.get("excluded") and not m.get("pending")]
        try:
            bad = sum(1 for m in rows if not c.satisfied(m["inputs"], inputs))
        except (ValueError, IndexError, TypeError):
            bad = 0
        if bad:
            txt += (f"<br><span style='color:{theme.WARN};'>"                       # i18n: skip
                    + tr("{n} measured rows already violate this constraint — check that "
                         "the constraint, and the values, are right.", n=bad)
                    + "</span>")
        return txt

    def _update_candidates(self, inputs: list[VarSpec], constraint: SumConstraint | None) -> None:
        """The input to requirement ① — how many conditions there are to choose from, next to the budget."""
        if not inputs:
            self.cand_hint.setText("")
            return
        budget = self.budget.value()
        try:
            n = count_candidates(inputs, constraint)
            where = candidate_summary(inputs, constraint)
        except ValueError:
            self.cand_hint.setText("")
            return
        if n is not None and n <= budget:
            self.cand_hint.setStyleSheet(f"color:{theme.FAIL};")
            self.cand_hint.setText(tr(
                "{where} ≤ budget {budget} — <b>requirement ① unmet</b>: measuring everything "
                "is better. A finer step or a wider range gives more candidates.",
                where=where, budget=budget))
        else:
            self.cand_hint.setStyleSheet(theme.muted())
            self.cand_hint.setText(tr("{where} — more than the budget of {budget}, "
                                      "so requirement ① passes.", where=where, budget=budget))

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
            self.log_hint.setText(tr(
                "The response spans two or more orders of magnitude — "
                "<b>turning on the log scale is the better choice</b> (Advanced)."))
        elif self.log.isChecked():
            self.log_hint.setText(tr("Working in log10 scale. The report says so too."))
        else:
            self.log_hint.setText("")

    def _update_hint(self) -> None:
        rec = suggest_initial_size(self.budget.value())
        if not self._loading and self.init_n.value() != rec:
            pass                       # the user set it in Advanced — respect that
        self.init_hint.setText(
            tr("The first batch draws <b>{n} points</b> space-filling "
               "({rec} recommended — 25–30% of the budget).",
               n=self.init_n.value(), rec=rec))
        self.adv_budget.set_summary(tr("initial design: {n} points", n=self.init_n.value()))

    def _make_initial(self) -> None:
        inputs, errs = self.collect()
        if errs:
            QMessageBox.warning(self, tr("Finish the variable definitions first"), "\n".join(errs))
            return
        constraint, cerr = self.collect_constraint(inputs)
        if cerr:
            QMessageBox.warning(self, tr("Finish the sum constraint first"), cerr)
            return
        k = self.init_n.value()
        X = initial_design(k, inputs, seed=0, constraint=constraint)
        fn, _ = QFileDialog.getSaveFileName(self, tr("Export initial design"),
                                            "initial_design.csv",      # i18n: skip — file name
                                            tr("CSV (*.csv)"))
        if not fn:
            return
        with open(fn, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow([f"{v.name} ({v.unit})" if v.unit else v.name for v in inputs]
                       + [self.obj_name.text() or "response"])          # i18n: skip — column names
            for row in X:
                w.writerow([f"{x:g}" for x in row] + [""])
        QMessageBox.information(
            self, tr("Exported"),
            tr("Saved {n} points.\nMeasure them, then fill in the values on the Data tab.", n=k))
