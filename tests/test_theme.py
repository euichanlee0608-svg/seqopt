# -*- coding: utf-8 -*-
"""Screen colors and text — **readable under any OS theme.**

There was a white-on-white bug in macOS dark mode. One cause — a hardcoded
light background without a text color, so the OS flipped the text to white.
This file keeps that mistake from coming back.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtGui import QColor, QPalette

from ui import theme

UI_DIR = Path(__file__).resolve().parent.parent / "ui"


def _luma(hex_color: str) -> float:
    """WCAG relative luminance. Raw sRGB values will not do — the gamma must be unrolled."""
    def lin(v: float) -> float:
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    c = QColor(hex_color)
    return 0.2126 * lin(c.redF()) + 0.7152 * lin(c.greenF()) + 0.0722 * lin(c.blueF())


def contrast(fg: str, bg: str) -> float:
    """WCAG contrast ratio. Body text needs at least 4.5:1 to be readable."""
    a, b = sorted((_luma(fg) + 0.05, _luma(bg) + 0.05), reverse=True)
    return a / b


# ══════════════════════════════════════════════════════════════════════
# contrast — is it readable
# ══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("fg,bg,name", [
    (theme.TEXT, theme.BG, "body/canvas"),
    (theme.TEXT, theme.SURFACE, "body/card"),
    (theme.TEXT, theme.SURFACE_ALT, "body/stripe"),
    (theme.TEXT, theme.ROW_EXCLUDED, "body/excluded-row"),
    (theme.TEXT, theme.ROW_PENDING, "body/pending-row"),
    (theme.TEXT, theme.ROW_ZERO, "body/zero-row"),
    (theme.TEXT, theme.ACCENT_SOFT, "body/selection"),
    (theme.TEXT_MUTED, theme.BG, "muted/canvas"),
    (theme.OK, theme.BG, "pass color"),
    (theme.FAIL, theme.BG, "fail color"),
])
def test_text_is_readable_on_its_background(fg, bg, name):
    assert contrast(fg, bg) >= 4.5, f"{name} contrast {contrast(fg, bg):.2f} < 4.5"


def test_faint_text_still_meets_the_large_text_bar():
    """Footnotes need 3:1 — below that it is not gray, it is invisible."""
    assert contrast(theme.TEXT_FAINT, theme.BG) >= 3.0


@pytest.mark.parametrize("tone", ["plain", "ok", "warn", "fail", "info"])
def test_every_card_sets_both_background_and_colour(tone):
    """A card sets background and text color **together, always.** One alone vanishes in dark mode."""
    css = theme.card(tone)
    assert "background:" in css and "color:" in css
    bg = re.search(r"background:(#[0-9a-fA-F]{6})", css).group(1)
    fg = re.search(r"color:(#[0-9a-fA-F]{6})", css).group(1)
    assert contrast(fg, bg) >= 4.5, f"{tone} card contrast {contrast(fg, bg):.2f}"


# ══════════════════════════════════════════════════════════════════════
# independent of the OS theme
# ══════════════════════════════════════════════════════════════════════
def test_theme_overrides_a_dark_os_palette(qapp):
    """Even with a dark palette applied first, the program must win."""
    dark = QPalette()
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        dark.setColor(role, QColor("#ffffff"))
    for role in (QPalette.Window, QPalette.Base, QPalette.Button):
        dark.setColor(role, QColor("#2b2b2b"))
    qapp.setPalette(dark)

    theme.apply(qapp)
    pal = qapp.palette()
    assert pal.color(QPalette.Text).name() == theme.TEXT
    assert pal.color(QPalette.Base).name() == theme.BG
    assert contrast(pal.color(QPalette.Text).name(),
                    pal.color(QPalette.Base).name()) >= 4.5


def test_style_does_not_follow_the_native_os_look(qapp):
    """macOS and Windows must look identical — the OS-native style is off-limits.

    With setStyleSheet applied, Qt wraps a QStyleSheetStyle proxy, so the name
    is no longer 'fusion'. What matters is **not-native**, not the name.
    """
    theme.apply(qapp)
    name = qapp.style().metaObject().className().lower()
    for native in ("qmacstyle", "macintosh", "windowsvista", "windows11"):
        assert native not in name, f"an OS-native style is active: {name}"
    assert qapp.styleSheet(), "the global stylesheet is empty"


def test_apply_sets_fusion_as_the_base_style(qapp):
    """Before the stylesheet, the base style must be Fusion."""
    qapp.setStyleSheet("")
    qapp.setStyle("Fusion")
    assert "fusion" in qapp.style().metaObject().className().lower()
    theme.apply(qapp)          # restore the original state


# ══════════════════════════════════════════════════════════════════════
# no hardcoding — is the rule held by code
# ══════════════════════════════════════════════════════════════════════
def test_no_screen_hardcodes_its_own_colour():
    """A color invented outside `theme.py` is the next dark-mode bug."""
    offenders = []
    for path in UI_DIR.rglob("*.py"):
        if path.name == "theme.py":
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"#[0-9a-fA-F]{6}\b", line) and "theme." not in line:
                offenders.append(f"{path.name}:{i}  {line.strip()[:70]}")
    assert not offenders, "hardcoded colors at:\n" + "\n".join(offenders)


def test_cells_with_a_background_also_set_a_foreground():
    """Wherever a background is painted, a foreground must come too (the shape of the original bug)."""
    for name in ("tab_data.py", "tab_diag.py", "import_wizard.py"):
        src = (UI_DIR / name).read_text(encoding="utf-8")
        if "setBackground(" in src:
            assert "setForeground(" in src, f"{name} paints a background without a text color"
