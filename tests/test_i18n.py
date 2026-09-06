# -*- coding: utf-8 -*-
"""Both languages, always — enforced, not remembered.

English text is the key; `core/lang/ko_*.py` holds the Korean. These tests make a one-language
update impossible to ship:
  · every user-visible string in the source goes through `tr()`          (tests/i18n_scan.py)
  · every `tr()` key has a Korean line, and every Korean line is still used
  · `{placeholders}` agree, the Korean is really Korean, and nothing lab-specific leaked in
"""
from __future__ import annotations

import re

import pytest

from core import i18n
from core.lang import KO
from tests.i18n_scan import ROOT, placeholders, scan_all, scan_file, sources

# English that stays English on the Korean screen (names, symbols) — a key listed here may have ko == en
SAME_OK: set[str] = set()
HANGUL = re.compile(r"[가-힣]")
LATIN_WORD = re.compile(r"[A-Za-z]{4,}")
# the public catalog is translated from the public English text — never from the private lab build
LAB_TOKENS = ("나노필름", "Nanofilm", "nanofilm", "Raman", "라만", "Dummy data", "교수")

FILES = sources()
IDS = [p.relative_to(ROOT).as_posix() for p in FILES]


@pytest.fixture(scope="module")
def scan():
    return scan_all(FILES)


@pytest.mark.parametrize("path", FILES, ids=IDS)
def test_user_text_goes_through_tr(path):
    s = scan_file(path)
    problems = [str(f) for f in s.errors + s.bare]
    assert not problems, f"{len(problems)} strings bypass tr():\n  " + "\n  ".join(problems)


@pytest.mark.parametrize("path", FILES, ids=IDS)
def test_every_key_has_korean(path):
    missing = sorted({k for _, _, k in scan_file(path).keys if k not in KO})
    assert not missing, f"{len(missing)} keys without Korean:\n  " + "\n  ".join(repr(k) for k in missing)


def test_no_stale_korean(scan):
    used = {k for _, _, k in scan.keys}
    stale = sorted(k for k in KO if k not in used)
    assert not stale, f"{len(stale)} Korean lines no longer match any tr() key:\n  " + \
        "\n  ".join(repr(k) for k in stale)


def test_placeholders_agree():
    bad = [(en, ko) for en, ko in KO.items() if placeholders(en) != placeholders(ko)]
    assert not bad, "\n".join(f"{en!r} -> {ko!r}" for en, ko in bad)


def test_korean_is_korean():
    """A Korean line that is just the English copied over is a hole in the translation."""
    lazy = [en for en, ko in KO.items()
            if en not in SAME_OK and " " in en.strip() and LATIN_WORD.search(en) and not HANGUL.search(ko)]
    assert not lazy, "\n".join(repr(k) for k in lazy)


def test_no_lab_tokens():
    hits = [(en, ko) for en, ko in KO.items() if any(t in en or t in ko for t in LAB_TOKENS)]
    assert not hits, hits


def test_tr_falls_back_and_records(korean):
    assert i18n.language() == "ko"
    assert i18n.tr("§ no such key {n} §", n=3) == "§ no such key 3 §"
    assert "§ no such key {n} §" in i18n.missing()


def test_default_language(monkeypatch):
    monkeypatch.delenv("SEQOPT_LANG", raising=False)
    assert i18n.default_language() == "en"
    assert i18n.default_language(system="ko_KR") == "ko"
    assert i18n.default_language(saved="ko", system="en_US") == "ko"
    assert i18n.default_language(saved="en", system="ko_KR") == "en"
    monkeypatch.setenv("SEQOPT_LANG", "ko")
    assert i18n.default_language(saved="en", system="en_US") == "ko"
    monkeypatch.setenv("SEQOPT_LANG", "xx")
    assert i18n.default_language(system="ko_KR") == "ko"
    with pytest.raises(ValueError):
        i18n.set_language("xx")
