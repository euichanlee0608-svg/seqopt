# -*- coding: utf-8 -*-
"""M5, reports — PDF · calculation log · reproduction script (F-40 ~ F-43).

What gets checked is not "was a file written" but **is the evidence actually
inside.** A report that copies the numbers and drops the working cannot stop
the mistake this project made four times.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from core.diagnostics import discriminability, loocv_r2, nugget_ratio
from core.fonts import find_cjk_font, register_pdf_font
from core.importer import apply_profile, preview
from core.project import Project
from core.report import ReportData, calculation_log, report_figures, reproduce_script, write_pdf
from core.spec import ObjSpec, VarSpec
from tests.loaders import DATA
from tests.test_ui import synthetic_profile

XLSX = str(Path(DATA) / "synthetic_raman.xlsx")


@pytest.fixture(scope="module")
def syn_project():
    _, rows = preview(XLSX, "xlsx", 1, limit=10 ** 9)
    prof = synthetic_profile()
    ms, _ = apply_profile(rows, prof)
    for i, m in enumerate(ms, 1):
        m["id"] = i
    return Project(name="Synthetic G/D optimization",
                   inputs=[VarSpec("power", "W", "continuous", 150, 190, step=10.0),
                           VarSpec("dwell", "s", "integer", 3, 7)],
                   objective=ObjSpec("G/D ratio", "a.u.", "max"),
                   budget_total=40, measurements=ms,
                   exclude_zero=True, import_profile=prof)


@pytest.fixture(scope="module")
def data(syn_project):
    return ReportData.compute(syn_project)


# ══════════════════════════════════════════════════════════════════════
# Fonts — a missing CJK font degrades gracefully, never crashes
# ══════════════════════════════════════════════════════════════════════
def test_pdf_font_registers_or_falls_back():
    """With a CJK font installed it registers; without one it must still return
    a usable font (Helvetica) — an English report cannot fail to generate just
    because the machine has no Korean font."""
    name = register_pdf_font()
    assert name in ("CJK", "Helvetica")
    if find_cjk_font() is not None:
        assert name == "CJK"


def test_missing_cjk_font_falls_back_to_helvetica(monkeypatch):
    import core.fonts as fonts
    monkeypatch.setattr(fonts, "find_cjk_font", lambda: None)
    assert fonts.register_pdf_font("CJK-test-missing") == "Helvetica"


def test_has_cjk_detects_scripts():
    from core.fonts import has_cjk
    assert has_cjk("전력")
    assert has_cjk("dwell 時間")
    assert not has_cjk("power / dwell 3s")


# ══════════════════════════════════════════════════════════════════════
# The calculation log (F-41) — does it reproduce the diagnostics
# ══════════════════════════════════════════════════════════════════════
def test_log_reproduces_diagnostic_numbers(data, syn_project):
    """The log must carry the same numbers the diagnostics computed."""
    log = calculation_log(data)
    ds = syn_project.dataset()
    d = discriminability(ds.reps)
    r = loocv_r2(ds.XN, ds.y_mean)
    n = nugget_ratio(ds.XN, ds.y_mean, sigma_w=d.sigma_w)
    for token in (f"{d.sigma_w:.4f}", f"{d.sigma_b:.4f}",
                  f"{d.total_ss:.6f}",
                  f"[{d.ci_lo:.2f}, {d.ci_hi:.2f}]",
                  f"{r.r2:+.3f}",
                  f"{r.ss_res:.4f}", f"{r.ss_tot:.4f}",
                  f"{n.ratio:.3f}"):
        assert token in log, f"{token} is missing from the calculation log"


def test_log_shows_the_working_not_just_answers(data, syn_project):
    """Numbers without the working are not a report (principle P4)."""
    log = calculation_log(data)
    d = discriminability(syn_project.dataset().reps)
    assert f"sigma_w = sqrt({d.total_ss:.6f} / {d.total_df})" in log   # the formula itself
    assert "(n-1)*var" in log                                          # the per-condition table
    assert log.count("\n") > 40                                        # 15 condition rows + steps


def test_log_states_the_verdict_and_why(data):
    log = calculation_log(data)
    assert "[gate verdict]" in log
    assert "LOCKED" in log
    assert "measuring everything is better" in log


def test_log_marks_forced_reports(syn_project):
    forced = ReportData.compute(syn_project, gate_bypassed=True)
    assert "[caution]" in calculation_log(forced)
    assert "force-generated with requirements unmet" in calculation_log(forced)


def test_log_refuses_to_invent_sigma_w_without_replicates():
    """Without replicates it says NOT COMPUTABLE. No assumed value is substituted."""
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    for i, v in enumerate([0.5, 0.9, 1.2, 0.7]):
        p.add([float(i)], v)
    log = calculation_log(ReportData.compute(p))
    assert "NOT COMPUTABLE" in log
    assert "No assumed value is substituted" in log


# ══════════════════════════════════════════════════════════════════════
# The PDF (F-40)
# ══════════════════════════════════════════════════════════════════════
def test_pdf_is_written_and_readable(data, tmp_path):
    out = write_pdf(data, tmp_path / "r.pdf")
    raw = out.read_bytes()
    assert raw.startswith(b"%PDF")
    assert len(raw) > 50_000                 # with figures inside, at least this much


def test_pdf_contains_figures(data):
    titles = [t for t, _ in report_figures(data)]
    assert "Replicate scatter" in titles
    assert "Learnability" in titles          # makes R²<0 visible (F-35)
    assert "Terrain" in titles
    assert "Response surface" in titles      # 2 variables → drawn


def test_forced_pdf_is_bigger_because_of_the_stamp(data, syn_project, tmp_path):
    """A forced report stamps every page — one captured page still carries it."""
    plain = write_pdf(data, tmp_path / "a.pdf").stat().st_size
    forced = write_pdf(ReportData.compute(syn_project, gate_bypassed=True),
                       tmp_path / "b.pdf").stat().st_size
    assert forced > plain


# ══════════════════════════════════════════════════════════════════════
# The reproduction script (F-43) — does it really run
# ══════════════════════════════════════════════════════════════════════
def test_reproduce_script_actually_runs_and_matches(data, syn_project, tmp_path):
    """The generated script is **actually executed** and must print the report's numbers.

    Code that looks runnable and code that runs are different things.
    """
    script = tmp_path / "repro.py"
    script.write_text(reproduce_script(data), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(script)], cwd=Path.cwd(),
                          capture_output=True, text=True, timeout=300,
                          encoding="utf-8", errors="replace")
    assert proc.returncode == 0, proc.stderr[-800:]
    out = proc.stdout
    ds = syn_project.dataset()
    d = discriminability(ds.reps)
    r = loocv_r2(ds.XN, ds.y_mean)
    assert "usable conditions 15 · 45 measurements" in out
    assert f"{d.sigma_w:.4f}" in out
    assert f"{d.sigma_b:.4f}" in out
    assert f"{r.r2:+.3f}" in out
    assert "LOCKED" in out


def test_reproduce_script_survives_a_non_utf8_console(data, tmp_path):
    """It must not die on a legacy-encoding Windows console.

    This actually blew up with UnicodeEncodeError on windows-latest in CI once.
    The generated script reconfigures stdout to UTF-8.
    """
    src = reproduce_script(data)
    assert 'reconfigure(encoding="utf-8")' in src

    script = tmp_path / "repro.py"
    script.write_text(src, encoding="utf-8")
    import os
    env = {**os.environ, "PYTHONIOENCODING": "cp949"}      # imitate the legacy console
    proc = subprocess.run([sys.executable, str(script)], cwd=Path.cwd(), env=env,
                          capture_output=True, text=True, timeout=300,
                          encoding="utf-8", errors="replace")
    assert proc.returncode == 0, proc.stderr[-800:]


def test_reproduce_script_keeps_exclusions(data):
    """Exclusion and pending marks must survive into the script, or the numbers differ."""
    src = reproduce_script(data)
    assert "EXCLUDE_ZERO = True" in src
    assert "excluded=" in src and "pending=" in src
    assert src.count("dict(inputs=") == len(data.project.measurements)


# ══════════════════════════════════════════════════════════════════════
# The screen — does it merely display what the core built
# ══════════════════════════════════════════════════════════════════════
def test_tab_disables_export_until_built(qapp, syn_project):
    from ui.tab_report import ReportTab
    tab = ReportTab(syn_project)
    assert not tab.pdf.isEnabled()
    assert not tab.log.isEnabled()
    assert not tab.script.isEnabled()


def test_tab_shows_the_log_after_building(qapp, syn_project, data):
    from ui.tab_report import ReportTab
    tab = ReportTab(syn_project)
    tab._on_done(data)                        # imitate background completion
    assert tab.pdf.isEnabled()
    assert "sigma_w" in tab.preview.toPlainText()
    assert "LOCKED" in tab.status.text()


def test_tab_warns_when_forced(qapp, syn_project):
    from ui.tab_report import ReportTab
    tab = ReportTab(syn_project)
    tab.set_bypassed(True)
    tab._on_done(ReportData.compute(syn_project, gate_bypassed=True))
    assert "Requirements unmet" in tab.status.text()
