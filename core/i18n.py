# -*- coding: utf-8 -*-
"""Two languages, one code base — English and Korean.

Every user-visible string is written **in English, in the code**, wrapped in `tr()`. The
Korean text lives in `core/lang/ko_*.py`, keyed by the English string. A missing Korean
entry shows the English (never a blank) and fails `tests/test_i18n.py`, so a string cannot
ship in one language only — and a bare literal in a text-setting call fails the same test.

Why the English text is the key (gettext style) and not an id like "recommend.title":
with 2,000+ strings, inventing an id for each is where mistakes creep in, and the code
stays readable as it is. Change the English wording and the test says the Korean is stale.

`core/` must not import Qt, so the language is plain module state here. `app.py` picks it
(SEQOPT_LANG → the saved setting → the OS locale) and the window rebuilds itself on a switch
(`ui/main_window.py: MainWindow.switch_language`).
"""
from __future__ import annotations

import os

from core.lang import KO

LANGUAGES = ("en", "ko")
NAMES = {"en": "English", "ko": "한국어"}

_current = "en"
_missing: set[str] = set()


def language() -> str:
    return _current


def set_language(lang: str) -> None:
    if lang not in LANGUAGES:
        raise ValueError(f"unknown language {lang!r} — one of {LANGUAGES}")
    global _current
    _current = lang


def default_language(saved: str | None = None, system: str | None = None) -> str:
    """SEQOPT_LANG → the setting the user saved → the OS locale (e.g. "ko_KR") → English."""
    env = os.environ.get("SEQOPT_LANG", "").strip().lower()
    if env in LANGUAGES:
        return env
    if saved in LANGUAGES:
        return saved
    if system and system.lower().startswith("ko"):
        return "ko"
    return "en"


def tr(text: str, **fields) -> str:
    """`text` in the current language. `{name}` fields are filled in from `fields` (both languages)."""
    if _current == "en":
        out = text
    else:
        out = KO.get(text)
        if out is None:
            _missing.add(text)
            out = text
    return out.format(**fields) if fields else out


def missing() -> set[str]:
    """English strings that were asked for in Korean and had no entry (for tests and debugging)."""
    return set(_missing)
