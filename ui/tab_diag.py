# -*- coding: utf-8 -*-
"""Tab 3, Diagnose — the most important screen (spec §4-2 · F-10 ~ F-17).

This screen is this tool's reason to exist. **Before advice is given, it says
whether the advice can be trusted.** The usability bar (§9-3) hangs here —
someone who opened a spreadsheet with no instructions has to be able to say,
within five minutes, "why optimization should not be used right now."

Hence four screen rules.
  · Verdicts are written as **sentences**, not symbols ("conditions 25 > budget 40 ?" reads backwards)
  · Every number **unfolds into its calculation** (principle P4) — formulas are typeset as real formulas
  · Near the threshold, the point estimate is not celebrated — the screen says **undecided** (principle P5)
  · **Thresholds carry their basis** — someone with no statistics must be able
    to ask "why 2". Values and their basis come from core.diagnostics.D_LEVELS alone.
"""
from __future__ import annotations

import html

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
                               QLabel, QScrollArea, QSizePolicy, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from core.diagnostics import (BOOTSTRAP_DRAWS, D_LEVELS, D_RECOMMENDED, D_THRESHOLD,
                              NUGGET_CLASSES, NUGGET_THRESHOLD, replicate_plan, required_reps)
from core.i18n import tr
from core.spec import candidate_summary
from . import theme
from .widgets.advanced import Advanced
from .widgets.gauge import DGauge
from .widgets.mathtext import FormulaCard
from .widgets.section import PageHeader, Section, link_button, tell_true_height

MARK = theme.STATE_MARK
COLOR = theme.STATE_COLOR


class _Row(QWidget):
    """One requirement line: mark · name · sentence · criterion."""

    def __init__(self, title: str, criterion: str, parent=None):
        super().__init__(parent)
        h = QHBoxLayout(self)
        h.setContentsMargins(4, 4, 4, 4)
        h.setSpacing(10)
        self.mark = QLabel("—")                                  # i18n: skip (a state symbol, not a word)
        self.mark.setFixedWidth(26)
        self.mark.setAlignment(Qt.AlignCenter)
        f = self.mark.font()
        f.setPixelSize(theme.FONT_SIZE + 5)
        f.setBold(True)
        self.mark.setFont(f)
        self.title = QLabel(title)
        self.title.setStyleSheet("font-weight:600;")             # i18n: skip (a style sheet)
        self.text = QLabel("—")                                  # i18n: skip (a placeholder dash)
        self.text.setWordWrap(True)
        tell_true_height(self.text)
        self.text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.criterion = QLabel(criterion)
        self.criterion.setObjectName("pill")
        self.criterion.setAlignment(Qt.AlignCenter)
        h.addWidget(self.mark)
        h.addWidget(self.title)
        h.addWidget(self.text, 1)
        h.addWidget(self.criterion, 0, Qt.AlignTop)

    def set(self, state: str, text: str) -> None:
        self.mark.setText(MARK.get(state, "—"))
        self.mark.setStyleSheet(f"color:{COLOR.get(state, theme.TEXT_FAINT)};")
        self.text.setText(text)


def _fit_height(table: QTableWidget, max_rows: int = 12) -> None:
    """The page itself scrolls, so tables grow to content (capped at max_rows)."""
    rows = min(table.rowCount(), max_rows)
    h = table.horizontalHeader().sizeHint().height() + rows * theme.ROW_HEIGHT + 2 * table.frameWidth()
    if table.rowCount() > max_rows:
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    table.setFixedHeight(h + 2)




def _hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"color:{theme.BORDER};")
    return line


class DiagTab(QWidget):
    prescription_changed = Signal()
    help_requested = Signal(str)

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.disc = None
        self.nugget = None
        self.loocv = None
        self._build()

    # ── screen ─────────────────────────────────────────────────────
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        head = PageHeader(tr("Diagnose — can this data be trusted"),
                          tr("Four requirements are checked before any recommendation. "
                             "Failing any one locks it."))
        # The header row is the title plus these links; four of them no longer fit beside an
        # English title at 1024 px, so the two that belong to one card moved onto that card.
        for label, key in ((tr("The four requirements?"), "gate"), (tr("Discriminability?"), "d")):
            head.add_right(self._help_link(label, key))
        root.addWidget(head)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        bv = QVBoxLayout(body)
        bv.setContentsMargins(0, 0, 6, 0)
        bv.setSpacing(12)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        # ── gate verdict ───────────────────────────────────────────
        gate = Section(tr("Gate verdict"),
                       tr("All four lines must be ○ for recommendations to open. "
                          "The right side is each requirement's criterion."))
        self.r1 = _Row(tr("① candidate count"), tr("candidates > budget"))
        self.r2 = _Row(tr("② surface learnability"), "R² > 0")            # i18n: skip (symbols only)
        self.r3 = _Row(tr("③ discriminability"),
                       tr("D > {gate} · recommended ≥ {rec}",
                          gate=f"{D_THRESHOLD:g}", rec=f"{D_RECOMMENDED:g}"))
        self.r4 = _Row(tr("④ replicates"), tr("≥ 50% with replicates"))
        rows = (self.r1, self.r2, self.r3, self.r4)
        # One name column, as wide as the widest name in *this* language — never a pixel guess
        name_w = max(r.title.sizeHint().width() for r in rows) + 6
        for r in rows:
            r.title.setFixedWidth(name_w)
            gate.add(r)
        self.verdict = QLabel()
        self.verdict.setWordWrap(True)
        tell_true_height(self.verdict)
        self.verdict.setStyleSheet(theme.card("plain"))
        gate.add(self.verdict)
        gate.add_link(self._help_link(tr("R² is negative?"), "r2"))     # requirement ②'s "why?"
        bv.addWidget(gate)

        cols = QHBoxLayout()
        cols.setSpacing(12)
        left = QVBoxLayout()
        left.setSpacing(12)
        right = QVBoxLayout()
        right.setSpacing(12)
        cols.addLayout(left, 1)
        cols.addLayout(right, 1)
        bv.addLayout(cols)

        # ── left: the D gauge ──────────────────────────────────────
        level = Section(tr("Discriminability D — which zone are you in"),
                        tr("The difference that changing conditions makes (σb), divided by the "
                           "wobble of re-measuring the same condition (σw). The larger it is, "
                           "the further condition differences rise above the noise."))
        self.gauge = DGauge()
        level.add(self.gauge)
        self.reading = QLabel("—")                               # i18n: skip (a placeholder dash)
        self.reading.setWordWrap(True)
        tell_true_height(self.reading)
        level.add(self.reading)
        self.levels = QLabel()
        self.levels.setWordWrap(True)
        tell_true_height(self.levels)
        self.levels.setTextFormat(Qt.RichText)
        self.levels.setText(self._levels_html())
        level.add(self.levels)
        why = QHBoxLayout()                          # the "why these numbers?" link, under them
        why.addWidget(self._help_link(tr("Why 1 · 2 · 3.5?"), "levels"))
        why.addStretch(1)
        level.add_layout(why)
        left.addWidget(level)
        left.addStretch(1)

        # ── full width, under both columns: the calculation ────────
        # Formula · prose · a five-column table do not fit in half of a 1024 px window —
        # this card gets the whole width, so nothing here is squeezed in either language.
        calc = Section(tr("The calculation — where this number came from"),
                       tr("The general formula first, then the same formula with this data's values. "
                          "Unfold the per-condition table to see the raw material."))
        self.toggle = link_button(tr("Unfold the per-condition table ▾"))
        self.toggle.setCheckable(True)
        self.toggle.toggled.connect(self._toggle_table)
        calc.add_link(self.toggle)
        self.formula = FormulaCard()
        calc.add(self.formula)

        self.calc_legend = QLabel()
        self.calc_legend.setWordWrap(True)
        tell_true_height(self.calc_legend)
        self.calc_legend.setStyleSheet(theme.card("info"))
        self.calc_legend.setVisible(False)
        calc.add(self.calc_legend)

        self.calc = QTableWidget(0, 5)
        self.calc.setHorizontalHeaderLabels(
            [tr("condition"), tr("n\n(replicates)"), tr("mean"), tr("sample SD\n(wobble)"),
             tr("(n−1)·var\n(σw share)")])
        # Column titles alone do not carry the meaning; tooltips on the header do.
        for col, tip in enumerate([
                tr("The combination of input values, in the order defined on the Setup tab."),
                tr("How many times this condition was measured. 1 means its wobble is unknowable."),
                tr("The mean of those replicates — the raw material of σb."),
                tr("How much those replicates scatter (sample standard deviation)."),
                tr("This condition's share of σw. Summed and divided by the dof, it gives σw².")]):
            item = self.calc.horizontalHeaderItem(col)
            if item is not None:
                item.setToolTip(tip)
        self.calc.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.calc.verticalHeader().setVisible(False)
        self.calc.setEditTriggers(QTableWidget.NoEditTriggers)
        self.calc.setAlternatingRowColors(True)
        self.calc.verticalHeader().setDefaultSectionSize(theme.ROW_HEIGHT)
        self.calc.setVisible(False)
        self.calc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        calc.add(self.calc)

        # ── right: prescription · warning · terrain ────────────────
        plan = Section(tr("Prescription — how many replicates"),
                       tr("For each target discriminability: replicates per condition, and how many "
                          "more measurements that costs. The recommended row is green."))
        self.plan = QTableWidget(0, 4)
        # Two-line headers: four columns of prose do not fit beside the gauge at 1024 px
        self.plan.setHorizontalHeaderLabels(
            [tr("target\nD"), tr("meaning"), tr("reps per\ncondition"), tr("extra\nruns")])
        for col, tip in enumerate([
                tr("The discriminability you want to reach."),
                tr("What that mark means (core/diagnostics.py: D_LEVELS)."),
                tr("How many times each condition would have to be measured."),
                tr("How many measurements that adds, over every condition together.")]):
            item = self.plan.horizontalHeaderItem(col)
            if item is not None:
                item.setToolTip(tip)
        self.plan.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.plan.verticalHeader().setVisible(False)
        self.plan.setEditTriggers(QTableWidget.NoEditTriggers)
        self.plan.setSelectionMode(QTableWidget.NoSelection)
        self.plan.verticalHeader().setDefaultSectionSize(theme.ROW_HEIGHT)
        self.plan.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.plan.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        plan.add(self.plan)
        self.plan_note = QLabel()
        self.plan_note.setWordWrap(True)
        tell_true_height(self.plan_note)
        theme.set_role(self.plan_note, "desc")
        plan.add(self.plan_note)
        # A custom target can be tried directly. Rarely changed, so it folds away.
        self.adv_pre = Advanced(label=tr("Compute for another target"))
        trow = QHBoxLayout()
        trow.addWidget(QLabel(tr("Target discriminability")))
        self.target_d = QDoubleSpinBox(minimum=0.5, maximum=20.0, singleStep=0.1,
                                       value=D_RECOMMENDED)
        self.target_d.valueChanged.connect(self._update_prescription)
        trow.addWidget(self.target_d)
        trow.addStretch(1)
        self.adv_pre.add_layout(trow)
        self.pre_text = QLabel("—")                              # i18n: skip (a placeholder dash)
        self.pre_text.setWordWrap(True)
        tell_true_height(self.pre_text)
        self.adv_pre.add(self.pre_text)
        plan.add(self.adv_pre)
        right.addWidget(plan)

        self.gwarn = Section(tr("Warning — one condition dominates D"))
        self.warn_text = QLabel("—")                             # i18n: skip (a placeholder dash)
        self.warn_text.setWordWrap(True)
        tell_true_height(self.warn_text)
        self.gwarn.add(self.warn_text)
        right.addWidget(self.gwarn)

        ter = Section(tr("Terrain — is the response surface smooth"),
                      tr("When even nearby conditions differ wildly (a large nugget), "
                         "the model has little to learn from."))
        self.terrain = QLabel("—")                               # i18n: skip (a placeholder dash)
        self.terrain.setWordWrap(True)
        tell_true_height(self.terrain)
        ter.add(self.terrain)
        right.addWidget(ter)
        right.addStretch(1)

        bv.addWidget(calc)
        bv.addStretch(1)

    def _help_link(self, label: str, topic: str):
        """A "why?" link that opens a help topic (main_window connects `help_requested`)."""
        b = link_button(label)
        b.clicked.connect(lambda _=False, k=topic: self.help_requested.emit(k))
        return b

    def _levels_html(self) -> str:
        """The D marks and their basis. Only the two short cells hold their line — meaning and
        basis wrap, or this table alone would set the width of the whole page (both languages)."""
        esc = html.escape
        nowrap = "padding:3px 10px 3px 0; white-space:nowrap"                     # i18n: skip (CSS)
        wrap = f"padding:3px 10px 3px 0; color:{theme.TEXT_MUTED}"                # i18n: skip (CSS)
        rows = "".join(
            f"<tr><td style='{nowrap}'><b>D ≥ {v:g}</b></td>"                     # i18n: skip (markup)
            f"<td style='{nowrap}'>{esc(tr(name))}</td>"                          # i18n: skip (markup)
            f"<td style='{wrap}'>{esc(tr(meaning))}</td>"                         # i18n: skip (markup)
            f"<td style='{wrap}; padding-right:0'>{esc(tr(basis))}</td></tr>"     # i18n: skip (markup)
            for v, name, meaning, basis in D_LEVELS)
        return (f"<span style='font-size:{theme.SMALL}px'>"                       # i18n: skip (markup)
                f"<span style='color:{theme.TEXT_FAINT}'>{esc(tr('thresholds and their basis'))}</span>"
                f"<table cellspacing='0'>{rows}</table></span>")                  # i18n: skip (markup)

    def _toggle_table(self, on: bool) -> None:
        self.calc.setVisible(on)
        self.calc_legend.setVisible(on)
        self.calc_legend.setText(tr(
            "<b>How to read this table</b> — one row is one condition. "
            "<b>n</b> is how many times it was measured, <b>sample SD</b> how much those "
            "replicates wobbled, and <b>(n−1)·var</b> that wobble's share of the total σw. "
            "The σw · σb · D in the formulas above come straight from these numbers."))
        self.toggle.setText(tr("Fold the per-condition table ▴") if on
                            else tr("Unfold the per-condition table ▾"))

    # ── updates ────────────────────────────────────────────────────
    def set_fast(self, disc, nugget) -> None:
        self.disc = disc
        self.nugget = nugget
        self._fill_calc()
        self._fill_gauge()
        self._fill_plan()
        self._update_prescription()
        self._fill_terrain()

    def set_pending(self) -> None:
        self.loocv = None

    def set_slow(self, loocv) -> None:
        self.loocv = loocv

    def refresh(self, dataset, gate) -> None:
        """Redraw the verdict table. The gate comes from main_window as-is."""
        p = self.project
        d = self.disc

        # ① candidate count — the conditions there are to choose from in the design space (SPEC_AMENDMENTS A6)
        where = candidate_summary(p.inputs, p.constraint)
        if gate.cond_count == "OK":
            t = tr("{where} > budget {budget} — there is room to choose",
                   where=where, budget=p.budget_total)
        else:
            t = tr("{where} ≤ budget {budget} — <b>measuring everything is better</b> "
                   "(the gain from optimizing is zero in principle). A finer step or a wider "
                   "range gives more candidates.", where=where, budget=p.budget_total)
        self.r1.set(gate.cond_count, t)

        # ② learnability
        if self.loocv is None:
            self.r2.set("PENDING", tr("Computing… (many conditions can take tens of seconds)"))
        else:
            r2 = self.loocv.r2
            note = tr(" · fewer than 8 conditions, so the sample is thin") \
                if self.loocv.low_sample_warning else ""
            if r2 > 0:
                t = tr("Learnability R² = {r2} — the surface is being learned{note}",
                       r2=f"{r2:+.3f}", note=note)
            else:
                t = tr("Learnability R² = {r2} ≤ 0 — <b>worse than always answering the overall "
                       "mean</b>. The model has learned nothing{note}", r2=f"{r2:+.3f}", note=note)
            self.r2.set(gate.learnable, t)

        # ③ discriminability
        if d is None or d.sigma_w is None:
            self.r3.set("UNCOMPUTABLE",
                        tr("No replicate measurements, so it cannot be computed. No assumed value "
                           "is substituted — measure the same condition at least twice."))
        else:
            ci = f" [{d.ci_lo:.2f}, {d.ci_hi:.2f}]" if d.ci_lo is not None else ""
            base = f"D = {d.D[1]:.2f}{ci}"                        # i18n: skip (a number and its interval)
            if gate.discrim == "OK":
                t = tr("{base} — condition differences can be told apart", base=base)
                if d.D[1] < D_RECOMMENDED:
                    t += tr(". Past the gate, but short of the recommended {rec} — raising "
                            "replicates per the prescription steadies the recommendations",
                            rec=f"{D_RECOMMENDED:g}")
            elif gate.discrim == "FAIL":
                t = tr("{base} — the measurement wobble exceeds the condition differences", base=base)
            else:
                t = tr("{base} — <b>undecided</b>. The 95% interval straddles the gate at {gate}. "
                       "This data cannot settle passed-or-failed either way.",
                       base=base, gate=f"{D_THRESHOLD:g}")
            self.r3.set(gate.discrim, t)

        # ④ replicates
        n_rep = sum(1 for v in dataset.reps if len(v) > 1)
        self.r4.set(gate.replicates,
                    tr("conditions with replicates {n}/{total} ({pct}%)",
                       n=n_rep, total=dataset.n_conditions,
                       pct=f"{n_rep / max(1, dataset.n_conditions) * 100:.0f}"))

        # overall
        if gate.locked:
            why = "<br>".join(f"· {r}" for r in gate.reasons) if gate.reasons else ""
            self.verdict.setText(
                tr("<b>Recommendations are locked</b> — {n} requirement(s) unmet<br>{why}",
                   n=len(gate.reasons), why=why))
            self.verdict.setStyleSheet(theme.card("fail"))
        else:
            self.verdict.setText(
                tr("<b>Requirements met.</b> Get your next candidates on the Recommend tab."))
            self.verdict.setStyleSheet(theme.card("ok"))

    # ── calculation · gauge · prescription · terrain ───────────────
    def _fill_calc(self) -> None:
        d = self.disc
        if d is None:
            return
        names = [v.name for v in self.project.inputs]
        try:
            ds = self.project.dataset()
            labels = [" · ".join(f"{x:g}" for x in row) for row in ds.X]
        except Exception:                            # noqa: BLE001
            labels = [str(r["index"]) for r in d.table]

        # the condition means are internal (negated for a min goal, log10 when asked
        # for); σ and (n−1)·var are magnitudes and do not move, so only the mean is
        # handed back to the user's frame — and the header says when it is a log
        obj = self.project.objective
        head = self.calc.horizontalHeaderItem(2)
        if head is not None:
            head.setText(tr("mean\n(log10)") if obj.log else tr("mean"))

        self.calc.setRowCount(len(d.table))
        top = d.top_condition
        for i, r in enumerate(d.table):
            cells = [labels[i] if i < len(labels) else "?",       # i18n: skip (values, not words)
                     str(r["n"]), f"{obj.to_plot(r['mean']):.4f}",
                     "—" if r["sd"] is None else f"{r['sd']:.4f}", f"{r['ss']:.6f}"]
            for c, txt in enumerate(cells):
                it = QTableWidgetItem(txt)
                it.setForeground(QBrush(QColor(theme.TEXT)))    # a painted background needs a text color too
                if c:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if r["n"] == 1:
                    it.setBackground(QBrush(QColor(theme.ROW_ZERO)))
                    it.setToolTip(tr("Only one replicate, so this condition does not enter "
                                     "the σw calculation."))
                elif i == top:
                    it.setBackground(QBrush(QColor(theme.ROW_EXCLUDED)))
                    it.setToolTip(tr("The condition carrying the largest share of within-condition "
                                     "variance (see the warning on the right)."))
                self.calc.setItem(i, c, it)
        self.calc.resizeColumnsToContents()
        _fit_height(self.calc)

        if d.sigma_w is None:
            self.formula.set_message(
                tr("No condition has replicates, so σw cannot be computed. "
                   "Measure the same condition at least twice."))
            return
        k = len(d.table)
        ci = (tr("95% interval [{lo}, {hi}] — condition bootstrap, {draws} draws",
                 lo=f"{d.ci_lo:.2f}", hi=f"{d.ci_hi:.2f}", draws=BOOTSTRAP_DRAWS)
              if d.ci_lo is not None else tr("too few conditions for an interval"))
        order = " · ".join(names)
        self.formula.set_lines([
            (r"\sigma_w = \sqrt{\frac{\sum_c (n_c-1)\,s_c^2}{\sum_c (n_c-1)}}",   # i18n: skip (TeX)
             tr("within-condition wobble — the dof-weighted average of the replicated "
                "conditions' variances, square-rooted")),
            (r"\sigma_b = \mathrm{SD}\left(\bar{y}_1,\ \ldots,\ \bar{y}_k\right)",  # i18n: skip (TeX)
             tr("between-condition difference — the sample SD of the condition means")),
            (r"D = \frac{\sigma_b}{\sigma_w/\sqrt{n}}",                             # i18n: skip (TeX)
             tr("discriminability — with n replicates per condition, the mean's wobble "
                "shrinks to σw/√n")),
            ("", ""),
            (rf"\sigma_w = \sqrt{{\frac{{{d.total_ss:.6f}}}{{{d.total_df}}}}} = \mathbf{{{d.sigma_w:.4f}}}",   # i18n: skip (TeX)
             tr("Σ(n−1)·s² = {ss}, dof Σ(n−1) = {df}", ss=f"{d.total_ss:.6f}", df=d.total_df)),
            (rf"\sigma_b = \mathrm{{SD}}\left(\bar{{y}}_1,\ \ldots,\ \bar{{y}}_{{{k}}}\right) = \mathbf{{{d.sigma_b:.4f}}}",   # i18n: skip (TeX)
             tr("the means of the {k} conditions (condition order: {order})", k=k, order=order)),
            (rf"D_{{n=1}} = \frac{{{d.sigma_b:.4f}}}{{{d.sigma_w:.4f}}} = \mathbf{{{d.D[1]:.2f}}}",   # i18n: skip (TeX)
             ci),
        ])

    def _fill_gauge(self) -> None:
        d = self.disc
        if d is None or d.sigma_w is None:
            self.gauge.set_value(None)
            self.reading.setText(
                tr("Replicate measurements are needed to compute discriminability."))
            return
        self.gauge.set_value(d.D[1], d.ci_lo, d.ci_hi)
        v = d.D[1]
        if v < D_THRESHOLD:
            zone = tr("The condition differences are <b>smaller</b> than the measurement wobble. "
                      "Right now, which condition is better cannot be told from noise.")
        elif v < D_RECOMMENDED:
            zone = tr("Past the gate, but <b>borderline</b>. Differences are only 1–2× the wobble, "
                      "so rankings can flip. See the prescription on the right to reach the "
                      "recommended {rec}.", rec=f"{D_RECOMMENDED:g}")
        else:
            zone = tr("The condition differences stand <b>clearly</b> above the wobble.")
        straddle = ""
        if d.ci_lo is not None and d.ci_lo <= D_THRESHOLD <= d.ci_hi:
            straddle = tr(" The 95% interval straddles the gate at {gate}, so with this data the "
                          "verdict is <b>undecided</b> — more replicates narrow the interval.",
                          gate=f"{D_THRESHOLD:g}")
        self.reading.setText(zone + straddle)

    def _fill_plan(self) -> None:
        d = self.disc
        self.plan.setRowCount(0)
        if d is None or d.sigma_w is None:
            self.plan_note.setText(tr("Replicate measurements are needed to compute this."))
            return
        try:
            ds = self.project.dataset()
            counts = [len(v) for v in ds.reps]
        except Exception:                            # noqa: BLE001
            counts = [r["n"] for r in d.table]
        try:
            rows = replicate_plan(d.sigma_b, d.sigma_w, counts)
        except ValueError as e:
            self.plan_note.setText(str(e))
            return
        meanings = {lv[0]: lv[1] for lv in D_LEVELS}
        self.plan.setRowCount(len(rows))
        for i, r in enumerate(rows):
            cells = [f"{r['target']:g}", tr(meanings.get(r["target"], "")), f"×{r['n']}",
                     f"+{r['extra']}" if r["extra"] else tr("enough")]
            for c, txt in enumerate(cells):
                it = QTableWidgetItem(txt)
                it.setForeground(QBrush(QColor(theme.TEXT)))
                if c != 1:
                    it.setTextAlignment(Qt.AlignCenter)
                if r["target"] == D_RECOMMENDED:
                    it.setBackground(QBrush(QColor(theme.OK_SOFT)))
                self.plan.setItem(i, c, it)
        self.plan.resizeColumnsToContents()
        _fit_height(self.plan)
        self.plan_note.setText(tr(
            "Based on {n} conditions. Replicates n solves D(n) = σb/(σw/√n) for n, and it is a "
            "projection <b>assuming σw stays what it is now</b>. More replicates change the σw "
            "estimate too, so measure up to the recommended row and diagnose again.",
            n=len(counts)))

    def _update_prescription(self) -> None:
        d = self.disc
        if d is None or d.sigma_w is None:
            self.pre_text.setText(tr("Replicate measurements are needed to compute this."))
            return
        target = self.target_d.value()
        try:
            n = required_reps(d.sigma_b, d.sigma_w, target)
        except ValueError as e:
            self.pre_text.setText(str(e))
            return
        try:
            ds = self.project.dataset()
            extra = sum(max(0, n - len(v)) for v in ds.reps)
            cond = ds.n_conditions
        except Exception:                            # noqa: BLE001
            extra, cond = 0, 0
        self.pre_text.setText(tr(
            "Target D = {target} → measure each condition <b>{n}×</b> and D becomes {becomes}. "
            "With {cond} conditions that is <b>{extra} extra measurements</b>.",
            target=f"{target:g}", n=n, becomes=f"{d.sigma_b / (d.sigma_w / n ** 0.5):.2f}",
            cond=cond, extra=extra))

    def _fill_terrain(self) -> None:
        n = self.nugget
        if n is None:
            self.terrain.setText(tr("Computed once there are at least 3 conditions."))
            return
        rough = n.ratio > NUGGET_THRESHOLD
        head = tr("nugget ratio = nugget {nugget} / sill {sill} = <b>{ratio}</b>",
                  nugget=f"{n.nugget:.3f}", sill=f"{n.sill:.3f}", ratio=f"{n.ratio:.3f}")
        share = (tr("<b>{pct}%</b> of the visible variation is measurement wobble.",
                    pct=f"{n.noise_share * 100:.0f}") if n.noise_share is not None else "")
        verdict = (tr("A rough surface — raise replicates first.") if rough
                   else tr("A smooth surface."))
        cls = next(name for lim, name in NUGGET_CLASSES if n.ratio <= lim)
        note = tr("This tool's criterion: nugget ratio > {limit} counts as rough. Reference scale "
                  "(geostatistics, Cambardella 1994): &lt;0.25 strong structure · 0.25–0.75 "
                  "moderate · &gt;0.75 weak — currently «{cls}».",
                  limit=f"{NUGGET_THRESHOLD:g}", cls=tr(cls))
        colour = theme.FAIL if rough else theme.OK
        self.terrain.setText(                                                    # i18n: skip (markup)
            f"{head}<br>{share}{'<br>' if share else ''}"
            f"<span style='color:{colour}'>{verdict}</span><br>"
            f"<span style='color:{theme.TEXT_MUTED}; font-size:{theme.SMALL}px'>{note}</span>")

    def set_warning(self, dataset) -> None:
        d = self.disc
        if d is None or d.top_condition is None:
            self.gwarn.setVisible(False)
            return
        if d.top_share is None or d.top_share < 30:
            self.gwarn.setVisible(False)
            return
        self.gwarn.setVisible(True)
        label = " · ".join(f"{x:g}" for x in dataset.X[d.top_condition])
        txt = tr("One condition, <b>{where}</b>, carries <b>{pct}%</b> of the within-condition "
                 "variance.", where=label, pct=f"{d.top_share:.0f}")
        if d.D_drop_top is not None:
            without = tr("Without it, σw is {sigma} and D is {d}.",
                         sigma=f"{d.sigma_w_drop_top:.4f}", d=f"{d.D_drop_top:.2f}")
            lean = tr("The discriminability estimate leans heavily on one condition. "
                      "Re-measuring that condition is the cheapest check.")
            txt += (f"<br>{without}<br>"                                         # i18n: skip (markup)
                    f"<span style='color:{theme.TEXT_MUTED}'>{lean}</span>")
        self.warn_text.setText(txt)
