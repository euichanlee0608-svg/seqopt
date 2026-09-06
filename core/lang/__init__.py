# -*- coding: utf-8 -*-
"""The Korean catalog — one dict per area, merged here. See core/i18n.py for the rules.

Each `ko_*.py` holds `KO = {"English text": "한국어", ...}` for the source files named in its
header. The split is only so that several people can edit different areas without merge
conflicts; a key may appear in more than one file only with the same Korean text.
"""
from __future__ import annotations

from . import ko_core, ko_data, ko_diag, ko_help, ko_model, ko_report, ko_shell

PARTS = (ko_shell, ko_data, ko_model, ko_diag, ko_help, ko_report, ko_core)

KO: dict[str, str] = {}
for _part in PARTS:
    for _en, _ko in _part.KO.items():
        if _en in KO and KO[_en] != _ko:
            raise ImportError(f"{_part.__name__}: {_en!r} already has a different Korean text")
        KO[_en] = _ko
