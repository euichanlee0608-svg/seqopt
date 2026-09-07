# -*- coding: utf-8 -*-
"""Reports — PDF · calculation log · reproduction script (F-40 ~ F-43).

**A report is a copy of the evidence, not a photo of the screen.** Three things
always go in.
  · the verdict and its **worked calculation** (principle P4 — every number must trace back)
  · a raw-data summary (how many conditions · how many runs · what was excluded)
  · if it was generated with requirements unmet, **the stamp on the cover** (§10 risk table)

Never imports the GUI. Runs as-is from the CLI.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib
import numpy as np

from .acquisition import make_acquisition
from .diagnostics import (D_THRESHOLD, NUGGET_THRESHOLD, DiscResult, Gate, LoocvResult,
                          NuggetResult, discriminability, loocv_r2, nugget_ratio)
from .fonts import register_pdf_font
from .i18n import tr
from .plotstyle import (C_AXIS, C_BAND, C_BEST, C_MEAN, C_POINT, C_RAW, CMAP_EI,
                        CMAP_MU, CMAP_SD, apply_style)
from .spec import Dataset, candidate_summary
from .surface import curve_1d, grid_2d, replicate_scatter, trajectory
from .surrogate import fit

MARK = {"OK": "○", "FAIL": "×", "UNDECIDED": "△", "WARN": "△",
        "PENDING": "…", "UNCOMPUTABLE": "—"}


@dataclass
class ReportData:
    """Everything the report needs, received as **values**, not screens."""

    project: object
    dataset: Dataset
    gate: Gate
    disc: DiscResult
    loocv: LoocvResult | None
    nugget: NuggetResult | None
    model: object | None = None
    gate_bypassed: bool = False

    @classmethod
    def compute(cls, project, gate_bypassed: bool = False) -> "ReportData":
        """Compute everything from one project. Slow (includes LOOCV) — call it in the background."""
        from .diagnostics import gate as make_gate

        ds = project.dataset()
        disc = discriminability(ds.reps)
        loo = loocv_r2(ds.XN, ds.y_mean) if ds.n_conditions >= 3 else None
        nug = nugget_ratio(ds.XN, ds.y_mean, sigma_w=disc.sigma_w) if ds.n_conditions >= 3 else None
        model = fit(ds.XN, ds.y_mean) if ds.n_conditions >= 3 else None
        g = make_gate(project.n_candidates(), project.budget_total,
                      loo.r2 if loo else None, disc, ds.frac_with_reps)
        return cls(project, ds, g, disc, loo, nug, model, gate_bypassed)


# ══════════════════════════════════════════════════════════════════════
# Calculation log (F-41)
# ══════════════════════════════════════════════════════════════════════
def calculation_log(data: ReportData) -> str:
    """Every number's formula and intermediate values. A person must be able to follow it by hand."""
    p, ds, d = data.project, data.dataset, data.disc
    L: list[str] = []
    add = L.append

    add("=" * 78)
    add(tr("{name} — full calculation disclosure", name=p.name))
    add("=" * 78)
    add(tr("generated {ts}", ts=datetime.now().astimezone().isoformat(timespec='seconds')))
    add(tr("  conditions {all} total · {usable} usable (excluded {excl}) · {meas} measurements",
           all=ds.n_conditions_all, usable=ds.n_conditions, excl=ds.n_excluded_conditions,
           meas=ds.n_measurements))
    add(tr("  replicate distribution : {dist}", dist=ds.rep_distribution))
    add(tr("  objective : {name} {goal}{log}", name=p.objective.name,
           goal=tr("maximize") if p.objective.goal == 'max' else tr("minimize"),
           log=tr(" · log10 transform") if p.objective.log else ""))
    add("")

    if d.sigma_w is None:
        add(tr("[step 1] within-condition spread sigma_w — NOT COMPUTABLE (no replicate measurements)"))
        add("         " + tr("No assumed value is substituted. Measure the same condition at least twice."))
    else:
        add(tr("[step 1] within-condition spread sigma_w — the wobble from re-measuring the same condition"))
        add(f"         {tr('condition'):<28}{'n':>4}{tr('mean'):>10}{tr('sample SD'):>10}{'(n-1)*var':>13}")
        for row, x in zip(d.table, ds.X):
            cond = " · ".join(f"{v:g}" for v in x)
            sd = "—" if row["sd"] is None else f"{row['sd']:.4f}"
            add(f"         {cond:<28}{row['n']:>4}{row['mean']:>10.4f}{sd:>10}{row['ss']:>13.6f}")
        add(f"         {tr('total'):<28}{'':>24}{d.total_ss:>13.6f}   " + tr("(dof {n})", n=d.total_df))
        add(f"         sigma_w = sqrt({d.total_ss:.6f} / {d.total_df}) = {d.sigma_w:.4f}")  # i18n: skip
        add("")
        add(tr("[step 2] between-condition spread sigma_b — the difference that changing the condition makes"))
        add("         " + tr("sample SD of the {n} condition means", n=ds.n_conditions))
        add("         " + tr("sigma_b = {b}   (grand mean {g})",
                              b=f"{d.sigma_b:.4f}", g=f"{ds.y_mean.mean():.4f}"))
        add("")
        add(tr("[step 3] discriminability D = sigma_b / (sigma_w / sqrt(n))"))
        for n, v in d.D.items():
            mark = "  " + tr("<- current (single-replicate basis)") if n == 1 else ""
            add(f"         n={n} : {d.sigma_b:.4f} / {d.sigma_w / np.sqrt(n):.4f} = {v:.2f}{mark}")
        add("         " + tr("note: values for larger n are projections — they hold only if sigma_w "
                              "stays the same."))
        if d.ci_lo is not None:
            add("")
            add(tr("[step 3-1] how solid is this estimate"))
            add("         " + tr("condition bootstrap, 4000 draws : D(n=1) 95% interval = [{lo}, {hi}]",
                                  lo=f"{d.ci_lo:.2f}", hi=f"{d.ci_hi:.2f}"))
            verdict = {"OK": tr("clears the threshold"), "FAIL": tr("falls short of the threshold"),
                       "UNDECIDED": tr("the threshold sits inside the interval — cannot be settled")}[d.verdict]
            add("         " + tr("against threshold {t} : {v}", t=f"{D_THRESHOLD:g}", v=verdict))
        if d.top_share is not None and d.top_condition is not None:
            top = " · ".join(f"{v:g}" for v in ds.X[d.top_condition])
            add("         " + tr("{pct}% of the within-condition variance comes from one condition ({top}).",
                                  pct=f"{d.top_share:.0f}", top=top))
            if d.D_drop_top is not None:
                add("         " + tr("dropping it gives sigma_w={a} · D(n=1)={b}",
                                      a=f"{d.sigma_w_drop_top:.4f}", b=f"{d.D_drop_top:.2f}"))

    if data.loocv is not None:
        r = data.loocv
        add("")
        add(tr("[step 4] surface learnability — LOOCV prediction of the condition means"))
        add("         " + tr("leave one condition out, fit on the rest ({n} conditions)", n=ds.n_conditions))
        add(f"         SS_res = {r.ss_res:.4f} · SS_tot = {r.ss_tot:.4f}")  # i18n: skip
        add(f"         R^2 = 1 - {r.ss_res:.4f}/{r.ss_tot:.4f} = {r.r2:+.3f}")
        if r.r2 <= 0:
            add("         " + tr("R^2 <= 0 means worse than always answering the overall mean."))
        if r.low_sample_warning:
            add("         " + tr("note: fewer than 8 conditions — low-sample warning"))

    if data.nugget is not None:
        n = data.nugget
        add("")
        add(tr("[step 5] terrain roughness — semivariogram"))
        add("         " + tr("nugget {a} / sill {b} = nugget ratio {c}",
                              a=f"{n.nugget:.3f}", b=f"{n.sill:.3f}", c=f"{n.ratio:.3f}"))
        add("         " + tr("against threshold {t} : {v}", t=f"{NUGGET_THRESHOLD}",
                              v=tr("rough surface") if n.rough else tr("smooth surface")))
        if n.noise_share is not None:
            add("         " + tr("{pct}% of the visible variation is measurement wobble.",
                                  pct=f"{n.noise_share * 100:.0f}"))

    add("")
    add(tr("[gate verdict]"))
    g = data.gate
    add("         " + tr("① evidence : {ev} vs budget {b} runs",
                          ev=candidate_summary(p.inputs, p.constraint), b=p.budget_total))
    if p.constraint is not None:
        add("         " + tr("constraint : {c}", c=p.constraint.describe()))
    for label, state in ((tr("① candidate count"), g.cond_count), (tr("② learnability"), g.learnable),
                         (tr("③ discriminability"), g.discrim), (tr("④ replicates"), g.replicates)):
        add(f"         {label}  {MARK.get(state, '—')}  ({state})")
    add("         " + tr("→ recommendation {r}", r=tr("LOCKED") if g.locked else tr("available")))
    for reason in g.reasons:
        add(f"           · {reason}")
    if data.gate_bypassed:
        add("")
        add("         " + tr("[caution] this report was force-generated with requirements unmet."))
    return "\n".join(L)


# ══════════════════════════════════════════════════════════════════════
# Reproduction script (F-43)
# ══════════════════════════════════════════════════════════════════════
def reproduce_script(data: ReportData) -> str:
    """A Python script that recomputes the current state exactly.

    Must run without the GUI and reproduce the report's numbers.
    """
    p, ds = data.project, data.dataset
    rows = ",\n    ".join(
        f"dict(inputs={[float(v) for v in m['inputs']]}, value={float(m['value'])!r}, "  # i18n: skip
        f"excluded={bool(m.get('excluded'))}, pending={bool(m.get('pending'))})"
        for m in p.measurements)
    inputs = ",\n    ".join(
        f"VarSpec({v.name!r}, {v.unit!r}, {v.type!r}, {v.lo!r}, {v.hi!r}"
        + (f", levels={v.levels!r}" if v.levels else "")
        + (f", step={v.step!r}" if v.step is not None else "") + ")" for v in p.inputs)
    con = (f"SumConstraint({p.constraint.names!r}, {p.constraint.total!r}, {p.constraint.kind!r})"
           if p.constraint else "None")
    o = p.objective
    home = Path(__file__).resolve().parent.parent

    # User-facing text inside the generated script (docstring, comments, print labels) is
    # baked in the current language now; the numbers/identifiers stay Python.
    title = tr("{name} — reproduction script (auto-generated {ts})",
               name=p.name, ts=datetime.now().strftime("%Y-%m-%d %H:%M"))
    about = tr("This one file reproduces the report's numbers. Run it from any folder.\n"
               "Requires: numpy · scipy · scikit-learn==1.8.0 and seqopt's core/ package.")
    encoding_note = tr("# The Windows console (cmd) defaults to a legacy encoding and can die printing\n"
                        "# non-ASCII characters (user-entered names included). Two lines prevent that.")
    home_note = tr("# Where the seqopt that generated this script lives. Moved it? Edit this line only.")
    infinite_word = tr("infinite")
    usable_line = tr("usable conditions {n} · {m} measurements · selectable conditions {c}",
                      n="{ds.n_conditions}", m="{ds.n_measurements}",
                      c="{count_candidates(INPUTS, CONSTRAINT) or " + repr(infinite_word) + "}")
    report_val_w = tr("(report value {v})",
                       v=f"{data.disc.sigma_w if data.disc.sigma_w else float('nan'):.4f}")
    report_val_b = tr("(report value {v})", v=f"{data.disc.sigma_b:.4f}")
    nugget_line = tr("nugget ratio = {v}", v="{nug.ratio:.3f}")
    nugget_na = tr("nugget ratio = not computable (too few conditions)")
    locked_word = tr("LOCKED")
    available_word = tr("available")
    rec_label = tr("recommendation")

    return f'''# -*- coding: utf-8 -*-
"""{title}

{about}
"""
import sys
from pathlib import Path

{encoding_note}
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

{home_note}
SEQOPT_HOME = Path(r"{home}")
if SEQOPT_HOME.is_dir() and str(SEQOPT_HOME) not in sys.path:
    sys.path.insert(0, str(SEQOPT_HOME))

from core.dataset import from_measurements
from core.diagnostics import discriminability, gate, loocv_r2, nugget_ratio
from core.spec import ObjSpec, SumConstraint, VarSpec, count_candidates

INPUTS = [
    {inputs},
]
CONSTRAINT = {con}
OBJECTIVE = ObjSpec({o.name!r}, {o.unit!r}, {o.goal!r}, log={o.log!r})
BUDGET = {p.budget_total}
EXCLUDE_ZERO = {p.exclude_zero!r}

MEASUREMENTS = [
    {rows},
]

ds = from_measurements(MEASUREMENTS, INPUTS, OBJECTIVE, exclude_zero=EXCLUDE_ZERO)
disc = discriminability(ds.reps)
loo = loocv_r2(ds.XN, ds.y_mean)
nug = nugget_ratio(ds.XN, ds.y_mean, sigma_w=disc.sigma_w)
g = gate(count_candidates(INPUTS, CONSTRAINT), BUDGET, loo.r2, disc, ds.frac_with_reps)

print(f"{usable_line}")
print(f"sigma_w = {{disc.sigma_w:.4f}}   {report_val_w}")
print(f"sigma_b = {{disc.sigma_b:.4f}}   {report_val_b}")
print(f"D(n=1)  = {{disc.D[1]:.3f}}")
print(f"R^2     = {{loo.r2:+.3f}}")
print(f"{nugget_line}" if nug else "{nugget_na}")
print(f"{rec_label} {{{locked_word!r} if g.locked else {available_word!r}}}")
'''  # i18n: skip -- the rest of this template is Python syntax; the prose above is tr()'d


# ══════════════════════════════════════════════════════════════════════
# Figures (PNGs that go into the PDF)
# ══════════════════════════════════════════════════════════════════════
def _png(fig) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    matplotlib.pyplot.close(fig)
    buf.seek(0)
    return buf


def report_figures(data: ReportData) -> list[tuple[str, io.BytesIO]]:
    """The report's figures. Same color language as the screen."""
    import matplotlib.pyplot as plt

    apply_style()
    ds, out = data.dataset, []

    # Replicate scatter — the raw material of discriminability, shown as-is
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    _, reps, means = replicate_scatter(ds)
    for k, v in enumerate(reps):
        ax.scatter([k] * len(v), v, s=20, c=C_RAW, zorder=3)
    ax.plot(range(len(means)), means, color=C_MEAN, lw=1.4, label=tr("condition mean"))
    ax.set_xlabel(tr("condition (sorted by mean)"))
    ax.set_ylabel(data.project.objective.name)
    ax.set_title(tr("Replicate scatter — how much re-measuring the same condition wobbles"))
    ax.legend(loc="best")
    out.append((tr("Replicate scatter"), _png(fig)))

    # LOOCV scatter — makes R² < 0 visible
    if data.loocv is not None:
        fig, ax = plt.subplots(figsize=(3.5, 3.0))
        y, pred = ds.y_mean, data.loocv.pred
        ax.scatter(y, pred, s=26, c=C_POINT, edgecolors="white", linewidths=0.6, zorder=5)
        lim = [min(y.min(), pred.min()), max(y.max(), pred.max())]
        ax.plot(lim, lim, color=C_AXIS, lw=1, label=tr("perfect prediction"))
        ax.axhline(y.mean(), color=C_BEST, ls="--", lw=1.2, label=tr("always answer the mean"))
        ax.set_xlabel(tr("measured (condition mean)"))
        ax.set_ylabel(tr("LOOCV prediction"))
        ax.set_title(tr("Learnability R² = {r2}", r2=f"{data.loocv.r2:+.3f}"))
        ax.legend(loc="best", fontsize=7)
        out.append((tr("Learnability"), _png(fig)))

    # Semivariogram
    if data.nugget is not None:
        n = data.nugget
        fig, ax = plt.subplots(figsize=(3.5, 3.0))
        ax.plot(n.bin_centers, n.bin_gamma, "o-", color=C_MEAN, ms=4, lw=1.4)
        ax.axhline(n.sill, color=C_AXIS, ls="--", lw=1, label=tr("sill {v}", v=f"{n.sill:.2f}"))
        ax.axhline(n.nugget, color=C_BEST, ls=":", lw=1.2, label=tr("nugget {v}", v=f"{n.nugget:.2f}"))
        ax.set_xlabel(tr("distance between conditions (normalized)"))
        ax.set_ylabel(tr("semivariance γ"))
        ax.set_title(tr("Terrain roughness — nugget ratio {v}", v=f"{n.ratio:.3f}"))
        ax.legend(loc="best", fontsize=7)
        out.append((tr("Terrain"), _png(fig)))

    # Response surface — 1 or 2 variables only (3+ needs a slice choice; use the screen)
    if data.model is not None and ds.XN.shape[1] in (1, 2):
        acq = make_acquisition()
        best = float(max(v.max() for v in ds.reps))
        if ds.XN.shape[1] == 1:
            c = curve_1d(data.model, ds, best, acq)
            fig, ax = plt.subplots(figsize=(7.2, 3.0))
            ax.fill_between(c.x_real, c.mu - 2 * c.sd, c.mu + 2 * c.sd,
                            color=C_BAND, alpha=0.45, lw=0, label="μ ± 2σ")
            ax.plot(c.x_real, c.mu, color=C_MEAN, lw=2, label=tr("predicted mean"))
            for x, v in zip(ds.X[:, 0], ds.reps):
                ax.scatter([x] * len(v), v, s=20, c=C_POINT, zorder=5)
            ax.set_xlabel(data.project.inputs[0].name)
            ax.set_ylabel(data.project.objective.name)
            ax.set_title(tr("Response surface"))
            ax.legend(loc="best", fontsize=7)
        else:
            g = grid_2d(data.model, ds, best, acq, 0, 1, None, n=50)
            extent = [g.x_real[0], g.x_real[-1], g.y_real[0], g.y_real[-1]]
            fig, axes = plt.subplots(1, 3, figsize=(7.6, 2.6))
            for ax, (title, Z, cmap) in zip(axes, [
                    (tr("predicted mean μ"), g.mu, CMAP_MU),
                    (tr("uncertainty σ"), g.sd, CMAP_SD),
                    (tr("EI — where to measure next"), g.ei, CMAP_EI)]):
                im = ax.imshow(Z, origin="lower", extent=extent, aspect="auto", cmap=cmap)
                fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
                ax.scatter(ds.X[:, 0], ds.X[:, 1], s=12, c=C_POINT,
                           edgecolors="white", linewidths=0.4, zorder=5)
                ax.set_title(title, fontsize=8)
                ax.set_xlabel(data.project.inputs[0].name, fontsize=7)
                ax.set_ylabel(data.project.inputs[1].name, fontsize=7)
                ax.grid(False)
        out.append((tr("Response surface"), _png(fig)))

    # Trajectory
    n, run = trajectory(data.project.measurements, data.project.objective)
    if len(n):
        fig, ax = plt.subplots(figsize=(3.5, 2.6))
        ax.step(n, run, where="post", color=C_MEAN, lw=1.6)
        ax.set_xlabel(tr("measurements (cumulative)"))
        ax.set_ylabel(data.project.objective.name)
        ax.set_title(tr("Trajectory — best measured value so far"))
        out.append((tr("Trajectory"), _png(fig)))
    return out


# ══════════════════════════════════════════════════════════════════════
# PDF (F-40)
# ══════════════════════════════════════════════════════════════════════
def write_pdf(data: ReportData, path: str | Path) -> Path:
    """Verdict table + figures + calculation log + raw-data summary. Embeds a CJK font when available."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                    SimpleDocTemplate, Spacer, Table, TableStyle)

    font = register_pdf_font()
    path = Path(path)
    ss = getSampleStyleSheet()

    def style(name, size, leading, color="#212121", bold=False, space=4):
        return ParagraphStyle(name, parent=ss["Normal"], fontName=font, fontSize=size,
                              leading=leading, textColor=colors.HexColor(color),
                              spaceAfter=space)

    H1 = style("H1", 18, 24, bold=True, space=10)
    H2 = style("H2", 12, 17, "#37474f", space=6)
    BODY = style("BODY", 9, 13)
    SMALL = style("SMALL", 7.5, 10.5, "#666666")
    MONO = ParagraphStyle("MONO", parent=ss["Normal"], fontName="Courier", fontSize=6.6,
                          leading=8.4, textColor=colors.HexColor("#333333"))

    p, ds, g, d = data.project, data.dataset, data.gate, data.disc
    flow = []

    # ── cover ──────────────────────────────────────────────────────
    flow.append(Paragraph(p.name, H1))
    flow.append(Paragraph(
        tr("Sequential-optimization diagnostic report · generated {ts}",
           ts=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M')), SMALL))
    flow.append(Spacer(1, 6 * mm))

    if data.gate_bypassed:
        flow.append(Table(
            [[Paragraph(tr("CAUTION — generated with requirements unmet. "
                           "The recommendations in this report lack supporting evidence."),
                        style("W", 10, 14, "#b71c1c"))]],
            colWidths=[165 * mm],
            style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fdecea")),
                              ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#f5c6cb")),
                              ("LEFTPADDING", (0, 0), (-1, -1), 8),
                              ("TOPPADDING", (0, 0), (-1, -1), 8),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 8)])))
        flow.append(Spacer(1, 5 * mm))

    # ── gate verdict ───────────────────────────────────────────────
    flow.append(Paragraph(tr("Gate verdict"), H2))
    verdict_rows = [["", tr("requirement"), tr("verdict"), tr("evidence")]]
    r2_txt = f"R² = {data.loocv.r2:+.3f}" if data.loocv else tr("not computed")
    ci = f"[{d.ci_lo:.2f}, {d.ci_hi:.2f}]" if d.ci_lo is not None else ""
    n_rep = sum(1 for v in ds.reps if len(v) > 1)
    verdict_rows += [
        ["①", tr("candidate count"), MARK.get(g.cond_count, "—"),
         tr("{a} vs budget {b}", a=candidate_summary(p.inputs, p.constraint), b=p.budget_total)],
        ["②", tr("surface learnability"), MARK.get(g.learnable, "—"), r2_txt],
        ["③", tr("discriminability"), MARK.get(g.discrim, "—"),
         (f"D = {d.D[1]:.2f} {ci}" if d.sigma_w else tr("no replicates — not computable"))],
        ["④", tr("replicates"), MARK.get(g.replicates, "—"),
         tr("conditions with replicates {a}/{b}", a=n_rep, b=ds.n_conditions)],
    ]
    t = Table(verdict_rows, colWidths=[8 * mm, 34 * mm, 16 * mm, 107 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eceff1")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cfd8dc")),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    flow.append(t)
    flow.append(Spacer(1, 3 * mm))
    flow.append(Paragraph(
        (tr("<b>Recommendation LOCKED</b> — ") + " · ".join(g.reasons)) if g.locked
        else tr("<b>Requirements met</b> — next-candidate recommendation is available."),
        style("V", 9.5, 14, "#b71c1c" if g.locked else "#2e7d32")))
    flow.append(Spacer(1, 6 * mm))

    # ── raw-data summary ───────────────────────────────────────────
    flow.append(Paragraph(tr("Raw data"), H2))
    summary = [
        [tr("conditions (usable / total)"), f"{ds.n_conditions} / {ds.n_conditions_all}"],
        [tr("measurements"), f"{ds.n_measurements}"],
        [tr("replicate distribution"), str(ds.rep_distribution)],
        [tr("objective"), f"{p.objective.name} "
                          f"{tr('maximize') if p.objective.goal == 'max' else tr('minimize')}"
                          f"{tr(' · log10 transform') if p.objective.log else ''}"],
        [tr("inputs"), " · ".join(
            f"{v.name}[{v.lo:g}~{v.hi:g}{' ' + v.unit if v.unit else ''}"
            f"{tr(' · step ') + format(v.step, 'g') if v.step is not None else ''}]"
            if v.type != "categorical" else f"{v.name}[{', '.join(v.levels)}]"
            for v in p.inputs)],
    ] + ([[tr("constraint"), p.constraint.describe()]] if p.constraint else [])
    t = Table(summary, colWidths=[45 * mm, 120 * mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cfd8dc")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f7f8")),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    flow.append(t)

    # ── figures ────────────────────────────────────────────────────
    figs = report_figures(data)
    if figs:
        flow.append(PageBreak())
        flow.append(Paragraph(tr("Figures"), H2))
        for title, buf in figs:
            img = Image(buf)
            scale = min(165 * mm / img.imageWidth, 72 * mm / img.imageHeight)
            img.drawWidth = img.imageWidth * scale
            img.drawHeight = img.imageHeight * scale
            # a caption split from its figure across pages tells the reader nothing
            flow.append(KeepTogether([Paragraph(title, SMALL), img, Spacer(1, 4 * mm)]))

    # ── calculation log (principle P4) ─────────────────────────────
    flow.append(PageBreak())
    flow.append(Paragraph(tr("Calculation log"), H2))
    flow.append(Paragraph(
        tr("Where every number on screen came from, written out. It must be followable by hand."),
        SMALL))
    flow.append(Spacer(1, 2 * mm))
    for line in calculation_log(data).splitlines():
        flow.append(Paragraph(line.replace(" ", "&nbsp;").replace("<", "&lt;") or "&nbsp;",  # i18n: skip
                              MONO))

    def _stamp(canvas, doc):
        """With requirements unmet, stamp every page — capturing one page still carries the warning."""
        canvas.saveState()
        canvas.setFont(font, 7)
        canvas.setFillColor(colors.HexColor("#9e9e9e"))
        canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"{p.name} · p.{doc.page}")
        if data.gate_bypassed:
            canvas.setFont(font, 40)
            canvas.setFillColor(colors.Color(0.83, 0.18, 0.18, alpha=0.10))
            canvas.translate(A4[0] / 2, A4[1] / 2)
            canvas.rotate(28)
            canvas.drawCentredString(0, 0, tr("REQUIREMENTS UNMET"))
        canvas.restoreState()

    SimpleDocTemplate(str(path), pagesize=A4,
                      leftMargin=22 * mm, rightMargin=22 * mm,
                      topMargin=18 * mm, bottomMargin=18 * mm,
                      title=tr("{name} — diagnostic report", name=p.name)).build(
        flow, onFirstPage=_stamp, onLaterPages=_stamp)
    return path
