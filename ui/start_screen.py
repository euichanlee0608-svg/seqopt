# -*- coding: utf-8 -*-
"""Start screen — where you choose what to do when the program opens.

**Why it exists**

The program used to open on an empty table and a red error ("define at least
one input variable"). A screen that scolds you before you have done anything,
and never says what to click.

Borrowed from commercial tools
  · **JMP's Sample Data Library** — a first-time user has never seen the tool
    "working properly". One-click examples beat any manual.
  · **The start pages of Isight / modeFRONTIER** — new / open / recent, three ways in.
  · **Design-Expert's linear flow** — the screen decides what comes next.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QSizePolicy, QVBoxLayout, QWidget)

from . import theme
from .resources import example_dir, icon_path

EXAMPLE_DIR = example_dir()
APP_VERSION = "1.0"


class _Card(QFrame):
    """One big button. Title · description · click."""

    clicked = Signal()

    def __init__(self, title: str, desc: str, primary: bool = False, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        tone = theme.ACCENT if primary else theme.BORDER
        self.setStyleSheet(
            f"QFrame{{background:{theme.BG}; border:1px solid {tone};"
            f"border-radius:10px; padding:2px;}}"
            f"QFrame:hover{{background:{theme.SURFACE}; border-color:{theme.ACCENT};}}")
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(4)
        t = QLabel(title)
        t.setStyleSheet(f"font-size:{theme.H2 + 1}px; font-weight:600; border:0;"
                        f"color:{theme.ACCENT if primary else theme.TEXT};")
        d = QLabel(desc)
        d.setWordWrap(True)
        d.setStyleSheet(f"border:0; color:{theme.TEXT_MUTED};")
        v.addWidget(t)
        v.addWidget(d)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


def _clean_recents(paths: list[str]) -> list[str]:
    """Only files that exist, each once, and no single-letter junk names."""
    seen, out = set(), []
    for p in paths:
        path = Path(p)
        key = str(path.resolve()) if path.exists() else None
        if key is None or key in seen or len(path.stem) < 2:
            continue
        seen.add(key)
        out.append(str(path))
    return out


class StartScreen(QWidget):
    """New project / open example / open file / recent files."""

    new_project = Signal()
    open_file = Signal()
    open_path = Signal(str)

    def __init__(self, recents: list[str] | None = None, parent=None):
        super().__init__(parent)
        self._build(recents or [])

    def _build(self, recents: list[str]) -> None:
        outer = QHBoxLayout(self)
        outer.addStretch(1)

        col = QVBoxLayout()
        col.setSpacing(14)
        col.addStretch(1)

        brand = QHBoxLayout()
        brand.setSpacing(16)
        logo = QLabel()
        pix = QPixmap(str(icon_path()))
        if not pix.isNull():
            logo.setPixmap(pix.scaled(QSize(64, 64), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        brand.addWidget(logo, 0, Qt.AlignTop)
        tcol = QVBoxLayout()
        tcol.setSpacing(2)
        title = QLabel(f"seqopt  <span style='font-size:{theme.SMALL}px; font-weight:400;"
                       f"color:{theme.TEXT_FAINT}'>v{APP_VERSION}</span>")
        title.setStyleSheet(f"font-size:32px; font-weight:700; color:{theme.TEXT};")
        sub = QLabel("Enter your measurements and it tells you what to measure next —\n"
                     "and whether that advice can be trusted at all.")
        sub.setStyleSheet(f"font-size:{theme.FONT_SIZE}px; color:{theme.TEXT_MUTED};")
        tcol.addWidget(title)
        tcol.addWidget(sub)
        brand.addLayout(tcol, 1)
        col.addLayout(brand)
        col.addSpacing(10)

        new = _Card("Start a new project",
                    "Define your variables and objective, then draw the first measurement points.",
                    primary=True)
        new.clicked.connect(self.new_project)
        col.addWidget(new)

        examples = sorted(EXAMPLE_DIR.glob("*.seqopt")) if EXAMPLE_DIR.is_dir() else []
        if examples:
            ex = _Card("Open the example  —  P3HT:CNT conductivity",
                       "Real published measurements of a thin-film composite "
                       "(<i>Adv. Funct. Mater.</i> 2021, public dataset). Watch the gate "
                       "pass and a recommendation come out — or lock, once you thin the data.")
            ex.clicked.connect(lambda: self.open_path.emit(str(examples[0])))
            col.addWidget(ex)

        op = _Card("Open a saved project", "Open a .seqopt file you made earlier.")
        op.clicked.connect(self.open_file)
        col.addWidget(op)

        recents = _clean_recents(recents)
        if recents:
            col.addSpacing(6)
            lab = QLabel("Recent files")
            theme.set_role(lab, "desc")
            col.addWidget(lab)
            lst = QListWidget()
            lst.setFixedHeight(min(4, len(recents)) * 34 + 10)
            lst.setFocusPolicy(Qt.NoFocus)                   # removes the dotted current-item outline
            lst.setStyleSheet(
                f"QListWidget{{border:1px solid {theme.BORDER}; border-radius:8px;"
                f"background:{theme.BG}; outline:0;}}"
                f"QListWidget::item{{padding:7px 12px; border:0;}}"
                f"QListWidget::item:hover{{background:{theme.SURFACE};}}"
                f"QListWidget::item:selected{{background:{theme.ACCENT_SOFT}; color:{theme.TEXT};}}")
            for path in recents[:4]:
                p = Path(path)
                it = QListWidgetItem(f"{p.stem}   —   {p.parent.name}")
                it.setToolTip(path)
                it.setData(Qt.UserRole, path)
                lst.addItem(it)
            lst.itemClicked.connect(lambda i: self.open_path.emit(i.data(Qt.UserRole)))
            col.addWidget(lst)

        col.addSpacing(8)
        hint = QLabel("First time here? Open the <b>example</b> — it is the fastest way "
                      "to see what each screen is telling you.")
        hint.setWordWrap(True)
        hint.setStyleSheet(theme.card("info"))
        col.addWidget(hint)
        col.addStretch(2)

        wrap = QWidget()
        wrap.setLayout(col)
        wrap.setFixedWidth(560)
        outer.addWidget(wrap)
        outer.addStretch(1)
