# -*- coding: utf-8 -*-
"""The left step rail — numbered circle · name · state (done ✓ / locked).

**Why plain QListWidget text was not enough**

It used to be one line of text like "1  Setup". Which steps were finished,
where you should be now, and why something would not click — all of it rode on
a single text color, and users said "the tabs are hard to see". Like
Design-Expert's left rail, **the numbered circle does the talking.**

    ✓ green   finished          ● blue   where you should be now
    ○ gray    can be opened     ─ dim    not yet available (the tooltip says why)
"""
from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QStyle, QStyledItemDelegate

from core.i18n import tr
from .. import theme

ITEM_H = 44
ROLE_STATE = Qt.UserRole + 1     # "done" | "next" | "ready" | "locked"
ROLE_NUM = Qt.UserRole + 2       # "1" … "6" · "?"


class _Delegate(QStyledItemDelegate):
    def sizeHint(self, option, index) -> QSize:            # noqa: N802
        return QSize(option.rect.width(), ITEM_H)

    def paint(self, p: QPainter, option, index) -> None:
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        r: QRect = option.rect.adjusted(0, 0, 0, -3)
        state = index.data(ROLE_STATE) or "ready"
        num = index.data(ROLE_NUM) or ""
        selected = bool(option.state & QStyle.State_Selected)
        hovered = bool(option.state & QStyle.State_MouseOver)
        enabled = bool(option.state & QStyle.State_Enabled)

        # background
        if selected:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(theme.ACCENT_SOFT))
            p.drawRoundedRect(r, 8, 8)
            p.setBrush(QColor(theme.ACCENT))
            p.drawRoundedRect(QRect(r.left(), r.top() + 8, 3, r.height() - 16), 1.5, 1.5)
        elif hovered and enabled:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(theme.NAV_HOVER))
            p.drawRoundedRect(r, 8, 8)

        # numbered circle
        d = 24
        circle = QRect(r.left() + 12, r.top() + (r.height() - d) // 2, d, d)
        if state == "done":
            fill, edge, glyph, glyph_color = theme.OK_SOFT, theme.OK_SOFT, "✓", theme.OK
        elif state == "next" or selected:
            fill, edge, glyph, glyph_color = theme.ACCENT, theme.ACCENT, num, theme.BG
        elif state == "locked":
            fill, edge, glyph, glyph_color = "transparent", theme.NAV_LOCKED, num, theme.NAV_LOCKED
        else:
            fill, edge, glyph, glyph_color = theme.BG, theme.BORDER_STRONG, num, theme.TEXT_MUTED
        p.setPen(QPen(QColor(edge), 1.2))
        p.setBrush(QColor(fill) if fill != "transparent" else Qt.NoBrush)
        p.drawEllipse(circle)
        f = QFont(option.font)
        f.setPixelSize(12)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(glyph_color))
        p.drawText(circle, Qt.AlignCenter, glyph)

        # name
        f2 = QFont(option.font)
        f2.setPixelSize(theme.FONT_SIZE)
        f2.setBold(selected)
        p.setFont(f2)
        if state == "locked":
            color = theme.NAV_LOCKED
        elif selected:
            color = theme.ACCENT
        else:
            color = theme.TEXT
        p.setPen(QColor(color))
        text_rect = QRect(circle.right() + 12, r.top(), r.width() - d - 36, r.height())
        p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, index.data(Qt.DisplayRole) or "")

        # right-hand state tag
        tag = {"locked": tr("locked"), "next": tr("next")}.get(state, "")
        if tag and not selected:
            f3 = QFont(option.font)
            f3.setPixelSize(11)
            p.setFont(f3)
            p.setPen(QColor(theme.ACCENT if state == "next" else theme.NAV_LOCKED))
            p.drawText(r.adjusted(0, 0, -12, 0), Qt.AlignVCenter | Qt.AlignRight, tag)
        p.restore()


class NavList(QListWidget):
    """The step list. `set_state(row, state)` changes the circle's look."""

    def __init__(self, labels: list[tuple[str, str]], parent=None):
        super().__init__(parent)
        self.setObjectName("nav")
        self.setFixedWidth(theme.NAV_WIDTH)
        self.setItemDelegate(_Delegate(self))
        self.setMouseTracking(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setUniformItemSizes(True)
        for num, label in labels:
            it = QListWidgetItem(label)
            it.setData(ROLE_NUM, num)
            it.setData(ROLE_STATE, "ready")
            it.setSizeHint(QSize(theme.NAV_WIDTH - 16, ITEM_H))
            self.addItem(it)

    def clipped_texts(self) -> list[str]:
        """Step names that do not fit — the layout gate reads this (tests/clipcheck.py).

        The delegate paints the name itself, and every item's sizeHint is the full row width,
        so measuring the list the ordinary way can never see a name cut. The room the delegate
        leaves is the row minus the numbered circle and its gaps (see `_Delegate.paint`).
        """
        fm = QFontMetrics(self.font())
        room = self.viewport().width() - 60
        return [f"step name does not fit: {t!r}"                      # i18n: skip (a test report)
                for t in (self.item(i).text() for i in range(self.count()))
                if fm.horizontalAdvance(t) > room]

    def set_state(self, row: int, state: str) -> None:
        it = self.item(row)
        if it is not None and it.data(ROLE_STATE) != state:
            it.setData(ROLE_STATE, state)
