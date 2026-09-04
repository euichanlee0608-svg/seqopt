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

from . import theme
from .widgets.section import PageHeader


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


def _table(head: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{th}</tr>{tr}</table>"


# ══════════════════════════════════════════════════════════════════════
# Content
# ══════════════════════════════════════════════════════════════════════
TOPICS: list[Topic] = [
    # ── getting started ────────────────────────────────────────────
    Topic("start", "What is this program", tags="overview start introduction",
          body=_p(
              "<b>Enter your measurements and it tells you which condition to "
              "measure next — and whether that advice can be trusted at all.</b>",
              "The second half is the point. Plenty of tools already suggest the "
              "next condition. This one <b>checks the advice's reliability first, "
              "and refuses to advise when the data falls short.</b>") +
          "<h3>Why it was built this way</h3>" +
          _p("While validating this method, the same question was answered <b>four "
             "times and got it wrong three times.</b> The cause was never a code "
             "bug — it was <b>never asking whether the data could support the "
             "question at all.</b>",
             "One real lab dataset from that study had a learnability of "
             "R² = −0.272 — worse than always answering the overall mean. Feed it "
             "to an ordinary optimization tool and you get <b>a smooth response "
             "surface and a plausible next candidate anyway.</b> Trust that, and "
             "you spend time and samples on noise."),
          code=["core/diagnostics.py: gate()", "docs/ARCHITECTURE.md"]),

    Topic("simple", "Why are there so few choices", tags="simple choices advanced defaults algorithm kernel",
          body=_p("Deliberately. Compared with other optimization tools:") +
          _table(["tool", "what the user must choose"], [
              ["AutoOED", "surrogate · acquisition · multi-objective solver · selection strategy — four dropdowns"],
              ["MADGUI", "ElasticNet / RandomForest / XGBoost · cross-validation scheme"],
              ["OPTIMEO", "DoE type · model · acquisition"],
              ["<b>this program</b>", "<b>none</b> — fixed kernel · fixed EI · fixed model"]]) +
          "<h3>Why fixing them is affordable</h3>" +
          _p("<b>Because the gate exists.</b> Other tools hand you choices so you "
             "can wander between models when the data is bad. This program rules "
             "<b>\"changing the model will not help\"</b> — so there is nothing to choose.",
             "In the validation study, six model families were tried on a bad "
             "dataset and <b>not one</b> reached R² > 0. Offer a menu there, and "
             "people spend their time hunting for an answer that does not exist.") +
          "<h3>If you still want to change things</h3>" +
          _p("Unfold <b>\"Advanced ▸\"</b> on each screen — acquisition function, "
             "batch size, target discriminability, log transform and the initial "
             "design size are all there. Not removed. <b>Deferred.</b>"),
          code=["ui/widgets/advanced.py", "core/surrogate.py: DEFAULT_SURROGATE"]),

    Topic("flow", "In what order do I use it", tags="order flow workflow first",
          body="<h3>Starting a new experiment</h3>" +
          _ul("<b>Setup</b> — define your knobs (inputs), the objective, and the budget",
              "<b>Setup → generate initial design</b> — get the first measurement points as CSV",
              "Measure them in the lab",
              "<b>Data</b> — enter the values (paste · import · type)",
              "<b>Diagnose</b> — check the four requirements ← <b>this is the fork</b>",
              "Pass → get the next condition on <b>Recommend</b>, and repeat 4–6",
              "Fail → fix the data first, following the <b>prescription</b> on the Diagnose tab") +
          "<h3>Diagnosing a spreadsheet you already have</h3>" +
          _ul("<b>Data → import from file</b> and map the columns",
              "Read the verdict table on <b>Diagnose</b>",
              "Keep the evidence as a PDF with <b>Report</b>"),
          code=["ui/main_window.py: recompute()"]),

    # ── the requirements ───────────────────────────────────────────
    Topic("gate", "The four requirements — what and why", tags="gate requirements verdict locked",
          body=_p("All four must pass before recommendations open. "
                  "A single <b>×</b> locks them.") +
          _table(["", "requirement", "what it checks", "when it fails"], [
              ["①", "condition count", "are there more candidates than budget",
               "measuring everything is better (the gain from optimizing is zero in principle)"],
              ["②", "surface learnability", "is the model learning the terrain (LOOCV R² > 0)",
               "changing the model will not help. The data is the problem"],
              ["③", "discriminability", "do condition differences exceed the measurement wobble",
               "raise the replicate count"],
              ["④", "replicates", "has the same condition ever been re-measured",
               "the wobble's size is unknowable (a warning — it does not lock)"]]) +
          _p("<b>Any of ①②③ failing locks the gate.</b> ④ is a warning.",
             "Learnability R² is slow, so it runs in the background. "
             "<b>The lock holds while it computes</b> — the unknown is never counted as a pass."),
          code=["core/diagnostics.py: gate()", "core/recommend.py: recommend()"]),

    Topic("d", "What is discriminability (D)", tags="discriminability D sigma noise wobble replicates bootstrap",
          body=_p("<b>The difference that changing the condition makes</b>, divided by "
                  "<b>the wobble of re-measuring the same condition.</b> Above 1 means "
                  "\"neighboring conditions can be told apart\".") +
          "<pre>σw = √( Σ(n−1)·var(replicates per condition) / Σ(n−1) )   ← conditions with ≥2 replicates only\n"
          "σb = std( condition means , ddof=1 )\n"
          "D(n) = σb / (σw / √n)</pre>" +
          _p("<b>An analogy</b> — telling apart two people who differ by 1 kg, on a "
             "scale that jumps ±2 kg per reading. No amount of cleverness helps. "
             "It is the scale's fault.") +
          "<h3>Why the point estimate is not enough</h3>" +
          _p("Conditions are resampled with replacement and D is recomputed "
             "<b>4000 times</b> for a 95% interval. When that interval straddles "
             "the threshold of 1.0, the screen says <b>\"undecided\"</b>.",
             "The validation study hit exactly this case — D = 1.03 looked passed, "
             "but the interval was [0.49, 1.80], so <b>neither passed nor failed "
             "could honestly be claimed.</b>"),
          code=["core/diagnostics.py: discriminability()", "tests/test_diagnostics.py"]),

    Topic("levels", "Where do the thresholds 1 · 2 · 3.5 come from", tags="threshold recommended basis prescription replicates how many",
          body=_p("The discriminability gauge carries three marks. <b>The gate is 1, "
                  "alone</b>; the other two are marks for reading \"how comfortable\". "
                  "None of them is arbitrary.") +
          _table(["mark", "name", "meaning", "basis"], [
              ["D ≥ 1", "gate (minimum)", "difference = wobble",
               "Follows from the definition. With σb &lt; σw, the difference made by "
               "changing conditions is smaller than the wobble of re-measuring — "
               "rankings may be noise."],
              ["D ≥ 2", "recommended", "difference ≈ wobble × 2",
               "Two means about two standard errors apart — the usual statistical "
               "boundary for \"different\" (95%, z ≈ 1.96)."],
              ["D ≥ 3.5", "comfortable", "difference ≈ wobble × 3.5",
               "Matches measurement-system analysis (AIAG MSA), where a usable "
               "instrument needs ndc = 1.41·σb/σw ≥ 5 distinct categories."]]) +
          "<h3>How the prescription table is computed</h3>" +
          _p("With n replicates per condition the mean's wobble shrinks to σw/√n, "
             "so D(n) = σb/(σw/√n). Solving for n gives <b>n = ⌈(target D · σw / σb)²⌉</b>. "
             "\"Extra runs\" sums, per condition, the gap between its current "
             "replicates and n.",
             "<b>Caution</b> — the calculation assumes <b>σw stays what it is now.</b> "
             "More replicates change the σw estimate itself, so measure up to the "
             "recommended row and <b>diagnose again</b>.") +
          "<h3>And the nugget-ratio threshold of 0.3?</h3>" +
          _p("This tool calls a surface rough above a nugget ratio of 0.3. The widely "
             "used geostatistics scale (Cambardella 1994) — &lt;0.25 strong spatial "
             "structure · 0.25–0.75 moderate · &gt;0.75 weak — is shown alongside "
             "on the Diagnose tab."),
          code=["core/diagnostics.py: D_LEVELS · replicate_plan() · NUGGET_CLASSES",
                "tests/test_diagnostics.py"]),

    Topic("r2", "What does a negative learnability R² mean", tags="R2 learnability LOOCV negative surface",
          body=_p("Each condition is left out in turn, the model is fitted on the rest, "
                  "and the left-out condition is predicted (LOOCV). "
                  "R² = 1 − SS_res/SS_tot.",
                  "<b>R² ≤ 0 means worse than always answering the overall mean.</b> "
                  "The model has learned nothing.") +
          "<h3>Why changing the model will not help</h3>" +
          _p("The validation study ran six families (constant, linear, quadratic, GP, "
             "RF, …) on such a dataset, and <b>not one reached R² > 0.</b> When the "
             "signal is not in the data, no model can learn it.",
             "Look at the scatter on the <b>Validation tab</b>. Points clustering "
             "around the red \"always answer the mean\" line instead of the diagonal — "
             "that is what R² < 0 looks like."),
          code=["core/diagnostics.py: loocv_r2()", "ui/tab_model.py: _plot_loocv()"]),

    Topic("nugget", "Nugget ratio · terrain roughness", tags="nugget sill semivariogram terrain roughness",
          body=_p("A semivariogram is built from condition-pair distances and value "
                  "differences: how much difference survives even at near-zero "
                  "distance (<b>the nugget</b>), as a share of the height reached far "
                  "away (<b>the sill</b>).") +
          "<pre>nugget ratio = nugget / sill      &gt; 0.3 counts as a 'rough surface'</pre>" +
          _p("A large nugget ratio means <b>most of the visible variation is "
             "measurement wobble.</b> The lab dataset in the validation study sat at "
             "0.489, with a noise share of <b>95%</b>.") +
          "<h3>Caution — it does not predict the ordering</h3>" +
          _p("The original write-up claimed the nugget-ratio ordering matches the R² "
             "ordering exactly. Checked against the actual values, <b>it does not "
             "hold</b> (one dataset has the lower nugget ratio and the lower R²). "
             "What does hold is the <b>separation between the smooth and the rough.</b>"),
          code=["core/diagnostics.py: nugget_ratio()"]),

    # ── the screens ────────────────────────────────────────────────
    Topic("import", "My spreadsheets differ every time", tags="import excel column mapping preset format csv",
          body=_p("Which is why the program does not guess the format. "
                  "<b>The original shows on the left, and you assign the columns' "
                  "meanings on the right.</b>") +
          _ul("Changing a role recolors the left column instantly (blue=input · green=response · gray=ignore)",
              "<b>Before you press Import</b>, the bottom shows \"N conditions · N "
              "measurements · N missing\". Check that those match what you expect, then press",
              "<b>Save a preset</b> and the next file from the same instrument loads in one step",
              "The mapping is also stored in the project file, so reopening reads identically") +
          "<h3>How the role guessing works</h3>" +
          _p("<b>Design axes recycle their values; measurement columns differ on "
             "almost every row.</b> Only numeric columns with a low distinct-value "
             "ratio become input candidates. This one rule keeps intermediate "
             "measurement columns (raw band intensities and the like) from being "
             "mistaken for inputs."),
          code=["core/profile.py: guess_profile()", "core/importer.py: apply_profile()"]),

    Topic("reps", "May I enter the same condition several times", tags="replicates duplicates rows",
          body=_p("<b>You should.</b> One row = one measurement, and the same "
                  "condition on several rows is automatically read as <b>replicates</b>.",
                  "Without replicates, σw (the measurement wobble) cannot be computed "
                  "and requirement ③ shows <b>\"not computable\"</b>. The program "
                  "<b>does not substitute an assumed value</b> — it refuses to "
                  "pretend to know what it does not."),
          code=["core/dataset.py: group_measurements()"]),

    Topic("colors", "What do the table colors mean", tags="colors background yellow red gray legend table",
          body=_table(["color", "meaning", "where"], [
              [f"<span style='background:{theme.ROW_ZERO}'>&nbsp;yellow&nbsp;</span>",
               "a zero-response row · a condition with only one replicate", "Data · Diagnose"],
              [f"<span style='background:{theme.ROW_EXCLUDED}'>&nbsp;pink&nbsp;</span>",
               "an excluded row · the variance-dominating condition", "Data · Diagnose"],
              [f"<span style='background:{theme.ROW_PENDING}'>&nbsp;blue&nbsp;</span>",
               "a row pre-filled from a recommendation (not yet measured)", "Data"],
              [f"<span style='background:{theme.ACCENT_SOFT}'>&nbsp;sky&nbsp;</span>",
               "a column assigned as an input", "Import"],
              [f"<span style='background:{theme.OK_SOFT}'>&nbsp;green&nbsp;</span>",
               "the column assigned as the response", "Import"]]) +
          "<h3>Figure colors</h3>" +
          _ul("<b>μ (predicted mean)</b> — viridis. Magnitude",
              "<b>σ (uncertainty)</b> — grayscale. It is \"how unknown\", not a value",
              "<b>EI (acquisition)</b> — warm. The one color that calls for action",
              "No rainbow (jet) — it invents boundaries that do not exist"),
          code=["ui/theme.py", "core/plotstyle.py"]),

    # ── recommendations ────────────────────────────────────────────
    Topic("locked", "It is locked — can I not just use it anyway", tags="locked force override bypass unmet",
          body=_p("You can. Turn on <b>\"Force a recommendation despite unmet "
                  "requirements\"</b> on the Recommend tab.",
                  "But <b>it leaves a mark</b> — on the result screen, in the "
                  "instruction-sheet CSV, and as a <b>\"REQUIREMENTS UNMET\" stamp on "
                  "every page of the PDF report.</b> Screenshot a single page into a "
                  "slide and the warning travels with it.") +
          "<h3>Try these first</h3>" +
          _ul("Put a target discriminability into the <b>prescription</b> on the "
              "Diagnose tab — it back-computes how many more replicates you need",
              "If the <b>warning</b> box says one condition carries N% of the "
              "variance, re-measuring that condition is the cheapest check",
              "If requirement ① is the problem, widening the design range or "
              "shrinking the budget is the honest fix"),
          code=["core/recommend.py: recommend(override=...)", "core/report.py: write_pdf()"]),

    Topic("acq", "Which of the three methods should I use", tags="acquisition EI UCB Thompson beta explore method",
          body=_p("Chosen at the <b>top of the Recommend tab</b>. Without a specific "
                  "reason, keep the default.") +
          _table(["", "what", "when"], [
              ["<b>Default (EI)</b>", "Expected improvement — how much a candidate should beat the best so far",
               "Almost always. In the validation study it actually measured the "
               "global optimum within a 40-run budget 69–93% of the time"],
              ["<b>Explore wider (UCB)</b>", "μ + b·σ. A larger b pushes into uncertainty",
               "When the terrain is still unknown. Mind the caution below"],
              ["<b>Diversify (Thompson)</b>", "draw one function from the posterior, take its maximum",
               "When receiving several at once — candidates do not pile up in one spot"]]) +
          "<h3>Caution — pushing exploration harder does not help</h3>" +
          _p("Raising UCB's b from 1 to 4 dropped the global-optimum hit rate from "
             "<b>90% to 61%</b> in the validation study. Pure space-filling was the "
             "worst at 1–7%. Do not casually raise the default b = 2.0."),
          code=["core/acquisition.py"]),

    Topic("batch", "Can I get several at once", tags="batch several at once",
          body=_p("Up to 10, via <b>\"At a time\"</b> under Advanced on the Recommend tab.",
                  "They are picked sequentially, each picked point <b>assuming its "
                  "predicted mean as if observed</b> before the model refits for the "
                  "next pick (kriging believer). No unmeasured value is ever "
                  "consulted, so the <b>no-lookahead rule</b> holds."),
          code=["core/acquisition.py: batch_picks()"]),

    Topic("reps_rec", "Why does the recommendation carry a suggested replicate count", tags="suggested replicates instruction count",
          body=_p("Measure a new condition <b>only once and discriminability drops</b>, "
                  "worsening the next verdict. So \"measure it n times\" goes on the "
                  "instruction sheet.",
                  "The value follows the <b>median</b> replicate count of the current data."),
          code=["core/recommend.py: recommended_reps()"]),

    Topic("extrap", "It says \"outside measured range\"", tags="extrapolation outside range warning",
          body=_p("The model learned <b>the range you actually measured.</b> Where the "
                  "declared range on the Setup tab is wider, the outside is somewhere "
                  "the model has never seen.",
                  "<b>It is not blocked</b> — widening the range and measuring there "
                  "is sometimes exactly the right move. But it is always marked."),
          code=["core/recommend.py: _axis_bounds()"]),

    # ── trust ──────────────────────────────────────────────────────
    Topic("logic", "What is it computing inside", tags="logic algorithm GP kernel EI principle formulas",
          body="<h3>In one line</h3>" +
          _p("From the measured conditions it estimates the <b>response surface</b> "
             "(input → output), with a model that also reports its own "
             "<b>uncertainty</b>. Then \"how much would measuring here teach\" is "
             "scored, and the highest scorer wins.") +
          "<h3>1. The surrogate — a Gaussian process</h3>" +
          "<pre>ConstantKernel × Matern(ν=2.5, ARD) + WhiteKernel</pre>" +
          _ul("<b>Matern ν=2.5</b> — smooth but not overly smooth. A common fit for experimental surfaces",
              "<b>ARD</b> — one length scale per variable. The sensitivity view comes from here",
              "<b>WhiteKernel</b> — absorbs measurement noise. It earns its keep once replicates exist",
              "The model learns <b>condition means</b>. Replicates feed discriminability (gate ③)") +
          "<h3>2. The acquisition — choosing where to measure next</h3>" +
          "<pre>EI  = (μ − best)·Φ(z) + σ·φ(z),   z = (μ − best)/σ\n"
          "UCB = μ + b·σ\n"
          "TS  = one posterior draw, take its maximum</pre>" +
          _p("<b>best is always the best measured value.</b> Use a true or corrected "
             "value and the choice no longer matches what a researcher would actually do.") +
          "<h3>3. The diagnostics — what only this tool does</h3>" +
          "<pre>σ<sub>w</sub> = √( Σ(n−1)·var(replicates) / Σ(n−1) )    measurement wobble\n"
          "σ<sub>b</sub> = std( condition means , ddof=1 )         between-condition difference\n"
          "D(n) = σ<sub>b</sub> / (σ<sub>w</sub>/√n)                        discriminability\n\n"
          "R² = 1 − SS_res/SS_tot   (per-condition LOOCV, refit per fold)\n"
          "nugget ratio = nugget / sill   (semivariogram)</pre>" +
          _p("Discriminability comes with a 95% interval from a <b>4000-draw "
             "condition bootstrap</b>. When the interval straddles 1.0, the verdict "
             "is \"undecided\"."),
          code=["core/surrogate.py", "core/acquisition.py", "core/diagnostics.py"]),

    Topic("verified", "Has it been validated", tags="validation trust tests reproduce evidence measured",
          body="<h3>How far the validation goes</h3>" +
          _table(["part", "status", "evidence"], [
              ["<b>diagnostic calculations</b><br>discriminability · learnability · nugget",
               "<b>validated</b>",
               "the test suite pins the numbers the original validation scripts "
               "produced, to within 1e-3; the public-dataset expectation file "
               "(verify_terrain.json) ships in this repo"],
              ["<b>the gate verdict</b>", "<b>validated</b>",
               "the same yardstick applied to four datasets (one lab, three public) "
               "reproduced the original analysis' split"],
              ["single recommendations (EI · GP)", "within the original study's scope",
               "the global optimum was actually measured within a 40-run budget "
               "69–93% of the time"],
              ["batch recommendations", "<b>not validated</b>",
               "only checked that distinct points come out. Whether batches beat "
               "sequential picking was never measured"],
              ["the random-forest surrogate", "<b>not validated</b>",
               "its uncertainty calibration was never checked. Comparison only"],
          ]) +
          "<h3>Numbers pinned by the tests (public datasets)</h3>" +
          _table(["item", "value"], [
              ["external discriminability D", "P3HT-CNT 6.76 · AgNP 4.28 · Perovskite 1.82"],
              ["terrain nugget ratios", "P3HT-CNT 0.082 · AgNP 0.032 · Perovskite 0.404"],
          ]) +
          _p("The lab dataset the study was run for is <b>not distributed</b> with "
             "this repository; the numbers quoted in this help (R² = −0.272, "
             "D = 1.03 [0.49, 1.80], noise share 95%) are that study's published "
             "aggregates.") +
          "<h3>Held in place by machines</h3>" +
          _p("The test suite re-verifies these values on every run. Change the "
             "calculation and the tests break — that is the tripwire.",
             "The Windows executable is only built <b>after the tests pass</b>. "
             "A program that misjudges must never get packaged.") +
          "<h3>What honestly was not done</h3>" +
          _ul("Whether batch recommendations beat sequential ones was <b>never measured</b>",
              "The extrapolation margin of 0.02 was <b>chosen without evidence</b>",
              "Of the four gate thresholds, only <b>R² > 0</b> has a hard basis. "
              "The discriminability 1.0 is borrowed from other fields, so it is "
              "safest in \"A vs B\" comparisons",
              "The stopping-rule history resets when the program restarts"),
          code=["docs/ARCHITECTURE.md", "tests/test_diagnostics.py", "tests/data/verify_terrain.json"]),

    Topic("trust", "Can I trust these numbers", tags="validation trust evidence tests reproduce",
          body="<h3>Three ways to check</h3>" +
          _ul("<b>Diagnose tab → unfold the calculation</b> — per-condition n, mean, "
              "SD and contribution are all visible, and the σw·σb·D in the box "
              "below come straight from that table",
              "<b>Report → calculation log</b> — every number's formula and "
              "intermediate values, saved as text",
              "<b>Report → reproduction script</b> — one file that produces the same "
              "numbers again. Half a year later, \"where did this number come "
              "from\" still has an answer") +
          "<h3>Machine-checked</h3>" +
          _p("The computation core is pinned by tests that reproduce the original "
             "validation scripts' values to within 1e-3 (the external datasets' "
             "D values and terrain statistics among them).",
             "So <b>changing the calculation breaks the tests.</b> That is the tripwire."),
          code=["tests/test_diagnostics.py", "tests/data/verify_terrain.json"]),

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
              "<b>Constraints</b> — e.g. compositions summing to 100%. <b>First on the roadmap</b>",
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
"""


class HelpTab(QWidget):
    """List on the left, body on the right. Search narrows the list."""

    def __init__(self, project=None, parent=None):
        super().__init__(parent)
        self.project = project
        self._build()
        self._filter("")
        self.list.setCurrentRow(0)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        head = PageHeader("Help — the questions this tool is likely to raise",
                          "Each topic ends with the code locations that back its explanation.")
        self.search = QLineEdit(placeholderText="Search  (e.g. discriminability, locked, excel, slow)")
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

        self.hint = QLabel("The README covers installation and the Windows build.")
        self.hint.setStyleSheet(theme.muted())
        root.addWidget(self.hint)

    # ── the list ───────────────────────────────────────────────────
    def _filter(self, text: str) -> None:
        q = text.strip().lower()
        self.shown = [t for t in TOPICS if not q or q in t.searchable()]
        self.list.clear()
        for t in self.shown:
            it = QListWidgetItem(t.title)
            it.setToolTip(t.title)
            self.list.addItem(it)
        if self.shown:
            self.list.setCurrentRow(0)
        else:
            self.view.setHtml(_CSS + _p(f"Nothing matches '{text}'."))

    def _show(self, row: int) -> None:
        if not (0 <= row < len(self.shown)):
            return
        t = self.shown[row]
        src = ""
        if t.code:
            items = "".join(f"<li><code>{c}</code></li>" for c in t.code)
            src = f"<h3>Backing code and documents</h3><ul class='src'>{items}</ul>"
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
