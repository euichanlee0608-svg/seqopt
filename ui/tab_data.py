# -*- coding: utf-8 -*-
"""Tab 2, Data — the measurement table · import · exclusions (F-03 ~ F-06).

Supports what actually happens in a lab.
  · **Copy-paste from Excel** (Ctrl+V) — the most-used way in
  · Adding rows by hand
  · Importing a file (the structure-setup wizard)
  · **Undo (Ctrl+Z)** — a data-entry tool without undo loses someone a day to one slip

One row = one measurement. **Entering the same condition on several rows is
automatically read as replicates** (F-03).
"""
from __future__ import annotations

import copy
import csv

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QFileDialog,
                               QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from core.dataset import group_measurements
from . import theme
from .widgets.section import PageHeader
from .import_wizard import ImportWizard

UNDO_DEPTH = 50
EXCLUDED_BG = QColor(theme.ROW_EXCLUDED)
PENDING_BG = QColor(theme.ROW_PENDING)   # rows pre-filled from a recommendation (not yet measured)
ZERO_BG = QColor(theme.ROW_ZERO)
TEXT_FG = QColor(theme.TEXT)


class DataTab(QWidget):
    changed = Signal()

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self._loading = False
        self._undo: list[list[dict]] = []
        self._redo: list[list[dict]] = []
        self._build()
        self.reload()

    # ── screen ─────────────────────────────────────────────────────
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        head = PageHeader("Data — enter what you measured",
                          "One row is one measurement. The same condition on several rows "
                          "counts automatically as replicates.")
        root.addWidget(head)

        bar = QHBoxLayout()
        imp = QPushButton("Import from file…")
        imp.setProperty("primary", True)
        imp.setToolTip("Opens an Excel/CSV file and lets you assign what each column means.\n"
                       "The assignment is saved with the project, so the next file reads in one step.")
        imp.clicked.connect(self.import_file)
        add = QPushButton("+ Add row")
        add.clicked.connect(self._add_row)
        dele = QPushButton("− Remove selected")
        dele.clicked.connect(self._del_rows)
        paste = QPushButton("Paste (Ctrl+V)")
        paste.setToolTip("Copy a range in Excel, then press this. Tab- or comma-separated tables come in as they are.")
        paste.clicked.connect(self.paste_clipboard)
        exp = QPushButton("Export CSV")
        exp.clicked.connect(self._export)
        for w in (imp, add, dele, paste, exp):
            bar.addWidget(w)

        bar.addSpacing(16)
        self.hide_excluded = QCheckBox("Hide excluded rows")
        self.hide_excluded.stateChanged.connect(self.reload)
        bar.addWidget(self.hide_excluded)
        bar.addStretch(1)
        root.addLayout(bar)

        self.table = QTableWidget(0, 0, alternatingRowColors=True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemChanged.connect(self._on_edit)
        self.table.verticalHeader().setDefaultSectionSize(theme.ROW_HEIGHT)
        root.addWidget(self.table, 1)

        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet(theme.card())
        root.addWidget(self.summary)

        QShortcut(QKeySequence.Paste, self, activated=self.paste_clipboard)
        QShortcut(QKeySequence.Undo, self, activated=self.undo)
        QShortcut(QKeySequence.Redo, self, activated=self.redo)
        QShortcut(QKeySequence.Delete, self, activated=self._del_rows)

    # ── undo ───────────────────────────────────────────────────────
    def _snapshot(self) -> None:
        self._undo.append(copy.deepcopy(self.project.measurements))
        del self._undo[:-UNDO_DEPTH]
        self._redo.clear()

    def undo(self) -> None:
        if not self._undo:
            return
        self._redo.append(copy.deepcopy(self.project.measurements))
        self.project.measurements = self._undo.pop()
        self.reload()
        self.changed.emit()

    def redo(self) -> None:
        if not self._redo:
            return
        self._undo.append(copy.deepcopy(self.project.measurements))
        self.project.measurements = self._redo.pop()
        self.reload()
        self.changed.emit()

    # ── the table ──────────────────────────────────────────────────
    def _headers(self) -> list[str]:
        p = self.project
        cols = [f"{v.name} ({v.unit})" if v.unit else v.name for v in p.inputs]
        obj = p.objective
        cols.append(f"{obj.name} ({obj.unit})" if obj.unit else obj.name)
        return cols + ["exclude", "note"]

    def _header_tip(self, col: int) -> str:
        d = len(self.project.inputs)
        if col < d:
            v = self.project.inputs[col]
            rng = f"  ·  range {v.lo:g} ~ {v.hi:g}" if v.lo is not None else ""
            return f"input variable · {v.type}{rng}\nA knob you turn."
        if col == d:
            o = self.project.objective
            goal = "bigger is better" if o.goal == "max" else "smaller is better"
            log = "  ·  log10 transform" if o.log else ""
            return f"response · {goal}{log}\nThe value you get by measuring."
        if col == d + 1:
            return ("Checked rows leave the calculation. They are removed from the math, "
                    "not deleted — the raw data stays.")
        return "Free-form note. Rows inserted from a recommendation carry their evidence automatically."

    def visible_rows(self) -> list[int]:
        ms = self.project.measurements
        if self.hide_excluded.isChecked():
            return [i for i, m in enumerate(ms) if not m.get("excluded")]
        return list(range(len(ms)))

    def reload(self) -> None:
        p = self.project
        self._loading = True
        heads = self._headers()
        idxs = self.visible_rows()
        self.table.setColumnCount(len(heads))
        self.table.setHorizontalHeaderLabels(heads)
        self.table.setRowCount(len(idxs))
        self.table.setVerticalHeaderLabels([str(p.measurements[i].get("id", i + 1)) for i in idxs])
        d = len(p.inputs)

        for r, i in enumerate(idxs):
            m = p.measurements[i]
            excluded = bool(m.get("excluded"))
            pending = bool(m.get("pending"))
            zeroish = float(m.get("value", 0)) == 0.0 and not pending
            vals = list(m["inputs"]) + [m["value"]]
            for c in range(d + 1):
                if pending and c == d:
                    txt = ""                      # not measured yet — the value cell stays empty
                else:
                    txt = f"{vals[c]:g}" if c < len(vals) else ""
                it = QTableWidgetItem(txt)
                it.setForeground(QBrush(TEXT_FG))   # paint a background and the text color must come too
                if excluded:
                    it.setBackground(QBrush(EXCLUDED_BG))
                elif pending:
                    it.setBackground(QBrush(PENDING_BG))
                    it.setToolTip("Pre-filled from a recommendation. It becomes real when you enter the measured value.")
                elif zeroish and c == d:
                    it.setBackground(QBrush(ZERO_BG))
                self.table.setItem(r, c, it)

            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            chk.setCheckState(Qt.Checked if excluded else Qt.Unchecked)
            if excluded:
                chk.setBackground(QBrush(EXCLUDED_BG))
            elif pending:
                chk.setBackground(QBrush(PENDING_BG))
            if zeroish and not excluded:
                chk.setToolTip("The response is 0. If the sample was destroyed, exclude it.")
            self.table.setItem(r, d + 1, chk)
            note_it = QTableWidgetItem(m.get("note", ""))
            note_it.setForeground(QBrush(TEXT_FG))
            if excluded:
                note_it.setBackground(QBrush(EXCLUDED_BG))
            elif pending:
                note_it.setBackground(QBrush(PENDING_BG))
            self.table.setItem(r, d + 2, note_it)

        # A clipped column title tells you nothing — size to content, full name in the tooltip
        head = self.table.horizontalHeader()
        head.setMinimumSectionSize(72)
        for c in range(self.table.columnCount()):
            head.setSectionResizeMode(c, QHeaderView.ResizeToContents)
            item = self.table.horizontalHeaderItem(c)
            if item is not None:
                item.setToolTip(self._header_tip(c))
        if self.table.columnCount():
            head.setSectionResizeMode(self.table.columnCount() - 1, QHeaderView.Stretch)
        self._loading = False
        self._update_summary()

    def _on_edit(self, item: QTableWidgetItem) -> None:
        if self._loading:
            return
        p = self.project
        d = len(p.inputs)
        idxs = self.visible_rows()
        if item.row() >= len(idxs):
            return
        m = p.measurements[idxs[item.row()]]
        c = item.column()
        self._snapshot()

        if c == d + 1:
            m["excluded"] = item.checkState() == Qt.Checked
        elif c == d + 2:
            m["note"] = item.text()
        else:
            try:
                v = float(item.text())
            except ValueError:
                QMessageBox.warning(self, "Numbers only", f"'{item.text()}' is not a number.")
                self._undo.pop()
                self.reload()
                return
            if c < d:
                m["inputs"][c] = v
            else:
                m["value"] = v
                m.pop("pending", None)            # a value arrived — the row is real now
        # One edited cell does not redraw the whole table — at 69 rows the
        # freeze is visible. Only the row's colors and the summary update.
        self._repaint_row(item.row(), m)
        self._update_summary()
        self.changed.emit()

    def _repaint_row(self, row: int, m: dict) -> None:
        """Fix only one row's background to match its state."""
        d = len(self.project.inputs)
        excluded = bool(m.get("excluded"))
        pending = bool(m.get("pending"))
        zeroish = float(m.get("value", 0)) == 0.0 and not pending
        bg = (EXCLUDED_BG if excluded else PENDING_BG if pending else None)
        self._loading = True
        for c in range(d + 3):
            it = self.table.item(row, c)
            if it is None:
                continue
            it.setForeground(QBrush(TEXT_FG))
            if bg is not None:
                it.setBackground(QBrush(bg))
            elif zeroish and c == d:
                it.setBackground(QBrush(ZERO_BG))
            else:
                it.setBackground(QBrush(QColor(Qt.transparent)))
        self._loading = False

    def _add_row(self) -> None:
        p = self.project
        if not p.inputs:
            QMessageBox.warning(self, "Define variables first", "Define your input variables on the Setup tab.")
            return
        self._snapshot()
        seed = p.measurements[-1]["inputs"] if p.measurements else [
            (v.lo + v.hi) / 2 if v.lo is not None else 0.0 for v in p.inputs]
        p.add(list(seed), 0.0)
        self.reload()
        self.table.scrollToBottom()
        self.changed.emit()

    def _del_rows(self) -> None:
        rows = sorted({x.row() for x in self.table.selectedIndexes()}, reverse=True)
        if not rows:
            return
        idxs = self.visible_rows()
        self._snapshot()
        for r in rows:
            if r < len(idxs):
                self.project.measurements.pop(idxs[r])
        self.reload()
        self.changed.emit()

    def insert_pending(self, payload: list) -> None:
        """Insert recommended conditions **as gray rows, ahead of measurement** (§4-4).

        The value cell stays empty — a number sitting there before the
        measurement makes it impossible to tell measured from predicted, and
        that confusion is the most dangerous kind in this program (principles
        P2 · P3).
        """
        if not payload:
            return
        self._snapshot()
        for inputs, note in payload:
            m = self.project.add(list(inputs), 0.0, note=note)
            m["pending"] = True
        self.reload()
        self.table.scrollToBottom()
        self.changed.emit()

    # ── paste ──────────────────────────────────────────────────────
    def paste_clipboard(self) -> None:
        """Accepts a range copied from Excel as-is. A header row is skipped automatically."""
        p = self.project
        if not p.inputs:
            QMessageBox.warning(self, "Define variables first", "Define your input variables on the Setup tab.")
            return
        text = QApplication.clipboard().text()
        if not text.strip():
            return
        need = len(p.inputs) + 1
        added = skipped = 0
        rows_to_add = []
        for line in text.splitlines():
            if not line.strip():
                continue
            parts = [c.strip() for c in (line.split("\t") if "\t" in line else line.split(","))]
            if len(parts) < need:
                skipped += 1
                continue
            try:
                nums = [float(x) for x in parts[:need]]
            except ValueError:
                skipped += 1                 # header rows and the like
                continue
            rows_to_add.append(nums)

        if not rows_to_add:
            QMessageBox.warning(self, "No numbers to paste",
                                f"Each line needs {need} numbers ({len(p.inputs)} inputs + 1 response).")
            return
        self._snapshot()
        for nums in rows_to_add:
            p.add(nums[:-1], nums[-1])
            added += 1
        self.reload()
        self.changed.emit()
        msg = f"Inserted {added} rows."
        if skipped:
            msg += f"\nSkipped {skipped} non-numeric lines (possibly a header row)."
        QMessageBox.information(self, "Paste finished", msg)

    # ── import · export ────────────────────────────────────────────
    def import_file(self) -> None:
        p = self.project
        dlg = ImportWizard(self, profile=p.import_profile)
        if dlg.exec() != ImportWizard.Accepted:
            return
        prof = dlg.profile
        ms = dlg.result_measurements

        if p.measurements:
            ans = QMessageBox.question(
                self, "There is existing data",
                f"There are already {len(p.measurements)} rows.\n\n"
                "[Yes] replace them with the import\n[No] append after them",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if ans == QMessageBox.Cancel:
                return
            self._snapshot()
            if ans == QMessageBox.Yes:
                p.measurements = []
        else:
            self._snapshot()

        base = p.next_id() - 1
        for k, m in enumerate(ms, 1):
            m["id"] = base + k
        p.measurements.extend(ms)
        p.import_profile = prof
        p.exclude_zero = prof.exclude_zero

        # The variable definitions from the mapping flow into the Setup tab —
        # never make the user write them in two places
        from core.spec import ObjSpec, VarSpec
        ins = prof.input_columns
        cols = list(zip(*[m["inputs"] for m in ms])) if ms else []
        new_inputs = []
        for j, c in enumerate(ins):
            vals = cols[j] if j < len(cols) else (0.0, 1.0)
            lo, hi = float(min(vals)), float(max(vals))
            if lo == hi:
                hi = lo + 1.0
            new_inputs.append(VarSpec(c.label, c.unit, c.type, lo, hi))
        p.inputs = new_inputs
        rc = prof.response_column
        p.objective = ObjSpec(rc.label or "response", rc.unit, p.objective.goal, p.objective.log)

        self.reload()
        self.changed.emit()

    def _export(self) -> None:
        p = self.project
        fn, _ = QFileDialog.getSaveFileName(self, "Export measurement table",
                                            "measurements.csv", "CSV (*.csv)")
        if not fn:
            return
        with open(fn, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(self._headers())
            for m in p.measurements:
                w.writerow([f"{x:g}" for x in m["inputs"]] + [f"{m['value']:g}",
                           "excluded" if m.get("excluded") else "", m.get("note", "")])

    # ── summary ────────────────────────────────────────────────────
    def _update_summary(self) -> None:
        p = self.project
        pending = [m for m in p.measurements if m.get("pending")]
        ms = [m for m in p.measurements
              if not m.get("excluded") and not m.get("pending")]
        if not ms:
            self.summary.setText("No measurements yet. Start with import, paste, or add-row.")
            return
        groups = group_measurements(p.measurements)
        zeros = [k for k, v in groups.items() if max(v) <= 0] if p.exclude_zero else []
        live = {k: v for k, v in groups.items() if k not in set(zeros)}
        reps = sum(1 for v in live.values() if len(v) > 1)
        excluded = len(p.measurements) - len(ms)

        # Same yardstick as the Diagnose tab — two screens with different
        # condition counts leave the user not knowing which to believe
        head = f"<b>{len(live)} usable conditions</b>"
        if zeros:
            head += (f" <span style='color:{theme.TEXT_FAINT}'>"
                     f"({len(groups)} total · {len(zeros)} exclusion candidates)</span>")
        parts = [head, f"{len(ms)} measurements"]
        if live:
            parts.append(f"conditions with replicates {reps}/{len(live)} ({reps / len(live) * 100:.0f}%)")
        if excluded:
            parts.append(f"{excluded} rows excluded by hand")
        if zeros:
            parts.append(f"<span style='color:{theme.WARN}'>{len(zeros)} all-zero conditions</span>")
        if pending:
            parts.append(f"<span style='color:{theme.ACCENT}'>{len(pending)} rows awaiting measurement</span>")
        self.summary.setText("  ·  ".join(parts)
                             + f"<br><span style='color:{theme.TEXT_MUTED}'>The same condition on several "
                               "rows counts automatically as replicates. Ctrl+Z undoes.</span>")
