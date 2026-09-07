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
        # a title that cannot wrap sets the page's minimum width — and the English
        # titles are the long ones
        self.title = wrapping(QLabel(title))
        theme.set_role(self.title, "h1")
        self.desc = wrapping(QLabel(desc))
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
        self.title = wrapping(QLabel(title))
        theme.set_role(self.title, "h2")
        self.desc = wrapping(QLabel(desc))
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

        # Height-for-width, or the description loses its last line (see tell_true_height).
        tell_true_height(self)

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


def tell_true_height(w: QWidget) -> QWidget:
    """Let `w` tell its layout the height it needs **at the width it actually gets**.

    A word-wrapped label's sizeHint is measured at the width Qt would like to give it; hand it
    less and the lines past the first are simply cut off, because Qt asks `heightForWidth()`
    only when the size policy says to. Korean and English wrap at different points, so every
    wrapping label — and every card holding one — says to. A card used to be
    QSizePolicy.Maximum vertically, which caps it at its own sizeHint, measured before the
    text has wrapped; a card that must grow a line has to give that cap up.
    """
    sp = w.sizePolicy()
    sp.setHeightForWidth(True)
    if sp.verticalPolicy() == QSizePolicy.Maximum:
        sp.setVerticalPolicy(QSizePolicy.Preferred)
    w.setSizePolicy(sp)
    return w


def wrapping(label: QLabel) -> QLabel:
    """A label that wraps **and says so to its layout** — `setWordWrap` alone is not enough."""
    label.setWordWrap(True)
    return tell_true_height(label)


def link_button(text: str, parent=None):
    """A text-only blue link button. Clicking it never disturbs the layout."""
    from PySide6.QtWidgets import QToolButton
    b = QToolButton(parent)
    b.setText(text)
    b.setProperty("link", True)
    b.setCursor(Qt.PointingHandCursor)
    b.setFocusPolicy(Qt.NoFocus)
    return b
