# -*- coding: utf-8 -*-
"""Are the numbers the help quotes true.

The help's «N tests» shipped stale twice (133 → 169 → …). A number a human counts is
always wrong sooner or later, so it is compared with the real collected count here.
Benchmark numbers must come from one place only, `core/acquisition.py: BENCH_CLAIMS`
(tests/test_global.py checks those values against the JSON).
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from core.acquisition import BENCH_CLAIMS

ROOT = Path(__file__).resolve().parents[1]


def _topics():
    from ui.tab_help import topics
    return {t.key: t for t in topics()}


def _plain(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def test_claimed_test_count_is_the_real_one():
    from ui.tab_help import TEST_COUNT
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    out = subprocess.run([sys.executable, "-m", "pytest", "tests", "--collect-only", "-q",
                          "-p", "no:cacheprovider"], cwd=ROOT, env=env,
                         capture_output=True, text=True, timeout=300).stdout
    m = re.search(r"(\d+) tests? collected", out)
    assert m, out[-500:]
    assert int(m.group(1)) == TEST_COUNT, (
        f"tests/ holds {m.group(1)} tests but the help says {TEST_COUNT} — "
        "ui/tab_help.py: TEST_COUNT must be updated")


def test_help_quotes_the_benchmark_from_the_single_source():
    t = _topics()
    acq, verified = _plain(t["acq"].body), _plain(t["verified"].body)
    multi = f"{round(BENCH_CLAIMS['multimodal_hit'] * 100)}%"
    assert multi in acq and multi in verified
    assert f"{round(BENCH_CLAIMS['best_alternative_multimodal_hit'] * 100)}%" in acq
    assert f"{round(BENCH_CLAIMS['ucb_multimodal_hit'] * 100)}%" in acq
    for name in ("levy4", "twopeak", "ackley2", "hartmann6"):
        assert f"{round(BENCH_CLAIMS['ei_hit'][name] * 100)}%" in acq, name
    # the old validation script (outside the repo) is never cited as evidence
    for topic in t.values():
        assert "verify_global.py" not in topic.body and "verify_global.py" not in " ".join(topic.code)
        assert "69~93" not in topic.body and "69–93" not in topic.body and "69-93" not in topic.body


def test_every_topic_says_where_its_numbers_come_from():
    for key, topic in _topics().items():
        assert topic.code, f"{key}: the list of backing code locations is empty"
        assert len(_plain(topic.body)) > 80, f"{key}: the body is too short"
