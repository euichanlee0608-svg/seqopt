# -*- coding: utf-8 -*-
"""Run Qt without a display. GUI tests run as-is on CI and headless machines."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    # the app's real font and style — Qt's fallback font is ~30% narrower, so a
    # layout measured without the theme passes text that users see clipped
    from ui import theme
    theme.apply(app)
    yield app


@pytest.fixture(autouse=True)
def _english_by_default():
    """Tests assert English text. A test that switches to Korean must not leak into the next one."""
    from core import i18n
    i18n.set_language("en")
    yield
    i18n.set_language("en")


@pytest.fixture
def korean():
    from core import i18n
    i18n.set_language("ko")
    yield
    i18n.set_language("en")
