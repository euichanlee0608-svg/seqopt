# -*- coding: utf-8 -*-
"""Tab 7, Help — answers to the questions this program is likely to raise, in one place.

**Why it lives inside the program**

This tool stops people from doing what they are used to ("run the optimization"
→ "no"). A tool that blocks must be able to explain **why it blocks**, right
there. If the explanation lives in a separate PDF, nobody reads it — they just
tick the force-run checkbox.

Each topic also says **which code the numbers come from** — "where did that
number come from" is the question this project was asked at every report.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QSplitter, QTextBrowser, QVBoxLayout, QWidget)

from core.acquisition import BENCH_CLAIMS
from core.i18n import tr

from . import theme
from .widgets.section import PageHeader

TEST_COUNT = 227      # number of tests under tests/ — tests/test_help.py checks it against the real collected count


@dataclass
class Topic:
    """One help topic. `code` lists the code locations backing the explanation."""

    key: str
    title: str
    body: str
    code: list[str] = field(default_factory=list)
    tags: str = ""

    def searchable(self) -> str:
        return f"{self.title} {self.body} {self.tags}".lower()


def _p(*parts: str) -> str:
    return "".join(f"<p>{x}</p>" for x in parts)


def _ul(*items: str) -> str:
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


def _pct(x: float) -> str:
    return f"{round(x * 100):d}%"


def _table(head: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{th}</tr>{tr}</table>"


# ══════════════════════════════════════════════════════════════════════
# Content
# ══════════════════════════════════════════════════════════════════════
def topics() -> list[Topic]:
    """Built fresh each call — `tr()` reads the current language, so this must not run at import time."""
    return [
    # ── getting started ────────────────────────────────────────────
    Topic("start", tr("What is this program"), tags=tr("overview start introduction"),  # i18n: skip
          body=_p(
              tr("<b>Enter your measurements and it tells you which condition to "
                 "measure next — and whether that advice can be trusted at all.</b>"),
              tr("The second half is the point. Plenty of tools already suggest the "
                 "next condition. This one <b>checks the advice's reliability first, "
                 "and refuses to advise when the data falls short.</b>")) +
          tr("<h3>Why it was built this way</h3>") +
          _p(tr("While validating this method, the same question was answered <b>four "
                "times and got it wrong three times.</b> The cause was never a code "
                "bug — it was <b>never asking whether the data could support the "
                "question at all.</b>"),
             tr("One real lab dataset from that study had a learnability of "
                "R² = −0.272 — worse than always answering the overall mean. Feed it "
                "to an ordinary optimization tool and you get <b>a smooth response "
                "surface and a plausible next candidate anyway.</b> Trust that, and "
                "you spend time and samples on noise.")),
          code=["core/diagnostics.py: gate()", "docs/ARCHITECTURE.md"]),  # i18n: skip

    Topic("simple", tr("Why are there so few choices"),  # i18n: skip
          tags=tr("simple choices advanced defaults algorithm kernel"),
          body=_p(tr("Deliberately. Compared with other optimization tools:")) +
          _table([tr("tool"), tr("what the user must choose")], [
              [tr("AutoOED"), tr("surrogate · acquisition · multi-objective solver · selection strategy — four dropdowns")],
              [tr("MADGUI"), tr("ElasticNet / RandomForest / XGBoost · cross-validation scheme")],
              [tr("OPTIMEO"), tr("DoE type · model · acquisition")],
              [tr("<b>this program</b>"), tr("<b>none</b> — fixed kernel · fixed EI · fixed model")]]) +
          tr("<h3>Why fixing them is affordable</h3>") +
          _p(tr("<b>Because the gate exists.</b> Other tools hand you choices so you "
                "can wander between models when the data is bad. This program rules "
                "<b>\"changing the model will not help\"</b> — so there is nothing to choose."),
             tr("In the validation study, six model families were tried on a bad "
                "dataset and <b>not one</b> reached R² > 0. Offer a menu there, and "
                "people spend their time hunting for an answer that does not exist.")) +
          tr("<h3>If you still want to change things</h3>") +
          _p(tr("Unfold <b>\"Advanced ▸\"</b> on each screen — acquisition function, "
                "batch size, target discriminability, log transform and the initial "
                "design size are all there. Not removed. <b>Deferred.</b>")),
          code=["ui/widgets/advanced.py", "core/surrogate.py: DEFAULT_SURROGATE"]),  # i18n: skip

    Topic("flow", tr("In what order do I use it"), tags=tr("order flow workflow first"),  # i18n: skip
          body=tr("<h3>Starting a new experiment</h3>") +
          _ul(tr("<b>Setup</b> — define your knobs (inputs), the objective, and the budget"),
              tr("<b>Setup → generate initial design</b> — get the first measurement points as CSV"),
              tr("Measure them in the lab"),
              tr("<b>Data</b> — enter the values (paste · import · type)"),
              tr("<b>Diagnose</b> — check the four requirements ← <b>this is the fork</b>"),
              tr("Pass → get the next condition on <b>Recommend</b>, and repeat 4–6"),
              tr("Fail → fix the data first, following the <b>prescription</b> on the Diagnose tab")) +
          tr("<h3>Diagnosing a spreadsheet you already have</h3>") +
          _ul(tr("<b>Data → import from file</b> and map the columns"),
              tr("Read the verdict table on <b>Diagnose</b>"),
              tr("Keep the evidence as a PDF with <b>Report</b>")),
          code=["ui/main_window.py: recompute()"]),  # i18n: skip

    # ── the requirements ───────────────────────────────────────────
    Topic("gate", tr("The four requirements — what and why"), tags=tr("gate requirements verdict locked"),  # i18n: skip
          body=_p(tr("All four must pass before recommendations open. "
                     "A single <b>×</b> locks them.")) +
          _table(["", tr("requirement"), tr("what it checks"), tr("when it fails")], [
              ["①", tr("candidate count"), tr("are there more <b>conditions to choose from</b> in the design space than budget"),
               tr("measuring everything is better (the gain from optimizing is zero in principle). "
                  "A finer step or a wider range gives more candidates")],
              ["②", tr("surface learnability"), tr("is the model learning the terrain (LOOCV R² > 0)"),
               tr("changing the model will not help. The data is the problem")],
              ["③", tr("discriminability"), tr("do condition differences exceed the measurement wobble"),
               tr("raise the replicate count")],
              ["④", tr("replicates"), tr("has the same condition ever been re-measured"),
               tr("the wobble's size is unknowable (a warning — it does not lock)")]]) +
          _p(tr("<b>Any of ①②③ failing locks the gate.</b> ④ is a warning."),
             tr("① counts <b>not the conditions already measured</b> but the Setup tab's ranges · "
                "steps · sum constraint — integer, categorical and stepped variables multiply their "
                "level counts, and a single continuous variable without a step makes the count "
                "infinite, which passes. The count is always shown under the variable table on the Setup tab."),
             tr("Learnability R² is slow, so it runs in the background. "
                "<b>The lock holds while it computes</b> — the unknown is never counted as a pass.")),
          code=["core/diagnostics.py: gate()", "core/spec.py: count_candidates()",
                "core/recommend.py: recommend()"]),  # i18n: skip

    Topic("d", tr("What is discriminability (D)"),  # i18n: skip
          tags=tr("discriminability D sigma noise wobble replicates bootstrap"),
          body=_p(tr("<b>The difference that changing the condition makes</b>, divided by "
                     "<b>the wobble of re-measuring the same condition.</b> Above 1 means "
                     "\"neighboring conditions can be told apart\".")) +
          tr("<pre>σw = √( Σ(n−1)·var(replicates per condition) / Σ(n−1) )   ← conditions with ≥2 replicates only\n"
             "σb = std( condition means , ddof=1 )\n"
             "D(n) = σb / (σw / √n)</pre>") +
          _p(tr("<b>An analogy</b> — telling apart two people who differ by 1 kg, on a "
                "scale that jumps ±2 kg per reading. No amount of cleverness helps. "
                "It is the scale's fault.")) +
          tr("<h3>Why the point estimate is not enough</h3>") +
          _p(tr("Conditions are resampled with replacement and D is recomputed "
                "<b>4000 times</b> for a 95% interval. When that interval straddles "
                "the threshold of 1.0, the screen says <b>\"undecided\"</b>."),
             tr("The validation study hit exactly this case — D = 1.03 looked passed, "
                "but the interval was [0.49, 1.80], so <b>neither passed nor failed "
                "could honestly be claimed.</b>")),
          code=["core/diagnostics.py: discriminability()", "tests/test_diagnostics.py"]),  # i18n: skip

    Topic("levels", tr("Where do the thresholds 1 · 2 · 3.5 come from"),  # i18n: skip
          tags=tr("threshold recommended basis prescription replicates how many"),
          body=_p(tr("The discriminability gauge carries three marks. <b>The gate is 1, "
                     "alone</b>; the other two are marks for reading \"how comfortable\". "
                     "None of them is arbitrary.")) +
          _table([tr("mark"), tr("name"), tr("meaning"), tr("basis")], [
              ["D ≥ 1", tr("gate (minimum)"), tr("difference = wobble"),
               tr("Follows from the definition. With σb &lt; σw, the difference made by "
                  "changing conditions is smaller than the wobble of re-measuring — "
                  "rankings may be noise.")],
              ["D ≥ 2", tr("recommended"), tr("difference ≈ wobble × 2"),
               tr("Two means about two standard errors apart — the usual statistical "
                  "boundary for \"different\" (95%, z ≈ 1.96).")],
              ["D ≥ 3.5", tr("comfortable"), tr("difference ≈ wobble × 3.5"),
               tr("Matches measurement-system analysis (AIAG MSA), where a usable "
                  "instrument needs ndc = 1.41·σb/σw ≥ 5 distinct categories.")]]) +
          tr("<h3>How the prescription table is computed</h3>") +
          _p(tr("With n replicates per condition the mean's wobble shrinks to σw/√n, "
                "so D(n) = σb/(σw/√n). Solving for n gives <b>n = ⌈(target D · σw / σb)²⌉</b>. "
                "\"Extra runs\" sums, per condition, the gap between its current "
                "replicates and n."),
             tr("<b>Caution</b> — the calculation assumes <b>σw stays what it is now.</b> "
                "More replicates change the σw estimate itself, so measure up to the "
                "recommended row and <b>diagnose again</b>.")) +
          tr("<h3>And the nugget-ratio threshold of 0.3?</h3>") +
          _p(tr("This tool calls a surface rough above a nugget ratio of 0.3. The widely "
                "used geostatistics scale (Cambardella 1994) — &lt;0.25 strong spatial "
                "structure · 0.25–0.75 moderate · &gt;0.75 weak — is shown alongside "
                "on the Diagnose tab.")),
          code=["core/diagnostics.py: D_LEVELS · replicate_plan() · NUGGET_CLASSES",
                "tests/test_diagnostics.py"]),  # i18n: skip

    Topic("r2", tr("What does a negative learnability R² mean"),  # i18n: skip
          tags=tr("R2 learnability LOOCV negative surface"),
          body=_p(tr("Each condition is left out in turn, the model is fitted on the rest, "
                     "and the left-out condition is predicted (LOOCV). "
                     "R² = 1 − SS_res/SS_tot."),
                  tr("<b>R² ≤ 0 means worse than always answering the overall mean.</b> "
                     "The model has learned nothing.")) +
          tr("<h3>Why changing the model will not help</h3>") +
          _p(tr("The validation study ran six families (constant, linear, quadratic, GP, "
                "RF, …) on such a dataset, and <b>not one reached R² > 0.</b> When the "
                "signal is not in the data, no model can learn it."),
             tr("Look at the scatter on the <b>Validation tab</b>. Points clustering "
                "around the red \"always answer the mean\" line instead of the diagonal — "
                "that is what R² < 0 looks like.")),
          code=["core/diagnostics.py: loocv_r2()", "ui/tab_model.py: _plot_loocv()"]),  # i18n: skip

    Topic("nugget", tr("Nugget ratio · terrain roughness"),  # i18n: skip
          tags=tr("nugget sill semivariogram terrain roughness"),
          body=_p(tr("A semivariogram is built from condition-pair distances and value "
                     "differences: how much difference survives even at near-zero "
                     "distance (<b>the nugget</b>), as a share of the height reached far "
                     "away (<b>the sill</b>).")) +
          tr("<pre>nugget ratio = nugget / sill      &gt; 0.3 counts as a 'rough surface'</pre>") +
          _p(tr("A large nugget ratio means <b>most of the visible variation is "
                "measurement wobble.</b> The lab dataset in the validation study sat at "
                "0.489, with a noise share of <b>95%</b>.")) +
          tr("<h3>Caution — it does not predict the ordering</h3>") +
          _p(tr("The original write-up claimed the nugget-ratio ordering matches the R² "
                "ordering exactly. Checked against the actual values, <b>it does not "
                "hold</b> (one dataset has the lower nugget ratio and the lower R²). "
                "What does hold is the <b>separation between the smooth and the rough.</b>")),
          code=["core/diagnostics.py: nugget_ratio()"]),  # i18n: skip

    # ── the screens ────────────────────────────────────────────────
    Topic("import", tr("My spreadsheets differ every time"),  # i18n: skip
          tags=tr("import excel column mapping preset format csv"),
          body=_p(tr("Which is why the program does not guess the format. "
                     "<b>The original shows on the left, and you assign the columns' "
                     "meanings on the right.</b>")) +
          _ul(tr("Changing a role recolors the left column instantly (blue=input · green=response · gray=ignore)"),
              tr("<b>Before you press Import</b>, the bottom shows \"N conditions · N "
                 "measurements · N missing\". Check that those match what you expect, then press"),
              tr("<b>Save a preset</b> and the next file from the same instrument loads in one step"),
              tr("The mapping is also stored in the project file, so reopening reads identically")) +
          tr("<h3>How the role guessing works</h3>") +
          _p(tr("<b>Design axes recycle their values; measurement columns differ on "
                "almost every row.</b> Only numeric columns with a low distinct-value "
                "ratio become input candidates. This one rule keeps intermediate "
                "measurement columns (raw band intensities and the like) from being "
                "mistaken for inputs.")),
          code=["core/profile.py: guess_profile()", "core/importer.py: apply_profile()"]),  # i18n: skip

    Topic("reps", tr("May I enter the same condition several times"), tags=tr("replicates duplicates rows"),  # i18n: skip
          body=_p(tr("<b>You should.</b> One row = one measurement, and the same "
                     "condition on several rows is automatically read as <b>replicates</b>."),
                  tr("Without replicates, σw (the measurement wobble) cannot be computed "
                     "and requirement ③ shows <b>\"not computable\"</b>. The program "
                     "<b>does not substitute an assumed value</b> — it refuses to "
                     "pretend to know what it does not.")),
          code=["core/dataset.py: group_measurements()"]),  # i18n: skip

    Topic("colors", tr("What do the table colors mean"), tags=tr("colors background yellow red gray legend table"),  # i18n: skip
          body=_table([tr("color"), tr("meaning"), tr("where")], [
              [tr("<span style='background:{c}'>&nbsp;yellow&nbsp;</span>", c=theme.ROW_ZERO),
               tr("a zero-response row · a condition with only one replicate"), tr("Data · Diagnose")],
              [tr("<span style='background:{c}'>&nbsp;pink&nbsp;</span>", c=theme.ROW_EXCLUDED),
               tr("an excluded row · the variance-dominating condition"), tr("Data · Diagnose")],
              [tr("<span style='background:{c}'>&nbsp;blue&nbsp;</span>", c=theme.ROW_PENDING),
               tr("a row pre-filled from a recommendation (not yet measured)"), tr("Data")],
              [tr("<span style='background:{c}'>&nbsp;sky&nbsp;</span>", c=theme.ACCENT_SOFT),
               tr("a column assigned as an input"), tr("Import")],
              [tr("<span style='background:{c}'>&nbsp;green&nbsp;</span>", c=theme.OK_SOFT),
               tr("the column assigned as the response"), tr("Import")]]) +
          tr("<h3>Figure colors</h3>") +
          _ul(tr("<b>μ (predicted mean)</b> — viridis. Magnitude"),
              tr("<b>σ (uncertainty)</b> — grayscale. It is \"how unknown\", not a value"),
              tr("<b>EI (acquisition)</b> — warm. The one color that calls for action"),
              tr("No rainbow (jet) — it invents boundaries that do not exist")),
          code=["ui/theme.py", "core/plotstyle.py"]),  # i18n: skip

    # ── recommendations ────────────────────────────────────────────
    Topic("locked", tr("It is locked — can I not just use it anyway"), tags=tr("locked force override bypass unmet"),  # i18n: skip
          body=_p(tr("You can. Turn on <b>\"Force a recommendation despite unmet "
                     "requirements\"</b> on the Recommend tab."),
                  tr("But <b>it leaves a mark</b> — on the result screen, in the "
                     "instruction-sheet CSV, and as a <b>\"REQUIREMENTS UNMET\" stamp on "
                     "every page of the PDF report.</b> Screenshot a single page into a "
                     "slide and the warning travels with it.")) +
          tr("<h3>Try these first</h3>") +
          _ul(tr("Put a target discriminability into the <b>prescription</b> on the "
                 "Diagnose tab — it back-computes how many more replicates you need"),
              tr("If the <b>warning</b> box says one condition carries N% of the "
                 "variance, re-measuring that condition is the cheapest check"),
              tr("If requirement ① is the problem, make the step finer or the range wider on the "
                 "Setup tab. If the candidates are still fewer than the budget, <b>measuring everything "
                 "is right</b> — this program is not needed in that case")),
          code=["core/recommend.py: recommend(override=...)", "core/report.py: write_pdf()"]),  # i18n: skip

    Topic("acq", tr("Which of the three methods should I use"),  # i18n: skip
          tags=tr("acquisition EI UCB Thompson beta explore method global local benchmark"),
          body=_p(tr("Chosen at the <b>top of the Recommend tab</b>. Without a specific "
                     "reason, keep the default.")) +
          _table(["", tr("what"), tr("when")], [
              [tr("<b>Default (EI)</b>"), tr("Expected improvement — how much a candidate should beat the best so far"),
               tr("Almost always. On 8 standard test functions it reached the neighbourhood of the "
                  "global optimum within a 40-run budget — "
                  "multimodal average {multi} · unimodal average {uni} (table below)",
                  multi=_pct(BENCH_CLAIMS['multimodal_hit']), uni=_pct(BENCH_CLAIMS['unimodal_hit']))],
              [tr("<b>Explore wider (UCB)</b>"), tr("μ + b·σ. A larger b pushes into uncertainty"),
               tr("When the terrain is still unknown. Mind the caution below")],
              [tr("<b>Diversify (Thompson)</b>"), tr("draw one function from the posterior, take its maximum"),
               tr("When receiving several at once — candidates do not pile up in one spot")]]) +
          tr("<h3>Does it get stuck in a local optimum</h3>") +
          _p(tr("Two layers guard against it. ① The initial design is space-filling (maximin LHS), so "
                "the whole range is swept from the start, and ② the acquisition maximisation is "
                "<b>multi-start</b> (L-BFGS-B from the best 20 of 2000 space-filling points), so it does "
                "not settle on the nearest peak — at all 72 check points it found a value at least as "
                "good as differential evolution (a global optimiser)."),
             tr("Still, <b>some terrain it cannot find</b>. The 2026-09-05 benchmark "
                "(budget 40 = 11 initial + 29 sequential, 3% noise, 10 seeds, hit = regret below 5%):")) +
          _table([tr("test function"), tr("EI hit rate"), tr("what it measures")], [
              [tr("Branin · six-hump camel · Hartmann-3 · Rosenbrock"),
               " · ".join(_pct(BENCH_CLAIMS["ei_hit"][k]) for k in ("branin", "camel6", "hartmann3", "rosen2")),
               tr("several peaks (2–3 dimensions) — standard multimodal · a curved valley")],
              [tr("Levy-4"), _pct(BENCH_CLAIMS["ei_hit"]["levy4"]), tr("many local peaks (4 dimensions)")],
              [tr("Two peaks (needle)"), _pct(BENCH_CLAIMS["ei_hit"]["twopeak"]),
               tr("a narrow valley covering barely 1% of the space — only the seeds whose initial "
                  "design landed in it found it")],
              [tr("Ackley"), _pct(BENCH_CLAIMS["ei_hit"]["ackley2"]), tr("a rough surface (terrain dense with small bumps)")],
              [tr("Hartmann-6"), _pct(BENCH_CLAIMS["ei_hit"]["hartmann6"]),
               tr("6 dimensions — no method finds it within a 40-run budget")]]) +
          _p(tr("So with <b>6 or more variables, or a very narrow optimum</b>, a 40-run budget is not "
                "enough. The answer then is not a different acquisition function but the "
                "<b>initial design size (25–30% of the budget) · the budget · the range</b>.")) +
          tr("<h3>Why there is no separate global-search acquisition</h3>") +
          _p(tr("Four alternatives (MES · EI mixed with exploration · a GP-UCB schedule · Thompson) were "
                "measured under the same conditions. The best multimodal average was "
                "{best_alt}, which did not beat "
                "EI ({ei}), and the narrow valley and the 6-dimensional "
                "function defeated the alternatives just the same. The rule — 'it goes on screen only if it "
                "beats EI on multimodal functions and loses nothing on unimodal ones' — was fixed "
                "<b>before measuring</b>, and nothing passed it, so nothing went on screen. The candidate "
                "code and the result file stay in the repo — re-measure, and if one passes, a test says so.",
                best_alt=_pct(BENCH_CLAIMS['best_alternative_multimodal_hit']),
                ei=_pct(BENCH_CLAIMS['multimodal_hit']))) +
          tr("<h3>Caution — pushing exploration harder does not help</h3>") +
          _p(tr("In the original validation (2026-08), raising UCB's b from 1 to 4 dropped the "
                "global-optimum hit rate from <b>90% to 61%</b>, and pure space-filling was the "
                "worst at 1–7%. In this benchmark too, UCB (b=2) averaged "
                "{ucb} on the multimodal functions, below "
                "EI's {ei}. "
                "Do not casually raise the default b = 2.0.",
                ucb=_pct(BENCH_CLAIMS['ucb_multimodal_hit']), ei=_pct(BENCH_CLAIMS['multimodal_hit']))),
          code=["core/acquisition.py: maximise_continuous() · BENCH_CLAIMS", "packaging/bench_global.py",
                "docs/bench_global.json"]),  # i18n: skip

    Topic("batch", tr("Can I get several at once"), tags=tr("batch several at once"),  # i18n: skip
          body=_p(tr("Up to 10, via <b>\"At a time\"</b> under Advanced on the Recommend tab."),
                  tr("They are picked sequentially, each picked point <b>assuming its "
                     "predicted mean as if observed</b> before the model refits for the "
                     "next pick (kriging believer). No unmeasured value is ever "
                     "consulted, so the <b>no-lookahead rule</b> holds.")),
          code=["core/acquisition.py: batch_picks()"]),  # i18n: skip

    Topic("reps_rec", tr("Why does the recommendation carry a suggested replicate count"),  # i18n: skip
          tags=tr("suggested replicates instruction count"),
          body=_p(tr("Measure a new condition <b>only once and discriminability drops</b>, "
                     "worsening the next verdict. So \"measure it n times\" goes on the "
                     "instruction sheet."),
                  tr("The value follows the <b>median</b> replicate count of the current data.")),
          code=["core/recommend.py: recommended_reps()"]),  # i18n: skip

    Topic("step", tr("What is the \"step\", and must I fill it in"),  # i18n: skip
          tags=tr("step grid resolution instrument setting candidates"),
          body=_p(tr("The <b>step</b> in the Setup tab's variable table is <b>the spacing the instrument "
                     "can actually be set to</b>. If the power dial moves in 10 W units, enter 10; if the "
                     "temperature setting moves in 5 °C units, enter 5. Only continuous variables have "
                     "one — integer variables have a built-in step of 1.")) +
          tr("<h3>What changes once it is filled in</h3>") +
          _ul(tr("<b>Recommendations land on the grid</b>. A value like 173.6 W cannot go on an instruction sheet"),
              tr("<b>The candidate count of requirement ①</b> becomes countable — with even one continuous "
                 "variable without a step, the candidates are infinite and ① always passes"),
              tr("The initial design points are snapped to the grid too. If snapping makes two coincide, "
                 "they stay — a coincidence is simply a replicate")) +
          _p(tr("Leave it empty and the variable is treated as continuous. That is not wrong, but the "
                "recommendations will be finer than the instrument can set.")),
          code=["core/spec.py: VarSpec.step · n_levels()", "core/design.py: to_real()"]),  # i18n: skip

    Topic("constraint", tr("Can I add a constraint like composition sum = 100 %"),  # i18n: skip
          tags=tr("constraint sum composition 100 mixture blend"),
          body=_p(tr("Yes. Under <b>\"Sum constraint\"</b> on the Setup tab, pick 2 or more variables and "
                     "enter <b>= exactly</b> or <b>≤ at most</b> with the total. From then on the initial "
                     "design points and the recommendations come out <b>only as values that satisfy "
                     "the constraint</b>.")) +
          tr("<h3>How it is kept</h3>") +
          _ul(tr("Points are drawn evenly on the constraint plane (Dirichlet) and the ones far apart "
                 "from each other become the initial design"),
              tr("If snapping to the grid breaks the sum, the values are moved <b>in whole steps</b> to "
                 "restore it — which is why <b>\"= exactly\" needs the constrained variables to share "
                 "one step</b> (the Setup tab tells you)"),
              tr("The candidate count of requirement ① is also counted inside the constraint "
                 "(A·B·C with step 10, sum 100 → 66 candidates)")) +
          tr("<h3>If measured values already violate the constraint</h3>") +
          _p(tr("The Setup tab shows how many rows violate it. Those rows are still used for learning "
                "(they were actually measured); only the new recommendations stay inside the constraint.")),
          code=["core/spec.py: SumConstraint", "core/design.py: feasible_unit() · snap_to_constraint()"]),  # i18n: skip

    Topic("startlog", tr("What happens at startup (the boot log)"),  # i18n: skip
          tags=tr("startup slow loading splash black window terminal log"),
          body=_p(tr("On launch a small card appears and says in one line what it is doing — <b>loading "
                     "the computation engine</b> is the longest part (numpy · scipy · scikit-learn, "
                     "usually 2–6 seconds). Then the window opens.")) +
          tr("<h3>The black console windows that used to flash</h3>") +
          _p(tr("Earlier builds flashed black windows on launch. They were not our code but the "
                "<code>cmd</code> · <code>powershell</code> processes that the computation packages "
                "spawn while being imported (the Python standard library's <code>platform</code> module "
                "and joblib's CPU count). Every child process is now forced to start <b>without a "
                "window</b>, and whatever was spawned is written to the log.")) +
          tr("<h3>The log file</h3>") +
          _p(tr("<code>home folder\\.seqopt\\seqopt.log</code> records how long each stage took. "
                "When someone says 'it is slow to start' or 'a strange window appeared', this file is "
                "the place to look. Errors go to <code>error.log</code> in the same folder.")),
          code=["core/boot.py", "app.py: _splash()"]),  # i18n: skip

    Topic("extrap", tr("It says \"outside measured range\""), tags=tr("extrapolation outside range warning"),  # i18n: skip
          body=_p(tr("The model learned <b>the range you actually measured.</b> Where the "
                     "declared range on the Setup tab is wider, the outside is somewhere "
                     "the model has never seen."),
                  tr("<b>It is not blocked</b> — widening the range and measuring there "
                     "is sometimes exactly the right move. But it is always marked.")),
          code=["core/recommend.py: _axis_bounds()"]),  # i18n: skip

    # ── trust ──────────────────────────────────────────────────────
    Topic("logic", tr("What is it computing inside"), tags=tr("logic algorithm GP kernel EI principle formulas"),  # i18n: skip
          body=tr("<h3>In one line</h3>") +
          _p(tr("From the measured conditions it estimates the <b>response surface</b> "
                "(input → output), with a model that also reports its own "
                "<b>uncertainty</b>. Then \"how much would measuring here teach\" is "
                "scored, and the highest scorer wins.")) +
          tr("<h3>1. The surrogate — a Gaussian process</h3>") +
          "<pre>ConstantKernel × Matern(ν=2.5, ARD) + WhiteKernel</pre>" +  # i18n: skip
          _ul(tr("<b>Matern ν=2.5</b> — smooth but not overly smooth. A common fit for experimental surfaces"),
              tr("<b>ARD</b> — one length scale per variable. The sensitivity view comes from here"),
              tr("<b>WhiteKernel</b> — absorbs measurement noise. It earns its keep once replicates exist"),
              tr("The model learns <b>condition means</b>. Replicates feed discriminability (gate ③)")) +
          tr("<h3>2. The acquisition — choosing where to measure next</h3>") +
          tr("<pre>EI  = (μ − best)·Φ(z) + σ·φ(z),   z = (μ − best)/σ\n"
             "UCB = μ + b·σ\n"
             "TS  = one posterior draw, take its maximum</pre>") +
          _p(tr("<b>best is always the best measured value.</b> Use a true or corrected "
                "value and the choice no longer matches what a researcher would actually do.")) +
          tr("<h3>3. The diagnostics — what only this tool does</h3>") +
          tr("<pre>σ<sub>w</sub> = √( Σ(n−1)·var(replicates) / Σ(n−1) )    measurement wobble\n"
             "σ<sub>b</sub> = std( condition means , ddof=1 )         between-condition difference\n"
             "D(n) = σ<sub>b</sub> / (σ<sub>w</sub>/√n)                        discriminability\n\n"
             "R² = 1 − SS_res/SS_tot   (per-condition LOOCV, refit per fold)\n"
             "nugget ratio = nugget / sill   (semivariogram)</pre>") +
          _p(tr("Discriminability comes with a 95% interval from a <b>4000-draw "
                "condition bootstrap</b>. When the interval straddles 1.0, the verdict "
                "is \"undecided\".")),
          code=["core/surrogate.py", "core/acquisition.py", "core/diagnostics.py"]),  # i18n: skip

    Topic("verified", tr("Has it been validated"), tags=tr("validation trust tests reproduce evidence measured"),  # i18n: skip
          body=tr("<h3>How far the validation goes</h3>") +
          _table([tr("part"), tr("status"), tr("evidence")], [
              [tr("<b>diagnostic calculations</b><br>discriminability · learnability · nugget"),
               tr("<b>validated</b>"),
               tr("the test suite pins the numbers the original validation scripts "
                  "produced, to within 1e-3; the public-dataset expectation file "
                  "(verify_terrain.json) ships in this repo")],
              [tr("<b>the gate verdict</b>"), tr("<b>validated</b>"),
               tr("the same yardstick applied to four datasets (one lab, three public) "
                  "reproduced the original analysis' split")],
              [tr("<b>single recommendations (EI · GP)</b>"), tr("<b>validated</b>"),
               tr("the global-optimum hit rate within a 40-run budget was actually measured on "
                  "8 standard test functions × 10 seeds "
                  "(multimodal average {multi}). The result file "
                  "ships in the repo, and a test checks the numbers on screen against it",
                  multi=_pct(BENCH_CLAIMS['multimodal_hit']))],
              [tr("<b>four global-search alternatives</b>"), tr("<b>no gain, confirmed</b>"),
               tr("MES · exploration mixing · GP-UCB · Thompson compared under the same conditions. "
                  "None beat EI on the multimodal functions, so none went on screen "
                  "(see «Which of the three methods»)")],
              [tr("<b>sum constraint · grid candidates</b>"), tr("<b>validated</b>"),
               tr("tests check that initial designs and recommendations land only on the "
                  "constraint plane and on the grid")],
              [tr("batch recommendations"), tr("<b>not validated</b>"),
               tr("only checked that distinct points come out. Whether batches beat "
                  "sequential picking was never measured")],
              [tr("the random-forest surrogate"), tr("<b>not validated</b>"),
               tr("its uncertainty calibration was never checked. Comparison only")],
          ]) +
          tr("<h3>Numbers pinned by the tests (public datasets)</h3>") +
          _table([tr("item"), tr("value")], [
              [tr("external discriminability D"), "P3HT-CNT 6.76 · AgNP 4.28 · Perovskite 1.82"],  # i18n: skip
              [tr("terrain nugget ratios"), "P3HT-CNT 0.082 · AgNP 0.032 · Perovskite 0.404"],  # i18n: skip
          ]) +
          _p(tr("The lab dataset the study was run for is <b>not distributed</b> with "
                "this repository; the numbers quoted in this help (R² = −0.272, "
                "D = 1.03 [0.49, 1.80], noise share 95%) are that study's published "
                "aggregates.")) +
          tr("<h3>Held in place by machines</h3>") +
          _p(tr("The test suite — <b>{n} tests</b> — re-verifies these values on every "
                "run. Change the calculation and the tests break — that is the tripwire.", n=TEST_COUNT),
             tr("The Windows executable is only built <b>after the tests pass</b>. "
                "A program that misjudges must never get packaged.")) +
          tr("<h3>What honestly was not done</h3>") +
          _ul(tr("Whether batch recommendations beat sequential ones was <b>never measured</b>"),
              tr("The extrapolation margin of 0.02 was <b>chosen without evidence</b>"),
              tr("Of the four gate thresholds, only <b>R² > 0</b> has a hard basis. "
                 "The discriminability 1.0 is borrowed from other fields, so it is "
                 "safest in \"A vs B\" comparisons"),
              tr("The global-search benchmark uses <b>synthetic test functions</b>, not real device terrain"),
              tr("The stopping-rule history resets when the program restarts")),
          code=["docs/ARCHITECTURE.md", "tests/test_diagnostics.py", "tests/data/verify_terrain.json",
                "docs/bench_global.json"]),  # i18n: skip

    Topic("trust", tr("Can I trust these numbers"), tags=tr("validation trust evidence tests reproduce"),  # i18n: skip
          body=tr("<h3>Three ways to check</h3>") +
          _ul(tr("<b>Diagnose tab → unfold the calculation</b> — per-condition n, mean, "
                 "SD and contribution are all visible, and the σw·σb·D in the box "
                 "below come straight from that table"),
              tr("<b>Report → calculation log</b> — every number's formula and "
                 "intermediate values, saved as text"),
              tr("<b>Report → reproduction script</b> — one file that produces the same "
                 "numbers again. Half a year later, \"where did this number come "
                 "from\" still has an answer")) +
          tr("<h3>Machine-checked</h3>") +
          _p(tr("The computation core is pinned by tests that reproduce the original "
                "validation scripts' values to within 1e-3 (the external datasets' "
                "D values and terrain statistics among them). {n} tests in all.", n=TEST_COUNT),
             tr("So <b>changing the calculation breaks the tests.</b> That is the tripwire.")),
          code=["tests/test_diagnostics.py", "tests/data/verify_terrain.json"]),  # i18n: skip

    Topic("slow", "The learnability computation is slow", tags="slow speed performance LOOCV background",
          body=_p("It is. LOOCV refits the model once per condition — "
                  "<b>39 seconds at 178 conditions × 5 variables</b> (measured).",
                  "So the fast parts (surface, σ, EI — 0.2s) and the slow part "
                  "(learnability R²) are split, and only the slow part runs in the "
                  "background. Table input never freezes.") +
          "<h3>Why not use the fast method</h3>" +
          _p("Closed-form LOO with fixed hyperparameters is <b>200× faster.</b> "
             "But on the validation study's lab data it flipped R² from "
             "<b>−0.272 to +0.228</b> — information used in fitting leaks into "
             "every fold.",
             "That speed would buy a <b>gate verdict reversed from FAIL to OK.</b> "
             "It would erase this tool's reason to exist, so it is not used."),
          code=["core/diagnostics.py: loocv_r2()"]),

    Topic("limits", "What this program does not do", tags="limits out of scope constraints multi-objective",
          body=_p("<b>Explicitly out of scope.</b> Not for lack of ability — half-built "
                  "features with no explanation are more dangerous than absent ones.") +
          _ul("<b>Multi-objective optimization (Pareto)</b> — more than one response",
              "<b>Constraints other than one sum</b> — only <b>a single linear sum constraint</b> "
              "(e.g. composition = 100%) is supported. Inequalities between variables such as "
              "'A &gt; B', nonlinear constraints and two or more constraints are not",
              "<b>Population methods — genetic algorithms · PSO · CMA-ES</b> — each generation needs "
              "dozens of runs, so a budget of a few dozen runs affords one or two generations "
              "(effectively random search). Global search is done by the space-filling initial "
              "design and the multi-start acquisition maximisation — see «Which of the three "
              "methods» for the results on 8 test functions",
              "<b>Multi-fidelity</b> — mixing coarse and precise computations",
              "<b>Instrument control / automated measurement</b> — a person measures and types the value",
              "<b>Cloud sync · multiple users</b>") +
          "<h3>Scale limits</h3>" +
          _p("Around 200 conditions × 5 variables is the comfortable range. Beyond "
             "500 conditions, a single model fit passes 2 seconds. For thousands of "
             "points, a different tool is the right choice."),
          code=["docs/ARCHITECTURE.md"]),

    Topic("save", "How do saving and backups work", tags="save backup autosave recovery seqopt file",
          body=_ul("A project is one <b>.seqopt</b> file, with <b>the raw data inside "
                   "it, whole</b> — move the original spreadsheet and every number "
                   "still traces back",
                   "Saves are <b>atomic</b> — the program dying mid-save leaves the previous file intact",
                   "The previous version survives as <b>.seqopt.bak</b>",
                   "Every minute, an <b>.seqopt.autosave</b> is written. A dead PC "
                   "still yields the last state",
                   "The Data tab undoes with <b>Ctrl+Z</b> (50 steps)"),
          code=["core/project.py: save()", "ui/tab_data.py: undo()"]),

    Topic("dev", "Adding features", tags="development extension code algorithm add module",
          body=_p("<b>Computation (core/) and screens (ui/) are split.</b> "
                  "core never imports the GUI and runs entirely from the CLI.") +
          "<h3>Plugging in a new algorithm</h3>" +
          _p("Register <b>one class</b> — no existing file changes. It enters the "
             "screen list, the report and the recommendation path automatically.") +
          "<pre>@ACQUISITIONS.register(\"PI\")\nclass ProbabilityOfImprovement:\n"
          "    label = \"PI — probability of improvement\"\n    supports_continuous = True\n"
          "    def score(self, model, X, best, rng=None): ...\n"
          "    def describe(self): return \"PI\"</pre>" +
          "<h3>What must not change</h3>" +
          _ul("<b>The GP kernel</b> — exactly one combination reproduces the regression expectations",
              "<b>LOOCV to closed form</b> — the gate verdict flips",
              "<b>The scikit-learn version</b> — pinned at 1.8.0",
              "<b>Any path around the gate</b> — the one entrance to a recommendation is <code>recommend()</code>"),
          code=["docs/ARCHITECTURE.md", "core/protocols.py", "core/registry.py"]),
]

_CSS = f"""
<style>
  body {{ color:{theme.TEXT}; font-size:13px; line-height:1.7; }}
  h2 {{ font-size:17px; color:{theme.TEXT}; margin:0 0 4px 0; }}
  h3 {{ font-size:13.5px; color:{theme.ACCENT}; margin:16px 0 4px 0; }}
  p  {{ margin:6px 0; }}
  ul {{ margin:6px 0 6px 18px; padding:0; }}
  li {{ margin:3px 0; }}
  table {{ border-collapse:collapse; margin:8px 0; width:100%; }}
  th {{ background:{theme.SURFACE}; text-align:left; padding:6px 8px;
        border:1px solid {theme.BORDER}; font-weight:600; }}
  td {{ padding:6px 8px; border:1px solid {theme.BORDER}; vertical-align:top; }}
  pre {{ background:{theme.SURFACE}; border:1px solid {theme.BORDER}; border-radius:6px;
         padding:10px; font-family:{theme.MONO_FAMILY}; font-size:12px; margin:8px 0; }}
  code {{ background:{theme.SURFACE}; padding:1px 4px; border-radius:3px;
          font-family:{theme.MONO_FAMILY}; }}
  .src {{ color:{theme.TEXT_MUTED}; font-size:12px; }}
</style>
"""  # i18n: skip


class HelpTab(QWidget):
    """List on the left, body on the right. Search narrows the list."""

    def __init__(self, project=None, parent=None):
        super().__init__(parent)
        self.project = project
        self._build()
        self._filter("")
        self.list.setCurrentRow(0)

    def _build(self) -> None:
        self._topics = topics()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        head = PageHeader(tr("Help — the questions this tool is likely to raise"),
                          tr("Each topic ends with the code locations that back its explanation."))
        self.search = QLineEdit(placeholderText=tr("Search  (e.g. discriminability, locked, excel, slow)"))
        self.search.setFixedWidth(300)
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        head.add_right(self.search)
        root.addWidget(head)

        split = QSplitter(Qt.Horizontal)
        self.list = QListWidget()
        self.list.setFixedWidth(272)
        self.list.setWordWrap(True)          # long titles wrap instead of clipping
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setStyleSheet(
            f"QListWidget{{border:1px solid {theme.BORDER}; border-radius:6px;"
            f"background:{theme.BG}; padding:4px;}}"
            f"QListWidget::item{{padding:7px 8px; border-radius:5px;}}"
            f"QListWidget::item:selected{{background:{theme.ACCENT_SOFT}; color:{theme.TEXT};}}"
            f"QListWidget::item:hover{{background:{theme.SURFACE};}}")
        self.list.currentRowChanged.connect(self._show)
        split.addWidget(self.list)

        self.view = QTextBrowser(openExternalLinks=False)
        self.view.setStyleSheet(f"border:1px solid {theme.BORDER}; border-radius:6px;"
                                f"padding:6px 12px; background:{theme.BG};")
        split.addWidget(self.view)
        split.setSizes([272, 860])
        root.addWidget(split, 1)

        self.hint = QLabel(tr("The README covers installation and the Windows build."))
        self.hint.setStyleSheet(theme.muted())
        root.addWidget(self.hint)

    # ── the list ───────────────────────────────────────────────────
    def _filter(self, text: str) -> None:
        q = text.strip().lower()
        self.shown = [t for t in self._topics if not q or q in t.searchable()]
        self.list.clear()
        for t in self.shown:
            it = QListWidgetItem(t.title)
            it.setToolTip(t.title)
            self.list.addItem(it)
        if self.shown:
            self.list.setCurrentRow(0)
        else:
            self.view.setHtml(_CSS + _p(tr("Nothing matches '{q}'.", q=text)))

    def _show(self, row: int) -> None:
        if not (0 <= row < len(self.shown)):
            return
        t = self.shown[row]
        src = ""
        if t.code:
            items = "".join(f"<li><code>{c}</code></li>" for c in t.code)
            src = tr("<h3>Backing code and documents</h3><ul class='src'>{items}</ul>", items=items)
        self.view.setHtml(_CSS + f"<h2>{t.title}</h2>" + t.body + src)
        self.view.verticalScrollBar().setValue(0)

    def show_topic(self, key: str) -> bool:
        """Used when a \"why?\" link on another screen jumps straight here."""
        self.search.clear()
        for i, t in enumerate(self.shown):
            if t.key == key:
                self.list.setCurrentRow(i)
                return True
        return False
