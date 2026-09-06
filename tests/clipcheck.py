# -*- coding: utf-8 -*-
"""Measure, don't grep: is every piece of text on the screen fully visible?

The English screens shipped with labels cut mid-word ("Hide excluded r", "rtainty σ — darker is
less known") because the layouts had been sized for the shorter Korean strings. A person spots
that only by looking at every tab in both languages at every window size — so this does it
instead: for each visible widget, the width the text needs (font metrics) is compared with the
width the widget got (layout), and a table or page that has grown a horizontal scrollbar is
reported as well. `tests/test_layout.py` runs it over every tab, both languages, two sizes.

A widget where cutting is the design (a table cell elided on purpose) opts out with
`w.setProperty("clip_ok", True)`. A custom-painted widget reports its own text through a
`clipped_texts() -> list[str]` method.
"""
from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import (QAbstractButton, QAbstractScrollArea, QComboBox, QGroupBox, QHeaderView,
                               QLabel, QListWidget, QTableWidget, QTabBar, QWidget)

SLACK = 2          # px — rounding between font metrics and layout


def _ok(w: QWidget) -> bool:
    return bool(w.property("clip_ok"))


def _viewport_of(w: QWidget):
    """The viewport of the nearest scroll area this widget lives in, or None."""
    p = w.parentWidget()
    while p is not None:
        if isinstance(p, QAbstractScrollArea):
            return p.viewport() if p.viewport().isAncestorOf(w) else None    # scroll-bar chrome: None
        p = p.parentWidget()
    return None


def _describe(w: QWidget) -> str:
    text = ""
    for attr in ("text", "title"):
        if callable(getattr(w, attr, None)):
            text = getattr(w, attr)()
            break
    name = type(w).__name__ + (f"#{w.objectName()}" if w.objectName() else "")
    return f"{name} {text[:60]!r}" if text else name


def _check(w: QWidget, win: QWidget) -> list[str]:
    out: list[str] = []
    if isinstance(w, QLabel) and w.text().strip():
        if w.wordWrap():
            need = w.heightForWidth(w.width())
            if need > w.height() + SLACK:
                out.append(f"wrapped text needs {need}px height, has {w.height()}px: {_describe(w)}")
        else:
            need = w.sizeHint().width()
            if need > w.width() + SLACK:
                out.append(f"text needs {need}px, has {w.width()}px: {_describe(w)}")
    elif isinstance(w, QAbstractButton) and w.text().strip():
        need = w.sizeHint().width()
        if need > w.width() + SLACK:
            out.append(f"button needs {need}px, has {w.width()}px: {_describe(w)}")
    elif isinstance(w, QGroupBox) and w.title().strip():
        need = w.fontMetrics().horizontalAdvance(w.title()) + 24
        if need > w.width() + SLACK:
            out.append(f"group title needs {need}px, has {w.width()}px: {_describe(w)}")
    elif isinstance(w, QComboBox) and w.currentText().strip():
        need = w.fontMetrics().horizontalAdvance(w.currentText()) + 34
        if need > w.width() + SLACK:
            out.append(f"combo text needs {need}px, has {w.width()}px: {w.currentText()!r}")
    elif isinstance(w, QTabBar):
        for i in range(w.count()):
            need, have = w.tabSizeHint(i).width(), w.tabRect(i).width()
            if need > have + SLACK:
                out.append(f"tab needs {need}px, has {have}px: {w.tabText(i)!r}")
    elif isinstance(w, QHeaderView) and w.orientation() == Qt.Orientation.Horizontal:
        for i in range(w.count()):
            if w.isSectionHidden(i):
                continue
            need, have = w.sectionSizeHint(i), w.sectionSize(i)
            if need > have + SLACK:
                label = w.model().headerData(i, Qt.Orientation.Horizontal)
                out.append(f"column header needs {need}px, has {have}px: {label!r}")
    elif isinstance(w, QListWidget) and not w.wordWrap() \
            and w.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff:
        need, have = w.sizeHintForColumn(0), w.viewport().width()
        if need > have + SLACK:
            out.append(f"list items need {need}px, have {have}px: {_describe(w)}")
    if isinstance(w, QAbstractScrollArea) and w.horizontalScrollBar().isVisible() \
            and not isinstance(w, QTableWidget):
        out.append(f"horizontal scrollbar: {_describe(w)}")
    if isinstance(w, QTableWidget) and w.horizontalScrollBar().isVisible():
        out.append(f"table wider than its viewport ({w.horizontalHeader().length()}px in "
                   f"{w.viewport().width()}px): {_describe(w)}")
    # pushed out of the window / out of its viewport to the right
    bound = _viewport_of(w) or win
    right = w.mapTo(bound, QPoint(w.width(), 0)).x()
    if right > bound.width() + SLACK and w.width() > 0:
        out.append(f"extends {right - bound.width()}px past the right edge: {_describe(w)}")
    return out


def _figure_clipped(canvas) -> list[str]:
    """Matplotlib: titles and axis labels inside the figure and no wider than their own axes."""
    out: list[str] = []
    fig = canvas.figure
    canvas.draw()
    renderer = canvas.get_renderer()
    fw, fh = fig.bbox.width, fig.bbox.height
    for ax in fig.axes:
        abox = ax.get_window_extent(renderer)
        for what, artist in (("title", ax.title), ("xlabel", ax.xaxis.label), ("ylabel", ax.yaxis.label)):
            text = artist.get_text()
            if not text.strip():
                continue
            box = artist.get_window_extent(renderer)
            if box.x0 < -SLACK or box.x1 > fw + SLACK or box.y0 < -SLACK or box.y1 > fh + SLACK:
                out.append(f"figure {what} outside the figure: {text!r}")
            elif what == "title" and box.width > abox.width * 1.02 + SLACK and len(fig.axes) > 1:
                out.append(f"figure title wider than its panel ({box.width:.0f}px > {abox.width:.0f}px): {text!r}")
        legend = ax.get_legend()
        if legend is not None and legend.get_visible():
            box = legend.get_window_extent(renderer)
            if box.x0 < -SLACK or box.x1 > fw + SLACK or box.y0 < -SLACK or box.y1 > fh + SLACK:
                out.append(f"legend outside the figure in panel {ax.get_title()!r}")
    for text in fig.texts:
        if text.get_text().strip():
            box = text.get_window_extent(renderer)
            if box.x0 < -SLACK or box.x1 > fw + SLACK:
                out.append(f"figure text outside the figure: {text.get_text()!r}")
    return out


def clipped_texts(win: QWidget) -> list[str]:
    """Every clipped piece of text in the shown window right now — empty means all text is visible."""
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    out: list[str] = []
    for w in win.findChildren(QWidget):
        if not w.isVisible() or _ok(w):
            continue
        if hasattr(w, "clipped_texts"):
            out += w.clipped_texts()
            continue
        if isinstance(w, FigureCanvasQTAgg):
            out += _figure_clipped(w)
            continue
        out += _check(w, win)
    return out
