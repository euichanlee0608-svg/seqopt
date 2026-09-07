# -*- coding: utf-8 -*-
"""Tab 6, Report — PDF · calculation log · reproduction script (F-40 ~ F-43).

**A report is a copy of the evidence, not a photo of the screen.** It carries
not just the verdict but the entire calculation that produced it (principle P4).

`core/report.py` does the making. This screen is only buttons and a preview.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QMessageBox,
                               QPlainTextEdit, QPushButton, QVBoxLayout, QWidget)

from core.i18n import tr
from core.report import ReportData, calculation_log, reproduce_script, write_pdf
from . import theme
from .widgets.section import PageHeader, Section


class _Signals(QObject):
    done = Signal(object)
    failed = Signal(str)


class _BuildJob(QRunnable):
    """Report computation includes LOOCV and takes a while — never freeze the screen."""

    def __init__(self, project, bypassed: bool):
        super().__init__()
        self.project = project
        self.bypassed = bypassed
        self.signals = _Signals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.done.emit(ReportData.compute(self.project, self.bypassed))
        except Exception as e:                   # noqa: BLE001
            self.signals.failed.emit(str(e))


class ReportTab(QWidget):
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.data: ReportData | None = None
        self.gate_bypassed = False
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        head = PageHeader(tr("Report — leave the whole evidence trail"),
                          tr("Exports the gate verdict, calculation log, figures and raw-data "
                             "summary as PDF and text — plus a script that reproduces the same numbers."))
        self.build = QPushButton(tr("Build report"))
        self.build.setProperty("primary", True)
        self.build.clicked.connect(self.rebuild)
        head.add_right(self.build)
        root.addWidget(head)

        self.status = QLabel(tr("Press \"Build report\" to assemble the full evidence "
                                "from the current data."))
        self.status.setWordWrap(True)
        # a wrapping label only gets the height its text needs if it asks for it
        sp = self.status.sizePolicy()
        sp.setHeightForWidth(True)
        self.status.setSizePolicy(sp)
        self.status.setStyleSheet(theme.card())
        root.addWidget(self.status)

        out = Section(tr("Export"))
        ov = QHBoxLayout()
        self.pdf = QPushButton(tr("PDF report"))
        self.pdf.setToolTip(tr("Gate verdict + calculation log + figures + raw-data summary.\n"
                               "Embeds the font, so it renders the same on any PC."))
        self.pdf.clicked.connect(self._save_pdf)
        self.log = QPushButton(tr("Calculation log (txt)"))
        self.log.setToolTip(tr("Every number's formula and intermediate values. Followable by hand."))
        self.log.clicked.connect(self._save_log)
        self.script = QPushButton(tr("Reproduction script (py)"))
        self.script.setToolTip(tr("This one file reproduces the same numbers."))
        self.script.clicked.connect(self._save_script)
        for w in (self.pdf, self.log, self.script):
            ov.addWidget(w)
        ov.addStretch(1)
        out.add_layout(ov)
        root.addWidget(out)

        root.addWidget(QLabel(theme.heading(tr("Calculation-log preview"))))
        self.preview = QPlainTextEdit(readOnly=True)
        self.preview.setStyleSheet(f"font-family:{theme.MONO_FAMILY}; font-size:12px;")
        root.addWidget(self.preview, 1)

        self._set_enabled(False)

    # ── state ──────────────────────────────────────────────────────
    def set_bypassed(self, bypassed: bool) -> None:
        """A forced run on the Recommend tab leaves its mark on the report (§10 risk table)."""
        self.gate_bypassed = bypassed

    def _set_enabled(self, on: bool) -> None:
        for w in (self.pdf, self.log, self.script):
            w.setEnabled(on)

    def rebuild(self) -> None:
        if not self.project.measurements:
            QMessageBox.warning(self, tr("No measurements"), tr("Enter values on the Data tab first."))
            return
        self.build.setEnabled(False)
        self.status.setText(tr("Computing… (includes learnability LOOCV, so many conditions "
                               "take tens of seconds)"))
        job = _BuildJob(self.project, self.gate_bypassed)
        job.signals.done.connect(self._on_done)
        job.signals.failed.connect(self._on_failed)
        QThreadPool.globalInstance().start(job)

    def _on_done(self, data: ReportData) -> None:
        self.data = data
        self.build.setEnabled(True)
        self._set_enabled(True)
        self.preview.setPlainText(calculation_log(data))
        g = data.gate
        # "LOCKED" · "available" · "recommendation" · "REQUIREMENTS UNMET" are the report's own
        # words (core/lang/ko_report.py) — the screen says exactly what the PDF will say.
        head = tr("<b>Ready.</b> {n} usable conditions · {m} measurements · {what} {verdict}",
                  n=data.dataset.n_conditions, m=data.dataset.n_measurements,
                  what=tr("recommendation"),
                  verdict=tr("LOCKED") if g.locked else tr("available"))
        if data.gate_bypassed:
            head += (f"<br><b style='color:{theme.FAIL}'>"                                # i18n: skip
                     + tr("Requirements unmet — the PDF cover and every page "
                          "get a \"{stamp}\" stamp.", stamp=tr("REQUIREMENTS UNMET"))
                     + "</b>")
        self.status.setText(head)
        self.status.setStyleSheet(theme.card("fail" if data.gate_bypassed else "ok"))

    def _on_failed(self, msg: str) -> None:
        self.build.setEnabled(True)
        self.status.setText(tr("Could not build the report — {why}", why=msg))
        self.status.setStyleSheet(theme.card("fail"))

    # ── export ─────────────────────────────────────────────────────
    def _ask(self, default: str, filt: str) -> str | None:
        fn, _ = QFileDialog.getSaveFileName(self, tr("Save"), default, filt)
        return fn or None

    def _save_pdf(self) -> None:
        if self.data is None:
            return
        fn = self._ask(f"{self.project.name}_report.pdf", tr("PDF (*.pdf)"))
        if not fn:
            return
        try:
            write_pdf(self.data, fn)
        except Exception as e:                   # noqa: BLE001
            QMessageBox.critical(self, tr("Could not build the PDF"), str(e))
            return
        QMessageBox.information(self, tr("Saved"), fn)

    def _save_log(self) -> None:
        if self.data is None:
            return
        fn = self._ask(f"{self.project.name}_calculation_log.txt", tr("Text (*.txt)"))
        if fn:
            Path(fn).write_text(calculation_log(self.data), encoding="utf-8")
            QMessageBox.information(self, tr("Saved"), fn)

    def _save_script(self) -> None:
        if self.data is None:
            return
        fn = self._ask(f"{self.project.name}_reproduce.py", tr("Python (*.py)"))
        if fn:
            Path(fn).write_text(reproduce_script(self.data), encoding="utf-8")
            QMessageBox.information(
                self, tr("Saved"),
                tr("{path}\n\nRun `python {name}` inside the seqopt folder\n"
                   "and the report's numbers come out again.", path=fn, name=Path(fn).name))
