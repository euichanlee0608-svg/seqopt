# -*- coding: utf-8 -*-
"""Data-structure setup — any table format gets its meaning assigned here.

Lab spreadsheets differ by instrument and by person. So instead of the code
guessing the format, **the user assigns column roles while looking at the
original.** The assignment is saved as a profile, and the next file of the
same shape reads in one step.

Screen rules
  · The left side is **the original, untouched.** Interpreted values are never shown — differ from the source and trust is gone
  · Changing a role recolors the left column instantly (input=blue · response=green · ignore=gray)
  · The summary below tells the outcome **before importing** — how many conditions, how many missing — and then you click
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
                               QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QSpinBox, QSplitter, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from core.dataset import group_measurements
from core.i18n import tr
from core.importer import apply_profile, preview, sheet_count
from core.profile import ColumnMap, ImportProfile, guess_profile
from . import theme

ROLE_KEYS = ("input", "response", "ignore")                     # i18n: key
ROLE_COLOR = {"input": QColor(theme.ACCENT_SOFT), "response": QColor(theme.OK_SOFT),
              "ignore": QColor(theme.SURFACE)}
TYPE_KEYS = ("continuous", "integer", "categorical")            # i18n: key

PREVIEW_ROWS = 60


def _wraps(label: QLabel) -> QLabel:
    """Wrap, and tell the layout the height that wrapping actually needs.

    Qt asks `heightForWidth()` only when the size policy says to; without it the lines past
    the first are silently cut. Every sentence here is a different length in the two
    languages, so every one of them says to.
    """
    label.setWordWrap(True)
    sp = label.sizePolicy()
    sp.setHeightForWidth(True)
    label.setSizePolicy(sp)
    return label


class ImportWizard(QDialog):
    """Yields (measurements, profile). Cancel makes exec() Rejected."""

    def __init__(self, parent=None, path: str | None = None,
                 profile: ImportProfile | None = None):
        super().__init__(parent)
        self.setWindowTitle(tr("Import data — structure setup"))
        self.resize(1120, 720)

        self.path: str | None = None
        self.keys: list[str] = []
        self.rows: list[dict] = []
        self.profile = profile or ImportProfile()
        self.result_measurements: list[dict] = []
        self._loading = False

        self._build()
        if path:
            self._load_file(path)

    # ── screen ─────────────────────────────────────────────────────
    def _build(self) -> None:
        root = QVBoxLayout(self)

        # row 1: the file
        bar = QHBoxLayout()
        self.path_edit = QLineEdit(readOnly=True,
                                   placeholderText=tr("Choose an Excel (.xlsx) or CSV file"))
        browse = QPushButton(tr("Browse…"))
        browse.clicked.connect(self._browse)
        bar.addWidget(QLabel(tr("File")))
        bar.addWidget(self.path_edit, 1)
        bar.addWidget(browse)

        bar.addSpacing(16)
        bar.addWidget(QLabel(tr("Sheet")))
        self.sheet = QSpinBox(minimum=1, maximum=1)
        self.sheet.valueChanged.connect(self._reload)
        bar.addWidget(self.sheet)

        bar.addSpacing(16)
        bar.addWidget(QLabel(tr("Header row")))
        self.header_row = QSpinBox(
            minimum=0, maximum=50, value=1,
            toolTip=tr("0 means there is no header. Rows up to this one are not read as data."))
        self.header_row.valueChanged.connect(self._refresh)
        bar.addWidget(self.header_row)
        root.addLayout(bar)

        # row 2: original | roles
        split = QSplitter(Qt.Horizontal)

        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.addWidget(_wraps(QLabel(tr("<b>Original preview</b>  <span style='color:{c}'>"
                                      "— exactly as it is in the file</span>",
                                      c=theme.TEXT_MUTED))))
        self.raw = QTableWidget(alternatingRowColors=True)
        self.raw.setEditTriggers(QTableWidget.NoEditTriggers)
        # The left side is the file as it is — a spreadsheet with many columns scrolls,
        # it is not squeezed. Its column headers are still measured.
        self.raw.setProperty("clip_ok", True)
        lv.addWidget(self.raw)
        split.addWidget(left)

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.addWidget(_wraps(QLabel(tr(
            "<b>Assign column meanings</b>  <span style='color:{c}'>— the roles are a "
            "<b>guess</b>. Check that the condition count below matches what you "
            "expect</span>", c=theme.TEXT_MUTED))))
        self.mapper = QTableWidget(0, 6)
        self.mapper.setHorizontalHeaderLabels([tr("column"), tr("sample values"), tr("role"),
                                               tr("name"), tr("unit"), tr("type")])
        self.mapper.verticalHeader().setVisible(False)
        self.mapper.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        rv.addWidget(self.mapper)

        opt = QGroupBox(tr("Reading rules"))
        ov = QVBoxLayout(opt)
        self.inherit = QCheckBox(tr("Blank cells inherit the condition above"))
        self.inherit.setToolTip(tr("For tables where the condition is written only on the first row of its\n"
                                   "block (merged-cell style). A non-numeric value breaks the inheritance."))
        self.inherit.stateChanged.connect(self._refresh)
        self.exclude_zero = QCheckBox(tr("Mark all-zero-response conditions as exclusion candidates"))
        self.exclude_zero.setToolTip(tr("For cases where nothing was really measured — a destroyed sample, say.\n"
                                        "They are marked, not deleted, and reviewable one by one on the Data tab."))
        self.exclude_zero.stateChanged.connect(self._refresh)
        ov.addWidget(self.inherit)
        ov.addWidget(self.exclude_zero)
        rv.addWidget(opt)
        split.addWidget(right)
        split.setSizes([620, 500])
        root.addWidget(split, 1)

        # row 3: outcome summary
        self.summary = _wraps(QLabel(tr("Choose a file and the outcome is previewed here.")))
        self.summary.setStyleSheet(theme.card())
        root.addWidget(self.summary)

        # row 4: buttons
        btm = QHBoxLayout()
        load_p = QPushButton(tr("Load preset…"))
        load_p.setToolTip(tr("Loads a saved column mapping — reuse it on other files "
                             "from the same instrument."))
        load_p.clicked.connect(self._load_preset)
        save_p = QPushButton(tr("Save preset…"))
        save_p.clicked.connect(self._save_preset)
        btm.addWidget(load_p)
        btm.addWidget(save_p)
        btm.addStretch(1)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(tr("Import"))
        self.buttons.button(QDialogButtonBox.Ok).setProperty("primary", True)
        self.buttons.button(QDialogButtonBox.Cancel).setText(tr("Cancel"))
        self.buttons.accepted.connect(self._accept)
        self.buttons.rejected.connect(self.reject)
        btm.addWidget(self.buttons)
        root.addLayout(btm)

    # ── file ───────────────────────────────────────────────────────
    def _browse(self) -> None:
        fn, _ = QFileDialog.getOpenFileName(
            self, tr("Choose a data file"), "",
            tr("Tables (*.xlsx *.csv);;Excel (*.xlsx);;CSV (*.csv)"))
        if fn:
            self._load_file(fn)

    def _load_file(self, path: str) -> None:
        kind = "xlsx" if path.lower().endswith(".xlsx") else "csv"
        try:
            n_sheets = sheet_count(path) if kind == "xlsx" else 1
            self.sheet.setMaximum(max(1, n_sheets))
            self.keys, self.rows = preview(path, kind, self.sheet.value(), PREVIEW_ROWS)
        except Exception as e:                       # noqa: BLE001
            QMessageBox.warning(self, tr("Could not read the file"), str(e))
            return
        self.path = path
        self.path_edit.setText(path)
        self.profile.kind = kind
        self.profile.sheet = self.sheet.value()
        if not self.profile.columns or {c.key for c in self.profile.columns} != set(self.keys):
            header = self._header_values()
            self.profile = guess_profile(kind, header, self.rows[1:], self.keys)
            self.profile.sheet = self.sheet.value()
        self._fill_mapper()
        self._refresh()

    def _reload(self) -> None:
        if self.path:
            self._load_file(self.path)

    def _header_values(self) -> list[str]:
        hr = self.header_row.value()
        if hr <= 0 or hr > len(self.rows):
            return list(self.keys)
        row = self.rows[hr - 1]
        return [str(row.get(k, "") or k) for k in self.keys]

    # ── mapping table ──────────────────────────────────────────────
    def _fill_mapper(self) -> None:
        self._loading = True
        by_key = {c.key: c for c in self.profile.columns}
        self.mapper.setRowCount(len(self.keys))
        header = self._header_values()

        for i, k in enumerate(self.keys):
            col = by_key.get(k) or ColumnMap(key=k)
            sample = [str(r.get(k, "")) for r in self.rows[self.header_row.value():]
                      if r.get(k) not in (None, "")][:3]

            self.mapper.setItem(i, 0, _ro(k))
            self.mapper.setItem(i, 1, _ro(" · ".join(sample) or "—"))

            role = QComboBox()
            for r in ROLE_KEYS:
                role.addItem(tr(r), r)
            role.setCurrentIndex(ROLE_KEYS.index(col.role))
            role.currentIndexChanged.connect(self._on_role_changed)
            self.mapper.setCellWidget(i, 2, role)

            self.mapper.setItem(i, 3, QTableWidgetItem(col.name or header[i]))
            self.mapper.setItem(i, 4, QTableWidgetItem(col.unit))

            vtype = QComboBox()
            for t in TYPE_KEYS:
                vtype.addItem(tr(t), t)
            vtype.setCurrentIndex(TYPE_KEYS.index(col.type))
            vtype.currentIndexChanged.connect(self._refresh)
            self.mapper.setCellWidget(i, 5, vtype)

        self.mapper.resizeColumnsToContents()
        # resizeColumnsToContents measures the cell's item, never the combo box inside it —
        # so the two combo columns are sized from the labels of the language that is on
        fm = self.mapper.fontMetrics()
        self.mapper.setColumnWidth(2, max(fm.horizontalAdvance(tr(r)) for r in ROLE_KEYS) + 64)
        self.mapper.setColumnWidth(5, max(fm.horizontalAdvance(tr(t)) for t in TYPE_KEYS) + 64)
        # What the six columns actually need, in the language that is on. Saying so keeps the
        # splitter from crushing "sample values" to nothing — the preview scrolls, this does not.
        hh = self.mapper.horizontalHeader()
        need = sum(self.mapper.columnWidth(c) if c in (2, 5) else hh.sectionSizeHint(c)
                   for c in range(self.mapper.columnCount()))
        self.mapper.setMinimumWidth(need + 2 * self.mapper.frameWidth()
                                    + self.mapper.verticalScrollBar().sizeHint().width() + 2)
        self.mapper.itemChanged.connect(self._refresh)
        self._loading = False

    def _on_role_changed(self) -> None:
        """There is exactly one response — picking a new one flips the old one to ignore."""
        if self._loading:
            return
        sender = self.sender()
        if sender.currentData() == "response":
            self._loading = True
            for i in range(self.mapper.rowCount()):
                w = self.mapper.cellWidget(i, 2)
                if w is not sender and w.currentData() == "response":
                    w.setCurrentIndex(2)             # ignore
            self._loading = False
        self._refresh()

    def _collect(self) -> ImportProfile:
        cols = []
        for i, k in enumerate(self.keys):
            cols.append(ColumnMap(
                key=k,
                role=self.mapper.cellWidget(i, 2).currentData(),
                name=(self.mapper.item(i, 3).text() if self.mapper.item(i, 3) else "").strip(),
                unit=(self.mapper.item(i, 4).text() if self.mapper.item(i, 4) else "").strip(),
                type=self.mapper.cellWidget(i, 5).currentData(),
            ))
        p = ImportProfile(kind=self.profile.kind, sheet=self.sheet.value(),
                          header_row=self.header_row.value(), columns=cols,
                          inherit_blank=self.inherit.isChecked(),
                          exclude_zero=self.exclude_zero.isChecked(),
                          name=self.profile.name, note=self.profile.note)
        return p

    # ── preview refresh ────────────────────────────────────────────
    def _refresh(self) -> None:
        if self._loading or not self.keys:
            return
        p = self._collect()
        self.profile = p
        self._paint_raw(p)

        errs = p.validate()
        if errs:
            self._say("· " + "\n· ".join(errs), ok=False)
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)
            return

        try:
            ms, rep = apply_profile(self.rows, p)
        except Exception as e:                       # noqa: BLE001
            self._say(str(e), ok=False)
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)
            return

        groups = group_measurements(ms, p.round_digits)
        dead = sum(1 for v in groups.values() if max(v) <= 0) if p.exclude_zero else 0
        reps = sum(1 for v in groups.values() if len(v) > 1)

        note = []
        if len(self.rows) >= PREVIEW_ROWS:
            note.append(tr("note: the preview counts only the first {n} rows. "
                           "Importing reads everything.", n=PREVIEW_ROWS))
        if rep["missing"]:
            note.append(tr("{n} non-numeric responses are skipped (#DIV/0!, blanks and the like).",
                           n=rep["missing"]))
        if rep["skipped"]:
            note.append(tr("{n} rows with no identifiable condition are skipped", n=rep["skipped"])
                        + (tr(" — try turning on blank-cell inheritance.")
                           if not p.inherit_blank else "."))
        if dead:
            note.append(tr("{n} all-zero-response conditions will be marked as exclusion candidates.",
                           n=dead))

        line = tr("<b>{n} conditions</b> · {meas} measurements · {reps} conditions with replicates",
                  n=len(groups) - dead, meas=len(ms), reps=reps)
        if note:
            line += (f"<br><span style='color:{theme.TEXT_MUTED}'>"          # i18n: skip
                     + "<br>".join(note) + "</span>")
        self._say(line, ok=True)
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(bool(groups))

    def _paint_raw(self, p: ImportProfile) -> None:
        role_of = {c.key: c.role for c in p.columns}
        hr = p.header_row
        self.raw.setRowCount(len(self.rows))
        self.raw.setColumnCount(len(self.keys))
        self.raw.setHorizontalHeaderLabels(
            [f"{k}\n{next((c.label for c in p.columns if c.key == k), k)}" for k in self.keys])
        for i, r in enumerate(self.rows):
            for j, k in enumerate(self.keys):
                it = QTableWidgetItem(str(r.get(k, "")))
                it.setBackground(QBrush(ROLE_COLOR[role_of.get(k, "ignore")]))
                it.setForeground(QBrush(QColor(theme.TEXT_FAINT if (hr and i < hr)
                                                else theme.TEXT)))
                self.raw.setItem(i, j, it)
        self.raw.resizeColumnsToContents()

    def _say(self, html: str, ok: bool) -> None:
        self.summary.setText(html)
        self.summary.setStyleSheet(theme.card("ok" if ok else "fail"))

    # ── presets ────────────────────────────────────────────────────
    def _load_preset(self) -> None:
        fn, _ = QFileDialog.getOpenFileName(self, tr("Load preset"), "",
                                            tr("Mapping presets (*.seqmap)"))
        if not fn:
            return
        try:
            p = ImportProfile.load(fn)
        except Exception as e:                       # noqa: BLE001
            QMessageBox.warning(self, tr("Could not read the preset"), str(e))
            return
        missing = [c.key for c in p.columns if c.role != "ignore" and c.key not in self.keys]
        if missing:
            QMessageBox.warning(
                self, tr("Columns do not match"),
                tr("Columns this preset expects are missing from the file: {names}\n"
                   "Check whether column names or positions changed.",
                   names=", ".join(missing)))
            return
        self.profile = p
        self.header_row.setValue(p.header_row)
        self.inherit.setChecked(p.inherit_blank)
        self.exclude_zero.setChecked(p.exclude_zero)
        self._fill_mapper()
        self._refresh()

    def _save_preset(self) -> None:
        p = self._collect()
        errs = p.validate()
        if errs:
            QMessageBox.warning(self, tr("Not ready to save yet"), "\n".join(errs))
            return
        fn, _ = QFileDialog.getSaveFileName(self, tr("Save preset"),
                                            "mapping.seqmap",       # i18n: skip — file name
                                            tr("Mapping presets (*.seqmap)"))
        if not fn:
            return
        p.name = os.path.splitext(os.path.basename(fn))[0]
        p.save(fn)

    # ── confirm ────────────────────────────────────────────────────
    def _accept(self) -> None:
        p = self._collect()
        errs = p.validate()
        if errs:
            QMessageBox.warning(self, tr("Finish the setup first"), "\n".join(errs))
            return
        kind = p.kind
        try:
            _, all_rows = preview(self.path, kind, p.sheet, limit=10 ** 9)
            ms, _ = apply_profile(all_rows, p)
        except Exception as e:                       # noqa: BLE001
            QMessageBox.critical(self, tr("Import failed"), str(e))
            return
        if not ms:
            QMessageBox.warning(self, tr("Nothing to import"),
                                tr("Check the column roles and reading rules."))
            return
        for i, m in enumerate(ms, 1):
            m["id"] = i
        self.result_measurements = ms
        self.profile = p
        self.accept()


def _ro(text: str) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    it.setFlags(Qt.ItemIsEnabled)
    return it
