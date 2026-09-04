# -*- coding: utf-8 -*-
"""The canvas for Qt screens. **Colors and fonts have one source: `core/plotstyle.py`.**

Never define a new color here — when the screen and the PDF report look
different, the user cannot tell which one to trust.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg  # noqa: E402
from matplotlib.figure import Figure                              # noqa: E402

from core.plotstyle import (C_AXIS, C_BAND, C_BEST, C_GRID, C_MEAN, C_POINT,  # noqa: F401
                            C_RAW, C_RESIDUAL, C_SUGGEST,
                            CMAP_EI, CMAP_MU, CMAP_SD, CJK_FONTS, apply_style,
                            available_fonts, mark_best, mark_suggest, scatter_points,
                            stamp_untrusted)


class Canvas(FigureCanvasQTAgg):
    """A matplotlib canvas used as a Qt widget."""

    def __init__(self, parent=None, width=6.0, height=4.0, dpi=110):
        self.fig = Figure(figsize=(width, height), dpi=dpi, constrained_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)

    def clear(self):
        self.fig.clear()
        return self.fig
