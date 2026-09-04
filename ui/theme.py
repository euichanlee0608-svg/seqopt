# -*- coding: utf-8 -*-
"""Single source of truth for the screen design — colors, fonts, spacing, widget shapes.

**Why the OS theme is not followed**

There was a bug where this program's text vanished in macOS dark mode. One
cause — widgets hardcoded a light background (`background:#fafafa`) **without
setting a text color**, so when the OS switched the default text to white, it
became white-on-white.

Two ways to fix it:
  ① write the text color everywhere too → every new widget forgets it again
  ② **the program owns its palette** → the same screen regardless of OS theme

② won. Engineering tools get screenshotted into reports, and the same program
photographing differently on every machine is its own kind of confusion.
Isight and its peers all shipping a fixed light theme is probably the same
reasoning.

**Type scale** — the screen uses exactly four sizes. Do not invent a fifth in a widget.
    H1 20px  page titles       H2 15px  card titles
    BODY 14px body/tables/buttons     SMALL 13px asides/footnotes

**Colors carry meaning** — never invent a color in widget code beyond what is named here.
"""
from __future__ import annotations

import sys

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

# ══════════════════════════════════════════════════════════════════════
# color tokens
# ══════════════════════════════════════════════════════════════════════
BG = "#ffffff"          # canvas
SURFACE = "#f6f8fa"     # one layer up: cards, headers
SURFACE_ALT = "#fbfcfd"  # table stripes
BORDER = "#d0d7de"
BORDER_STRONG = "#afb8c1"

TEXT = "#1f2328"        # body
TEXT_MUTED = "#59636e"  # asides
TEXT_FAINT = "#818b98"  # footnotes

ACCENT = "#0969da"      # selection · links · emphasis
ACCENT_SOFT = "#ddf4ff"

OK = "#1a7f37"          # requirement met
OK_SOFT = "#dafbe1"
WARN = "#9a6700"        # undecided · caution
WARN_SOFT = "#fff8c5"
FAIL = "#cf222e"        # requirement unmet
FAIL_SOFT = "#ffebe9"
PENDING = "#59636e"     # computing

# discriminability zones (Diagnose tab) — four steps, worst to best
ZONE_BAD = "#f2a19e"     # < 1   indistinguishable
ZONE_EDGE = "#f5dd7a"    # 1~2   borderline
ZONE_GOOD = "#9fe0b0"    # 2~3.5 usable
ZONE_BEST = "#5ec27c"    # ≥ 3.5 comfortable

# row-state backgrounds in tables (text color is always set separately to TEXT)
ROW_EXCLUDED = "#ffeef0"
ROW_PENDING = "#eef4fb"
ROW_ZERO = "#fff8e6"

STATE_COLOR = {"OK": OK, "FAIL": FAIL, "UNDECIDED": WARN, "WARN": WARN,
               "PENDING": PENDING, "UNCOMPUTABLE": TEXT_FAINT}
STATE_MARK = {"OK": "○", "FAIL": "×", "UNDECIDED": "△", "WARN": "△",
              "PENDING": "…", "UNCOMPUTABLE": "—"}

# ══════════════════════════════════════════════════════════════════════
# fonts · spacing
# ══════════════════════════════════════════════════════════════════════
# Per-OS font preference, CJK-capable first so user-entered CJK names render.
FONT_CANDIDATES = {
    "win32": ["Malgun Gothic", "Segoe UI"],
    "darwin": ["Apple SD Gothic Neo", "Helvetica Neue"],
}
MONO_FAMILY = "'SF Mono', Menlo, Consolas, 'D2Coding', monospace"

FONT_SIZE = 14       # BODY
H1 = 20
H2 = 15
SMALL = 13
GAP = 8
ROW_HEIGHT = 34      # table row height. Editors need room or the text clips
NAV_WIDTH = 212      # the left step rail
CONTROL_H = 34       # button / input height


# ══════════════════════════════════════════════════════════════════════
# cards · badges — recurring combinations get names
# ══════════════════════════════════════════════════════════════════════
def card(tone: str = "plain") -> str:
    """One prose box. tone = plain / ok / warn / fail / info

    **Background and text color are always set together.** Set only one and it
    disappears in dark mode.
    """
    bg, fg, border = {
        "plain": (SURFACE, TEXT, BORDER),
        "ok": (OK_SOFT, "#0f5323", "#aceebb"),
        "warn": (WARN_SOFT, "#7a4f01", "#f5e5a0"),
        "fail": (FAIL_SOFT, "#a40e26", "#ffcecb"),
        "info": (ACCENT_SOFT, "#0a3069", "#b6e3ff"),
    }[tone]
    return (f"background:{bg}; color:{fg}; border:1px solid {border};"
            f"border-radius:8px; padding:10px 12px;")


def muted() -> str:
    return f"color:{TEXT_MUTED};"


def faint() -> str:
    return f"color:{TEXT_FAINT};"


def small() -> str:
    return f"color:{TEXT_MUTED}; font-size:{SMALL}px;"


# ══════════════════════════════════════════════════════════════════════
# global application
# ══════════════════════════════════════════════════════════════════════
QSS = f"""
QWidget {{
    color: {TEXT};
    font-size: {FONT_SIZE}px;
}}
QMainWindow, QDialog {{ background: {BG}; }}
QScrollArea {{ background: transparent; border: 0; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

/* ── text roles ───────────────────────────────────────────────── */
QLabel[role="h1"] {{ font-size: {H1}px; font-weight: 700; color: {TEXT}; }}
QLabel[role="h2"] {{ font-size: {H2}px; font-weight: 600; color: {TEXT}; }}
QLabel[role="desc"] {{ font-size: {SMALL}px; color: {TEXT_MUTED}; }}
QLabel[role="muted"] {{ color: {TEXT_MUTED}; }}
QLabel[role="faint"] {{ font-size: {SMALL}px; color: {TEXT_FAINT}; }}

/* ── cards ────────────────────────────────────────────────────── */
QFrame[card="true"] {{
    background: {BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QFrame[card="true"] > QLabel, QFrame[card="true"] QLabel[plain="true"] {{ border: 0; }}

/* ── tables ───────────────────────────────────────────────────── */
QTableWidget, QTableView {{
    background: {BG};
    alternate-background-color: {SURFACE_ALT};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    border-radius: 6px;
    selection-background-color: {ACCENT_SOFT};
    selection-color: {TEXT};
}}
QTableWidget::item, QTableView::item {{ padding: 6px 9px; }}
QTableWidget::item:selected {{ background: {ACCENT_SOFT}; color: {TEXT}; }}

QHeaderView::section {{
    background: {SURFACE};
    color: {TEXT};
    font-weight: 600;
    padding: 9px 9px;
    border: 0;
    border-right: 1px solid {BORDER};
    border-bottom: 2px solid {BORDER_STRONG};
}}
QHeaderView::section:vertical {{
    color: {TEXT_FAINT};
    font-weight: 400;
    padding: 0 8px;
    border-right: 2px solid {BORDER_STRONG};
    border-bottom: 1px solid {BORDER};
}}
QTableCornerButton::section {{ background: {SURFACE}; border: 0;
                               border-bottom: 2px solid {BORDER_STRONG}; }}

/* ── boxes ────────────────────────────────────────────────────── */
QGroupBox {{
    background: {BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 18px;
    padding: 16px 14px 12px 14px;
    font-weight: 600;
    font-size: {H2}px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {TEXT};
}}

/* ── buttons ──────────────────────────────────────────────────── */
QPushButton {{
    background: {BG};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 0 16px;
    min-height: {CONTROL_H - 2}px;
    font-weight: 500;
}}
QPushButton:hover {{ background: {SURFACE}; border-color: {BORDER_STRONG}; }}
QPushButton:pressed {{ background: #e9edf1; }}
QPushButton:disabled {{ color: {TEXT_FAINT}; background: {SURFACE};
                        border-color: #e4e8ec; }}
QPushButton[primary="true"] {{
    background: {ACCENT}; color: #ffffff; border-color: #0a58ca; font-weight: 600;
}}
QPushButton[primary="true"]:hover {{ background: #0860c4; }}
QPushButton[primary="true"]:disabled {{ background: #b9c6d3; border-color: #b9c6d3;
                                        color: #ffffff; }}
QPushButton[danger="true"] {{ color: {FAIL}; }}
QPushButton[danger="true"]:hover {{ background: {FAIL_SOFT}; border-color: #ffcecb; }}

/* text-only link buttons — the "why?" kind. Never disturbs the flow */
QPushButton[link="true"], QToolButton[link="true"] {{
    background: transparent; border: 0; color: {ACCENT}; padding: 2px 4px;
    min-height: 0; font-weight: 500; text-decoration: underline;
}}
QPushButton[link="true"]:hover, QToolButton[link="true"]:hover {{ color: #0a58ca; }}
QToolButton {{ border: 0; background: transparent; padding: 2px 4px; color: {TEXT}; }}
QToolButton:hover {{ background: {SURFACE}; border-radius: 5px; }}

/* ── inputs ───────────────────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextBrowser {{
    background: {BG};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 5px 9px;
    selection-background-color: {ACCENT_SOFT};
    selection-color: {TEXT};
}}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{ min-height: {CONTROL_H - 12}px; }}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus,
QPlainTextEdit:focus {{ border-color: {ACCENT}; }}
QLineEdit:read-only {{ background: {SURFACE}; color: {TEXT_MUTED}; }}
QComboBox::drop-down {{ border: 0; width: 22px; }}
QComboBox QAbstractItemView {{
    background: {BG}; color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT_SOFT}; selection-color: {TEXT};
}}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{ width: 18px; border: 0; }}
QCheckBox {{ spacing: 7px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; }}

/* editors **inside** tables — cell height is fixed, so padding shrinks.
   Give them the outer padding (5px) plus a border and the text clips downward. */
QTableWidget QLineEdit, QTableView QLineEdit,
QTableWidget QComboBox, QTableView QComboBox,
QTableWidget QSpinBox,  QTableWidget QDoubleSpinBox {{
    padding: 0 5px;
    margin: 0;
    border-radius: 3px;
    min-height: 22px;
}}
QTableWidget QComboBox {{ border: 1px solid {BORDER}; background: {BG}; }}

/* ── the left step rail ───────────────────────────────────────── */
QListWidget#nav {{
    background: {SURFACE};
    border: 0; border-right: 1px solid {BORDER};
    padding: 10px 8px;
    outline: 0;
}}
QListWidget#nav::item {{ border: 0; padding: 0; margin: 0 0 3px 0; }}
QListWidget#nav::item:selected {{ background: transparent; }}

/* ── the top bar ──────────────────────────────────────────────── */
QFrame#header {{ background: {BG}; border-bottom: 1px solid {BORDER}; }}
QLabel#pill {{
    background: {SURFACE}; color: {TEXT_MUTED}; border: 1px solid {BORDER};
    border-radius: 12px; padding: 3px 11px; font-size: {SMALL}px;
}}

/* ── tabs ─────────────────────────────────────────────────────── */
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 8px; top: -1px; }}
QTabBar::tab {{
    background: transparent; color: {TEXT_MUTED};
    padding: 9px 18px; border: 1px solid transparent; border-bottom: 0;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
    min-width: 60px;
}}
QTabBar::tab:hover {{ color: {TEXT}; }}
QTabBar::tab:selected {{
    background: {BG}; color: {ACCENT}; font-weight: 600;
    border-color: {BORDER};
}}

/* ── the rest ─────────────────────────────────────────────────── */
QProgressBar {{
    border: 1px solid {BORDER}; border-radius: 6px;
    background: {SURFACE}; text-align: center; color: {TEXT};
    font-size: {SMALL}px; min-height: 18px; max-height: 20px;
}}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 5px; }}
QStatusBar {{ background: {SURFACE}; border-top: 1px solid {BORDER}; min-height: 30px; }}
QStatusBar::item {{ border: 0; }}
QSplitter::handle {{ background: transparent; }}
QSplitter::handle:horizontal {{ width: 10px; }}
QSplitter::handle:vertical {{ height: 10px; }}
QToolTip {{
    background: #1f2328; color: #ffffff;
    border: 0; padding: 7px 9px; border-radius: 6px; font-size: {SMALL}px;
}}
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #c8d1da; border-radius: 5px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background: {BORDER_STRONG}; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; }}
QScrollBar::handle:horizontal {{ background: #c8d1da; border-radius: 5px; min-width: 28px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QMenuBar {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; padding: 2px 6px; }}
QMenuBar::item {{ padding: 4px 10px; border-radius: 5px; }}
QMenuBar::item:selected {{ background: {ACCENT_SOFT}; }}
QMenu {{ background: {BG}; border: 1px solid {BORDER}; padding: 5px; }}
QMenu::item {{ padding: 7px 24px; border-radius: 5px; }}
QMenu::item:selected {{ background: {ACCENT_SOFT}; }}
QMessageBox QLabel {{ min-width: 360px; }}
"""


def pick_font_family() -> str | None:
    """The first preferred font installed on this OS. None → Qt default."""
    families = set(QFontDatabase.families())
    for name in FONT_CANDIDATES.get(sys.platform, []):
        if name in families:
            return name
    return None


def apply(app: QApplication) -> None:
    """Apply once, program-wide.

    Pinning the Fusion style makes macOS and Windows look the same, and owning
    the palette keeps OS dark mode from touching the text colors.
    """
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(BG))
    pal.setColor(QPalette.WindowText, QColor(TEXT))
    pal.setColor(QPalette.Base, QColor(BG))
    pal.setColor(QPalette.AlternateBase, QColor(SURFACE_ALT))
    pal.setColor(QPalette.Text, QColor(TEXT))
    pal.setColor(QPalette.Button, QColor(SURFACE))
    pal.setColor(QPalette.ButtonText, QColor(TEXT))
    pal.setColor(QPalette.Highlight, QColor(ACCENT_SOFT))
    pal.setColor(QPalette.HighlightedText, QColor(TEXT))
    pal.setColor(QPalette.ToolTipBase, QColor("#1f2328"))
    pal.setColor(QPalette.ToolTipText, QColor("#ffffff"))
    pal.setColor(QPalette.PlaceholderText, QColor(TEXT_FAINT))
    pal.setColor(QPalette.Disabled, QPalette.Text, QColor(TEXT_FAINT))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(TEXT_FAINT))
    pal.setColor(QPalette.Disabled, QPalette.WindowText, QColor(TEXT_FAINT))
    app.setPalette(pal)

    font = QFont()
    family = pick_font_family()
    if family:
        font.setFamily(family)
    font.setPixelSize(FONT_SIZE)
    app.setFont(font)
    app.setStyleSheet(QSS)


def heading(text: str, size: int = H2) -> str:
    return f"<span style='font-size:{size}px; font-weight:600; color:{TEXT}'>{text}</span>"


def set_role(widget, role: str) -> None:
    """Give a QLabel a text role (h1/h2/desc/muted/faint). Sizes live in the QSS alone."""
    widget.setProperty("role", role)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


# step-rail (left) only — named here so widget code never invents a color
NAV_HOVER = "#eaeef2"
NAV_LOCKED = "#b6bec7"
