# -*- coding: utf-8 -*-
"""Discriminability gauge — where D sits, at a glance.

The bare number "D = 1.03 [0.49, 1.80]" tells a newcomer nothing. Four zones
(indistinguishable · borderline · usable · comfortable) are painted, the point
estimate is a vertical line, and the 95% interval is a horizontal bracket. A
bracket straddling the gate line (1.0) IS the "undecided" verdict, visually.
Zone boundaries and their basis come from core.diagnostics.D_LEVELS alone.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from core.diagnostics import D_COMFORTABLE, D_RECOMMENDED, D_THRESHOLD
from core.i18n import tr
from .. import theme

# The zone names are translation keys — tr() runs when the gauge paints, not at import time.
ZONES = [(0.0, D_THRESHOLD, theme.ZONE_BAD, "indistinguishable"),      # i18n: key
         (D_THRESHOLD, D_RECOMMENDED, theme.ZONE_EDGE, "borderline"),  # i18n: key
         (D_RECOMMENDED, D_COMFORTABLE, theme.ZONE_GOOD, "usable"),    # i18n: key
         (D_COMFORTABLE, None, theme.ZONE_BEST, "comfortable")]        # i18n: key

BAR_Y, BAR_H = 40, 16
TICK_Y = BAR_Y + BAR_H + 2          # the boundary numbers, right under the bar they belong to
NAME_Y = TICK_Y + 18                # the zone legend below them, on as many rows as it needs
LINE_H = 16
SWATCH = 9                          # the colour chip in front of a zone name


class DGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = None
        self.lo = None
        self.hi = None
        self.setMinimumHeight(NAME_Y + 2 * LINE_H + 2)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_value(self, value, lo=None, hi=None) -> None:
        self.value, self.lo, self.hi = value, lo, hi
        self.update()

    def _xmax(self) -> float:
        top = max(4.5, (self.hi or 0) + 0.4, (self.value or 0) + 0.6)
        return min(top, 12.0)

    def _zone_labels(self) -> list[tuple[str, str, str, QRectF]]:
        """(shown text, full text, colour, where) for the four zone names — a wrapped legend.

        The names used to sit under their own band, which only works while the bands are wide:
        a large D stretches the axis to 11, squeezing 0…3.5 into a fifth of the bar, and
        "indistinguishable" no longer has anywhere to go (Korean is half the length, so it read
        fine there and was cut in English). A legend under the bar is decided by the text alone
        — swatch, name, next — and wraps to another row rather than overrunning.
        """
        fm = QFontMetrics(self._small_font())
        left, right = 12, self.width() - 12
        x, row = left, 0
        out = []
        for _lo, _hi, colour, name in ZONES:
            text = tr(name)
            room = right - left - SWATCH - 4
            shown = text if fm.horizontalAdvance(text) <= room else \
                fm.elidedText(text, Qt.ElideRight, int(room))
            w = SWATCH + 4 + fm.horizontalAdvance(shown)
            if x > left and x + w > right:
                x, row = left, row + 1
            out.append((shown, text, colour, QRectF(x, NAME_Y + row * LINE_H, w, LINE_H)))
            x += w + 14
        return out

    def _fit_rows(self) -> None:
        """Reserve the height the legend really needs (it wraps differently per language/width)."""
        rows = int(max(r.y() for _s, _f, _c, r in self._zone_labels()) - NAME_Y) // LINE_H + 1
        want = NAME_Y + rows * LINE_H + 2
        if self.minimumHeight() != want:
            self.setMinimumHeight(want)
            self.updateGeometry()

    def resizeEvent(self, event) -> None:                      # noqa: N802
        super().resizeEvent(event)
        self._fit_rows()

    def _small_font(self) -> QFont:
        f = QFont(self.font())
        f.setPixelSize(theme.SMALL - 1)
        return f

    def clipped_texts(self) -> list[str]:
        """What this widget paints that does not fit — the layout gate reads this (tests/clipcheck.py)."""
        out = []
        for shown, full, _colour, rect in self._zone_labels():
            if shown != full:
                out.append(f"zone name elided: {full!r} shown as {shown!r}")   # i18n: skip (a test report)
            if rect.bottom() > self.height():
                out.append(f"zone name below the widget: {full!r}")            # i18n: skip (a test report)
        if self.value is not None:
            fm = QFontMetrics(self._value_font())
            if fm.horizontalAdvance(self._value_text()) > self.width() - 24:
                out.append(f"D value does not fit: {self._value_text()!r}")   # i18n: skip (a test report)
        return out

    def _value_font(self) -> QFont:
        f = QFont(self.font())
        f.setPixelSize(theme.FONT_SIZE)
        f.setBold(True)
        return f

    def _value_text(self) -> str:
        label = f"D = {self.value:.2f}"                       # i18n: skip (a symbol and its number)
        if self.lo is not None:
            label += f"   [{self.lo:.2f}, {self.hi:.2f}]"     # i18n: skip (an interval of numbers)
        return label

    def paintEvent(self, event) -> None:                       # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        left, right = 12, w - 12
        bar_y, bar_h = BAR_Y, BAR_H
        xmax = self._xmax()

        def X(v: float) -> float:
            return left + (right - left) * min(v, xmax) / xmax

        p.setFont(self._small_font())

        # zone bands
        for lo, hi, colour, _name in ZONES:
            x0, x1 = X(lo), X(hi if hi is not None else xmax)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(colour))
            p.drawRect(QRectF(x0, bar_y, x1 - x0, bar_h))

        # boundary ticks
        p.setPen(QPen(QColor(theme.TEXT_MUTED), 1))
        for v in (D_THRESHOLD, D_RECOMMENDED, D_COMFORTABLE):
            x = X(v)
            p.drawLine(int(x), bar_y - 3, int(x), bar_y + bar_h + 3)
            p.drawText(QRectF(x - 24, TICK_Y, 48, LINE_H), Qt.AlignHCenter | Qt.AlignTop, f"{v:g}")
        p.drawText(QRectF(left - 10, TICK_Y, 30, LINE_H), Qt.AlignHCenter | Qt.AlignTop, "0")

        # the legend: what each colour means, wrapped to as many rows as the names need
        names = self._zone_labels()
        for shown, _full, colour, rect in names:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(colour))
            p.drawRect(QRectF(rect.x(), rect.y() + 4, SWATCH, SWATCH))
            p.setPen(QColor(theme.TEXT_MUTED))
            p.drawText(QRectF(rect.x() + SWATCH + 4, rect.y(), rect.width(), rect.height()),
                       Qt.AlignLeft | Qt.AlignTop, shown)
        self.setToolTip(" · ".join(full for _s, full, _c, _r in names))  # i18n: skip (built from tr()'d names)

        if self.value is None:
            p.setPen(QColor(theme.TEXT_FAINT))
            p.drawText(QRectF(left, 8, right - left, 22), Qt.AlignLeft | Qt.AlignVCenter,
                       tr("Replicate measurements are needed to compute D"))
            return

        # 95% interval bracket
        if self.lo is not None and self.hi is not None:
            x0, x1 = X(self.lo), X(self.hi)
            pen = QPen(QColor(theme.TEXT), 2)
            p.setPen(pen)
            y = bar_y - 12
            p.drawLine(int(x0), y, int(x1), y)
            p.drawLine(int(x0), y - 5, int(x0), y + 5)
            p.drawLine(int(x1), y - 5, int(x1), y + 5)

        # point-estimate line + value
        x = X(self.value)
        p.setPen(QPen(QColor(theme.TEXT), 2.5))
        p.drawLine(int(x), bar_y - 14, int(x), bar_y + bar_h + 2)
        bold = self._value_font()
        p.setFont(bold)
        p.setPen(QColor(theme.TEXT))
        label = self._value_text()
        tw = QFontMetrics(bold).horizontalAdvance(label) + 8      # the text's own width, not a guess
        tx = min(max(left, x - tw / 2), max(left, right - tw))
        p.drawText(QRectF(tx, 4, tw, 20), Qt.AlignHCenter | Qt.AlignVCenter, label)
