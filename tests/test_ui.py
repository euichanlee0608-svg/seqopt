# -*- coding: utf-8 -*-
"""M2 acceptance — **open the lab spreadsheet and the verdict table appears.**

Anchored on the synthetic spreadsheet (tests/data/make_synthetic.py), which
mirrors the structure of the lab file the original study used. Not pixels —
**what the screens say** is what gets checked, because the sentences a user
reads are the requirement.
"""
from __future__ import annotations

import os

import pytest

from core.dataset import group_measurements
from core.importer import apply_profile, preview
from core.profile import ColumnMap, ImportProfile, guess_profile
from core.project import Project
from core.spec import ObjSpec, VarSpec
from tests.loaders import DATA

XLSX = os.path.join(DATA, "synthetic_raman.xlsx")


def synthetic_profile() -> ImportProfile:
    """The reading rules for the synthetic spreadsheet — A power · B dwell · E response."""
    cols = [ColumnMap("A", "input", "power", "W", "continuous"),
            ColumnMap("B", "input", "dwell", "s", "integer"),
            ColumnMap("C", "ignore"), ColumnMap("D", "ignore"),
            ColumnMap("E", "response", "G/D ratio", "a.u.", "continuous"),
            ColumnMap("F", "ignore")]
    return ImportProfile(kind="xlsx", sheet=1, header_row=1, columns=cols,
                         inherit_blank=True, exclude_zero=True)


@pytest.fixture(scope="module")
def imported():
    keys, rows = preview(XLSX, "xlsx", 1, limit=10 ** 9)
    p = synthetic_profile()
    p.columns = [c for c in p.columns if c.key in keys]
    ms, report = apply_profile(rows, p)
    return p, ms, report


# ══════════════════════════════════════════════════════════════════════
# Importing (T-01) — does structure setup work on a real file
# ══════════════════════════════════════════════════════════════════════
def test_profile_validates():
    assert synthetic_profile().validate() == []


def test_profile_rejects_bad_setups():
    p = ImportProfile(columns=[ColumnMap("A", "input", "x")])
    assert any("response" in e for e in p.validate())

    p = ImportProfile(columns=[ColumnMap("A", "response", "y"),
                               ColumnMap("B", "response", "y2")])
    assert any("Only one" in e for e in p.validate())

    p = ImportProfile(columns=[ColumnMap("A", "input", "same"),
                               ColumnMap("B", "input", "same"),
                               ColumnMap("C", "response", "y")])
    assert any("Duplicate" in e for e in p.validate())


def test_import_reproduces_reference_counts(imported):
    """T-01 — 25 conditions recognized, 10 all-zero exclusion candidates, 66 measurements."""
    _, ms, report = imported
    groups = group_measurements(ms)
    assert len(groups) == 25
    assert len(ms) == 66
    assert sum(1 for v in groups.values() if max(v) <= 0) == 10
    # two cells are `#DIV/0!` — reported as missing, never silently read as 0 (F-04)
    assert report["missing"] == 2


def test_text_rows_do_not_leak_into_conditions(imported):
    """The two 'pristine C paper' reference rows are not design points — they must not mix in."""
    _, ms, _ = imported
    groups = group_measurements(ms)
    assert all(all(isinstance(v, float) for v in k) for k in groups)
    assert len(groups) == 25            # the reference sample never became condition #26


def test_inherit_blank_handles_merged_cell_tables(tmp_path):
    """Merged-cell tables (the condition written only on the block's first row) read correctly (§6-2)."""
    csv_path = tmp_path / "merged.csv"
    csv_path.write_text("power,dwell,gd\n150,7,1.20\n,,1.19\n,,1.21\n160,5,1.31\n,,1.29\n",
                        encoding="utf-8")
    _, rows = preview(str(csv_path), "csv")
    cols = [ColumnMap("power", "input", "power"), ColumnMap("dwell", "input", "dwell"),
            ColumnMap("gd", "response", "gd")]

    on, _ = apply_profile(rows, ImportProfile(kind="csv", header_row=0, columns=cols,
                                              inherit_blank=True))
    off, rep = apply_profile(rows, ImportProfile(kind="csv", header_row=0, columns=cols,
                                                 inherit_blank=False))
    assert len(on) == 5 and len(group_measurements(on)) == 2      # grouped as 3 + 2 replicates
    assert len(off) == 2 and rep["skipped"] == 3                  # off → the blank rows are lost


def test_guess_separates_design_axes_from_measured_columns():
    """Design axes recycle values; intermediate measurement columns differ per row.

    Columns A power · B dwell are the design axes; C (D band) · D (G band) ·
    F (Avg) came out of the measurement. Fail to separate them and the
    condition count explodes.
    """
    keys, rows = preview(XLSX, "xlsx", 1, limit=60)
    g = guess_profile("xlsx", [str(rows[0].get(k, "") or k) for k in keys], rows[1:], keys)
    assert [c.key for c in g.input_columns] == ["A", "B"]
    assert g.response_column.key == "E"
    assert {c.key for c in g.columns if c.role == "ignore"} == {"C", "D", "F"}
    assert g.validate() == []


def test_guess_is_only_a_starting_point():
    """Some tables defeat any guess — the result must still be well-formed (the user fixes it)."""
    rows = [{"a": "1", "b": "2", "c": "3"}, {"a": "1", "b": "9", "c": "4"}]
    g = guess_profile("csv", ["a", "b", "c"], rows, ["a", "b", "c"])
    assert g.response_column is not None
    assert g.input_columns


# ══════════════════════════════════════════════════════════════════════
# Project save/open (T-06)
# ══════════════════════════════════════════════════════════════════════
def test_project_roundtrip_keeps_diagnostics_identical(imported, tmp_path):
    from core.diagnostics import discriminability

    prof, ms, _ = imported
    p = Project(name="Synthetic G/D",
                inputs=[VarSpec("power", "W", "continuous", 150, 190, step=10.0),
                        VarSpec("dwell", "s", "integer", 3, 7)],
                objective=ObjSpec("G/D ratio", "a.u.", "max"),
                measurements=[dict(m) for m in ms],
                exclude_zero=True, import_profile=prof)

    before = discriminability(p.dataset().reps)
    path = p.save(str(tmp_path / "t.seqopt"))
    q = Project.load(path)
    after = discriminability(q.dataset().reps)

    assert q.dataset().n_conditions == p.dataset().n_conditions
    assert after.sigma_w == pytest.approx(before.sigma_w, abs=1e-12)
    assert after.D[1] == pytest.approx(before.D[1], abs=1e-12)
    assert q.import_profile.inherit_blank is True      # the mapping survives the round trip


def test_project_holds_raw_data_not_a_path(imported, tmp_path):
    """Raw data lives inside the file, whole (principle P4). No external path references."""
    prof, ms, _ = imported
    p = Project(inputs=[VarSpec("a", "", "continuous", 0, 1)],
                measurements=[dict(m) for m in ms], import_profile=prof)
    path = p.save(str(tmp_path / "t.seqopt"))
    text = open(path, encoding="utf-8").read()
    assert '"measurements"' in text
    assert XLSX not in text
    assert len(Project.load(path).measurements) == len(ms)


# ══════════════════════════════════════════════════════════════════════
# The main window — does the verdict table actually appear (M2)
# ══════════════════════════════════════════════════════════════════════
@pytest.fixture
def window(qapp, imported):
    from ui.main_window import MainWindow

    prof, ms, _ = imported
    p = Project(name="Synthetic G/D",
                inputs=[VarSpec("power", "W", "continuous", 150, 190, step=10.0),
                        VarSpec("dwell", "s", "integer", 3, 7)],
                objective=ObjSpec("G/D ratio", "a.u.", "max"),
                budget_total=40, measurements=[dict(m) for m in ms],
                exclude_zero=True, import_profile=prof)
    w = MainWindow(p)
    w.runner.wait()
    qapp.processEvents()
    w.runner.wait()
    qapp.processEvents()
    return w


def test_window_shows_locked_gate(window, qapp):
    """The fixture locks — and **the blocker is learnability (②)**, by design."""
    g = window.gate
    assert g is not None, "diagnosis did not finish"
    assert g.learnable == "FAIL"
    assert g.discrim == "UNDECIDED"
    assert g.cond_count == "FAIL"
    assert g.replicates == "OK"
    assert g.locked


def test_status_bar_says_locked(window):
    """Whatever tab you are on, the status bar announces the lock (§4-1)."""
    text = window.badges.text()
    assert "LOCKED" in text
    assert "②learnability ×" in text


def test_diag_tab_explains_why_in_sentences(window):
    """Verdicts are sentences, not condition expressions (SPEC_AMENDMENTS A4 · A6)."""
    d = window.tab_diag
    assert "measuring everything is better" in d.r1.text.text()
    assert "25" in d.r1.text.text()               # power 5 × dwell 5 — conditions there are to choose from
    assert "power 5 × dwell 5" in d.r1.text.text()
    assert "worse than always answering" in d.r2.text.text()
    assert "undecided" in d.r3.text.text()
    assert "14/15" in d.r4.text.text()


def test_diag_tab_shows_calculation_trail(window):
    """Every number unfolds into its calculation (principle P4)."""
    from core.diagnostics import discriminability

    d = window.tab_diag
    assert d.calc.rowCount() == 15
    disc = discriminability(window.dataset.reps)
    formula = d.formula.text()
    assert f"{disc.sigma_w:.4f}" in formula and f"{disc.sigma_b:.4f}" in formula
    assert f"{disc.D[1]:.2f}" in formula
    # typeset formulas, not monospace character art — the symbols come from TeX
    assert r"\sigma_w" in formula and r"\sigma_b" in formula
    assert f"{disc.total_ss:.6f}" in formula                # the sum is visible too
    # the general formula first, then the same formula with this data's values
    assert formula.index(r"\sum_c") < formula.index(f"{disc.total_ss:.6f}")


def test_diag_tab_reads_the_gauge_and_plan(window):
    """For newcomers — which zone D is in, and how many more runs the recommended mark costs."""
    from core.diagnostics import discriminability, replicate_plan

    d = window.tab_diag
    disc = discriminability(window.dataset.reps)
    assert d.gauge.value is not None and abs(d.gauge.value - disc.D[1]) < 0.01
    reading = d.reading.text()
    assert "borderline" in reading and "undecided" in reading   # 1 ≤ D < 2, interval straddles 1
    assert "1.96" in d.levels.text() and "ndc" in d.levels.text()   # the basis is on screen
    assert d.plan.rowCount() == 3
    counts = [len(v) for v in window.dataset.reps]
    rows = replicate_plan(disc.sigma_b, disc.sigma_w, counts)
    assert d.plan.item(1, 2).text() == f"×{rows[1]['n']}"
    assert d.plan.item(1, 3).text() == f"+{rows[1]['extra']}"
    assert "σw stays what it is now" in d.plan_note.text()      # the assumption is not hidden
    assert "recommended ≥ 2" in d.r3.criterion.text()           # gate and recommended, side by side


def test_mathtext_renders_offscreen(qapp):
    """Formulas are really typeset — the image must not be blank."""
    from ui.widgets.mathtext import render
    pm = render(r"D = \frac{\sigma_b}{\sigma_w/\sqrt{n}}", px=16)
    assert pm.width() > 20 and pm.height() > 10
    img = pm.toImage()
    assert any(img.pixelColor(x, img.height() // 2).alpha() > 0 for x in range(img.width()))


def test_window_size_and_icon(window):
    """The window fits a laptop screen, and the icon files ship in the bundle."""
    from ui.main_window import MIN_SIZE, TABS
    from ui.resources import icon_path, resource_dir
    assert window.minimumWidth() == MIN_SIZE[0] and window.minimumHeight() == MIN_SIZE[1]
    assert MIN_SIZE[0] <= 1366 and MIN_SIZE[1] <= 728
    assert window.nav.count() == len(TABS) == 7
    assert not window.windowIcon().isNull()
    assert icon_path().exists()
    for name in ("seqopt.ico", "seqopt.icns", "seqopt.png"):
        assert (resource_dir() / "assets" / name).exists()


def test_diag_tab_warns_about_dominant_condition(window):
    """It says that one condition carries ~48% of the variance (F-13)."""
    assert not window.tab_diag.gwarn.isHidden()             # a dominant condition exists
    assert "48%" in window.tab_diag.warn_text.text()
    assert "180 · 6" in window.tab_diag.warn_text.text()


def test_prescription_says_how_to_pass(window):
    """The prescription card — a target D back-computes the replicates (F-16)."""
    from core.diagnostics import discriminability, required_reps

    disc = discriminability(window.dataset.reps)
    n = required_reps(disc.sigma_b, disc.sigma_w, 2.0)
    window.tab_diag.target_d.setValue(2.0)
    assert f"<b>{n}×</b>" in window.tab_diag.pre_text.text()


def test_terrain_reports_noise_share(window):
    """Most of the visible variation is measurement wobble — and the screen says the number."""
    from core.diagnostics import discriminability, nugget_ratio

    disc = discriminability(window.dataset.reps)
    n = nugget_ratio(window.dataset.XN, window.dataset.y_mean, sigma_w=disc.sigma_w)
    assert f"{n.noise_share * 100:.0f}%" in window.tab_diag.terrain.text()
    assert "rough surface" in window.tab_diag.terrain.text().lower()


def test_budget_bar_shows_overrun_instead_of_capping(window):
    """66 already-measured rows loaded into a 40-run plan. The overshoot is not hidden."""
    assert window.project.used == 66
    assert window.budget_bar.value() == 66
    assert "66 / 40" in window.budget_bar.format()


# ══════════════════════════════════════════════════════════════════════
# The data table
# ══════════════════════════════════════════════════════════════════════
def test_data_tab_undo_redo(qapp):
    """Without undo, one slip costs the whole table."""
    from ui.tab_data import DataTab

    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    p.add([1.0], 0.5)
    tab = DataTab(p)
    tab._add_row()
    assert len(p.measurements) == 2
    tab.undo()
    assert len(p.measurements) == 1
    tab.redo()
    assert len(p.measurements) == 2


def test_excluded_rows_leave_the_dataset(qapp):
    """The exclude checkbox removes from the math, not from the file — raw data stays (P4)."""
    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    p.add([1.0], 0.5)
    p.add([2.0], 0.9)
    p.measurements[1]["excluded"] = True
    assert p.dataset().n_conditions == 1
    assert len(p.measurements) == 2
    assert p.used == 1


def test_paste_parses_excel_tab_separated(qapp, monkeypatch):
    """Copy-paste from Excel — the most common way data gets in."""
    from PySide6.QtWidgets import QApplication, QMessageBox
    from ui.tab_data import DataTab

    p = Project(inputs=[VarSpec("power", "W", "continuous", 150, 200, step=10.0),
                        VarSpec("dwell", "s", "integer", 3, 7)],
                objective=ObjSpec("G/D"))
    tab = DataTab(p)
    QApplication.clipboard().setText(
        "power\tdwell\tG/D\n150\t7\t1.20\n150\t7\t1.19\n160\t5\t1.31\n")
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    tab.paste_clipboard()
    assert len(p.measurements) == 3                 # the header line is skipped
    assert p.dataset().n_conditions == 2            # 150·7 groups into replicates
