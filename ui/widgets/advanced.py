# -*- coding: utf-8 -*-
"""The "Advanced" fold — the place for what can be chosen but **does not have to be.**

**Design principle — defer choices instead of deleting them**

Competing tools make the user pick surrogate, acquisition, solver and selection
strategy from dropdowns (AutoOED has four). They removed the coding but
**kept every concept on the user's plate.**

This tool goes the other way: it runs on one set of defaults, and the help
explains why those defaults. Deferral is affordable **because the gate
exists** — when the data is bad, the user does not have to wander through
models, because the tool rules "changing the model will not help."

Unfolding tells you in one line what would change. A box that is merely
labeled "Advanced" tells you nothing even after you open it.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QToolButton, QVBoxLayout, QWidget

from .. import theme


class Advanced(QWidget):
    """Folds away settings whose defaults are enough. Closed by default."""

    def __init__(self, summary: str = "", label: str = "Advanced", parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 0)
        root.setSpacing(4)

        self.toggle = QToolButton(text=f"{label}  ▸", checkable=True)
        self.toggle.setCursor(Qt.PointingHandCursor)
        self.toggle.setStyleSheet(
            f"QToolButton{{border:none; color:{theme.TEXT_MUTED}; padding:2px 0;}}"
            f"QToolButton:hover{{color:{theme.ACCENT};}}")
        self.toggle.toggled.connect(self._on_toggle)
        root.addWidget(self.toggle, alignment=Qt.AlignLeft)

        self.summary = QLabel(summary)
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet(theme.faint())
        self.summary.setVisible(bool(summary))
        root.addWidget(self.summary)

        self.body = QFrame()
        self.body.setStyleSheet(
            f"QFrame{{background:{theme.SURFACE}; border:1px solid {theme.BORDER};"
            f"border-radius:6px;}}")
        self.body.setVisible(False)
        self.inner = QVBoxLayout(self.body)
        self.inner.setContentsMargins(12, 10, 12, 10)
        root.addWidget(self.body)

        self._label = label

    def add(self, widget) -> None:
        self.inner.addWidget(widget)

    def add_layout(self, layout) -> None:
        self.inner.addLayout(layout)

    def _on_toggle(self, on: bool) -> None:
        self.body.setVisible(on)
        self.toggle.setText(f"{self._label}  {'▾' if on else '▸'}")
        self.summary.setVisible(bool(self.summary.text()) and not on)

    def set_summary(self, text: str) -> None:
        """Says, while folded, which values it is currently running on."""
        self.summary.setText(text)
        self.summary.setVisible(bool(text) and not self.toggle.isChecked())
