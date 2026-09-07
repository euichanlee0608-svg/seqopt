# -*- coding: utf-8 -*-
"""The two skeleton pieces of a screen — the page title (PageHeader) and the card (Section).

**Why not QGroupBox**

A QGroupBox title is small text perched on the border line. Stack three or four
cards and the titles sink into the borders — users reported "the tabs are small
and hard to see". Commercial tools (JMP, Minitab) put a bold title plus a
one-line description inside the card, with a "why?" link at the top right.
This reproduces that shape.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from .. import theme


class PageHeader(QWidget):
    """Top of a screen — big title + one-line description + a link slot on the right."""

    def __init__(self, title: str, desc: str = "", parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        col = QVBoxLayout()
        col.setSpacing(2)
        self.title = QLabel(title)
        theme.set_role(self.title, "h1")
        self.desc = QLabel(desc)
        self.desc.setWordWrap(True)
        theme.set_role(self.desc, "desc")
        col.addWidget(self.title)
        col.addWidget(self.desc)
        self.desc.setVisible(bool(desc))
        row.addLayout(col, 1)
        self.right = QHBoxLayout()
        self.right.setSpacing(10)
        row.addLayout(self.right)

    def add_right(self, widget: QWidget) -> None:
        self.right.addWidget(widget, 0, Qt.AlignTop)


class Section(QFrame):
    """One card — title · description · body. Put widgets into `body`."""

    def __init__(self, title: str, desc: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("card", True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(10)
        tcol = QVBoxLayout()
        tcol.setSpacing(2)
        self.title = QLabel(title)
        theme.set_role(self.title, "h2")
        self.desc = QLabel(desc)
        self.desc.setWordWrap(True)
        theme.set_role(self.desc, "desc")
        self.desc.setVisible(bool(desc))
        tcol.addWidget(self.title)
        tcol.addWidget(self.desc)
        head.addLayout(tcol, 1)
        self.head_right = QHBoxLayout()
        self.head_right.setSpacing(8)
        head.addLayout(self.head_right)
        outer.addLayout(head)

        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        outer.addLayout(self.body)

        # Height-for-width, or the description loses its last line. A card used to be
        # QSizePolicy.Maximum vertically, which caps it at its own sizeHint — and a sizeHint
        # is measured at the width Qt *wants*, not the narrower width the card actually gets.
        # Wrapped prose then needs more lines than the cap allows and the bottom one is cut.
        sp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)
        dsp = self.desc.sizePolicy()
        dsp.setHeightForWidth(True)
        self.desc.setSizePolicy(dsp)

    def add(self, widget: QWidget, stretch: int = 0) -> None:
        self.body.addWidget(widget, stretch)

    def add_layout(self, layout) -> None:
        self.body.addLayout(layout)

    def add_link(self, button) -> None:
        """The top-right link button ("why?")."""
        self.head_right.addWidget(button, 0, Qt.AlignTop)

    def set_desc(self, text: str) -> None:
        self.desc.setText(text)
        self.desc.setVisible(bool(text))


def link_button(text: str, parent=None):
    """A text-only blue link button. Clicking it never disturbs the layout."""
    from PySide6.QtWidgets import QToolButton
    b = QToolButton(parent)
    b.setText(text)
    b.setProperty("link", True)
    b.setCursor(Qt.PointingHandCursor)
    b.setFocusPolicy(Qt.NoFocus)
    return b
