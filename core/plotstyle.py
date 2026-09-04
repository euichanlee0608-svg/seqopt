# -*- coding: utf-8 -*-
"""Single source of truth for figures — fonts, colors and tick rules live only here.

Does not depend on Qt. The screen (`ui/widgets/plots.py`) and the PDF report
(`core/report.py`) must speak **the same color language**, so both import this
file.

**Colors carry meaning.** Different colors per figure would force the user to
re-read the legend every time.

  · predicted mean μ  → viridis   (magnitude; a perceptually ordered map)
  · uncertainty σ     → Greys     (darker = less known. It is "unknown", not a value, so grayscale)
  · acquisition EI    → YlOrRd    (where to measure next. The only "warm" map = the color of action)
  · measured points   → dark gray dots + white edge (visible on any background)
  · current best      → red ★
  · suggested point   → orange ◆

No rainbow (jet) — it invents boundaries that do not exist.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

# CJK-capable fonts — a fallback chain covering macOS and Windows lab PCs, so
# user-entered Korean/Japanese/Chinese variable names still render.
CJK_FONTS = ["Apple SD Gothic Neo", "AppleGothic", "Malgun Gothic",
             "NanumGothic", "Arial Unicode MS", "DejaVu Sans"]

CMAP_MU = "viridis"
CMAP_SD = "Greys"
CMAP_EI = "YlOrRd"

C_POINT = "#37474f"
C_BEST = "#d32f2f"
C_SUGGEST = "#f57c00"
C_MEAN = "#1e88e5"
C_BAND = "#90caf9"
C_GRID = "#e0e0e0"
C_AXIS = "#607d8b"        # reference lines (diagonal · thresholds)
C_RAW = "#9aa0a6"         # individual replicate points — fainter than condition means
C_RESIDUAL = "#90a4ae"    # residual drop lines


def available_fonts() -> list[str]:
    """Keep only the fonts that **actually exist** on this PC.

    Leaving a missing name in rcParams makes matplotlib warn on every glyph.
    The candidate list is generous so a project made on a Mac still opens on a
    Windows lab PC; filtering happens at run time.
    """
    import matplotlib.font_manager as fm
    have = {f.name for f in fm.fontManager.ttflist}
    found = [n for n in CJK_FONTS if n in have]
    return found or ["DejaVu Sans"]


def apply_style() -> None:
    """Call once. Do not touch rcParams anywhere else."""
    plt.rcParams.update({
        "font.family": available_fonts(),
        "axes.unicode_minus": False,          # CJK fonts often lack the Unicode minus and render a box
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#bdbdbd",
        "axes.labelcolor": "#37474f",
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "axes.titleweight": "bold",
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "xtick.color": "#607d8b",
        "ytick.color": "#607d8b",
        "legend.fontsize": 8,
        "legend.frameon": False,
        "grid.color": C_GRID,
        "grid.linewidth": 0.6,
        "axes.grid": True,
        "figure.autolayout": False,
        "savefig.dpi": 150,
    })



def stamp_untrusted(fig, text: str) -> None:
    """Stamp a response surface that has not learned.

    The figure is not hidden — diagnostics need it. Instead, **the fact that it
    must not be trusted is shown on top of it.** Screenshot it into a slide and
    the warning travels along.

    Text in figure coordinates gets covered by the axes, so a transparent
    full-canvas axes goes on top and the text is written there — that is what
    keeps it visible over a heatmap.
    """
    ov = fig.add_axes([0, 0, 1, 1], zorder=1000)
    ov.axis("off")
    ov.patch.set_alpha(0)
    ov.text(0.5, 0.5, text, ha="center", va="center", transform=ov.transAxes,
            fontsize=30, color="#d32f2f", alpha=0.22, rotation=24, weight="bold")


def scatter_points(ax, x, y=None, s=34, label="measured", zorder=5):
    """Measured points. White edges keep them visible on any background."""
    if y is None:
        return ax.scatter(x, [0] * len(x), s=s, c=C_POINT, edgecolors="white",
                          linewidths=0.8, zorder=zorder, label=label)
    return ax.scatter(x, y, s=s, c=C_POINT, edgecolors="white",
                      linewidths=0.8, zorder=zorder, label=label)


def mark_best(ax, x, y, label="current best"):
    return ax.scatter([x], [y], s=170, marker="*", c=C_BEST, edgecolors="white",
                      linewidths=1.0, zorder=7, label=label)


def mark_suggest(ax, x, y, label="EI max"):
    return ax.scatter([x], [y], s=95, marker="D", c=C_SUGGEST, edgecolors="white",
                      linewidths=1.0, zorder=7, label=label)
