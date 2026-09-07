# seqopt — sequential optimization for lab experiments

*[한국어](README.ko.md)* · The program itself speaks both languages — switch it on the start
screen or from the **Language** menu; the first run follows your OS language.

**Enter your measurements and it tells you which condition to measure next —
and whether that advice can be trusted at all.**

▶ **[What is sequential optimization? — an interactive explainer](https://euichanlee0608-svg.github.io/seqopt/)**
 · five minutes, no install, English and Korean. The Gaussian process runs in
 your browser; the figures come out of this repo's own diagnostic code.

The second half is the point. Plenty of tools already suggest the next
experiment. What none of them told the researcher was whether the suggestion
meant anything — so this one **checks the reliability of its own advice first,
and refuses to advise when the data cannot support it.**

### Nothing to choose

| tool | what the user must choose |
|---|---|
| AutoOED | surrogate · acquisition · multi-objective solver · selection strategy — four dropdowns |
| MADGUI | ElasticNet / RandomForest / XGBoost · cross-validation scheme |
| OPTIMEO | DoE type · model · acquisition |
| **seqopt** | **nothing** — fixed kernel · fixed EI · fixed model |

The gate is what makes the fixing affordable. When the data is bad, other
tools hand you a menu of models to wander through; this one rules **"changing
the model will not help"** and locks the recommendation instead. Everything
removed from the front is still there under each screen's *Advanced ▸* fold —
deferred, not deleted.

### The four gates — fail any one and the recommendation locks

| | gate | what it checks | when it fails |
|---|---|---|---|
| ① | candidate count | does the declared design space (ranges × grid steps) hold more candidates than the budget? | measuring everything is better |
| ② | surface learnability | is the model learning (LOOCV R² > 0)? | changing the model will not help |
| ③ | discriminability | do condition differences exceed the measurement wobble? | raise the replicates |
| ④ | replicates | has any condition been re-measured? | the wobble itself is unknowable |

The lock is enforced by the return type, not by UI discipline:
`recommend()` returns `Recommendation | Locked`, and `Locked` **carries no
suggestion fields at all** — there is nothing for a screen to misuse.

---

## Windows — just run it (no Python needed)

1. Open the **Actions** tab of this repository
2. Pick **windows-build** on the left and click the newest green ✅ run
3. Download **`seqopt-windows`** under *Artifacts* at the bottom
4. **Extract the zip first** (running the exe from inside the zip viewer will fail)
5. Double-click **`seqopt.exe`** inside the extracted `seqopt` folder

> The two most common mistakes:
> - **Running from inside the zip** — Explorer shows a zip like a folder, but
>   double-clicking there unpacks only the exe, without the files next to it.
> - **Moving just the exe** — it needs its folder. Move the whole folder.
>   (That folder layout is also why it opens in ~4 seconds.)
>
> If Windows shows the blue *SmartScreen* dialog, click **More info → Run
> anyway** — it appears because the binary is unsigned.

Something still wrong? Run `seqopt.exe --selftest` from a command prompt: it
says what is missing and writes `selftest.txt` next to the exe. Startup is
logged stage by stage to `%USERPROFILE%\.seqopt\seqopt.log` (a splash card
shows the same stages while the heavy libraries load), and crashes are logged
with full detail to `%USERPROFILE%\.seqopt\error.log`.

Want to see the program before downloading it? The same CI run also uploads
**`seqopt-windows-shots`** — a screenshot of every tab of every bundled
example, taken on the runner's real Windows display after the build.

### Build it yourself on Windows

1. Install [Python 3.11](https://www.python.org/downloads/release/python-3119/)
   (check **"Add python.exe to PATH"**)
2. *Code → Download ZIP* on this page, extract
3. Double-click **`packaging\build_windows.bat`**
4. The result is **`dist\seqopt\seqopt.exe`**

The batch file creates a venv, installs dependencies, **runs the regression
tests**, and only then builds — a program that misjudges must never get
packaged.

## macOS / from source

```bash
git clone https://github.com/euichanlee0608-svg/seqopt && cd seqopt
uv venv --python 3.11 .venv          # or: python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt PySide6 matplotlib reportlab
.venv/bin/python app.py
```

For a bundled app: `packaging/build_macos.sh` → `dist/seqopt.app`

---

## First launch

Two examples ship with the program:

- **Synthetic annealing (crystallinity)** — simulated data, 42 runs on a
  temperature × time grid (252 candidate conditions, budget 60). It passes all
  four gates, so you can see what a recommendation looks like and why; the true
  optimum is 290 °C / 40 min, and that is what comes out.
- **P3HT:CNT conductivity** — 48 conditions of real published thin-film
  measurements (*Adv. Funct. Mater.* 2021, public dataset). Delete rows or
  replicates on the Data tab and watch the gate lock.

| tab | what it does |
|---|---|
| 1 Setup | define the knobs (inputs) with the grid step the instrument can actually be set to, an optional sum constraint (e.g. fractions adding up to 100 %), the objective, and the budget |
| 2 Data | import from Excel/CSV, paste, or type; Ctrl+Z undo |
| 3 **Diagnose** | **the heart of the tool** — the four-gate verdict, with every calculation unfolded |
| 4 Model | response surface · uncertainty · EI · sensitivity |
| 5 Recommend | the next condition(s) on the declared grid and inside the constraint, locked until the gates pass |
| 6 Report | PDF · calculation log · a script that reproduces every number |
| ? Help | searchable answers, each backed by a code reference |

Every number traces back: the Diagnose tab unfolds the per-condition table
behind σw/σb/D, the report ships the full calculation log, and the exported
Python script re-derives the same numbers from the raw data alone.

---

## For developers

**Structure** — `core/` (computation, never imports the GUI) ↔ `ui/` (screens,
never judges). Everything in `core/` runs from the CLI.

Surrogates and acquisitions are registry plugins — one class, no other change:

```python
@ACQUISITIONS.register("PI")
class ProbabilityOfImprovement:
    label = "PI — probability of improvement"
    supports_continuous = True
    def score(self, model, X, best, rng=None): ...
    def describe(self): return "PI"
```

**The gate is not a plugin.** Refusing to optimize on data that cannot support
it is this tool's reason to exist (see `docs/ARCHITECTURE.md`).

**Why only EI · UCB · Thompson on screen.** Four global-search alternatives
(max-value entropy search, EI with exploration mixing, a GP-UCB schedule, a
Thompson variant) were benchmarked against them on 8 test functions × 10
seeds under a rule fixed before measuring — ship a candidate only if it beats
EI on multimodal functions without losing on unimodal ones. None did. The
numbers are in `docs/bench_global.json`, the write-up in
`docs/GLOBAL_SEARCH.md`, the candidates in `packaging/bench_global.py`, and
`tests/test_global.py` fails the day a candidate does beat EI — that is the
signal to promote it.

```bash
.venv/bin/python -m pytest tests -q
```

The suite anchors on two kinds of expectations: a **synthetic lab spreadsheet**
(`tests/data/make_synthetic.py` — generated with independent numpy formulas,
seed pinned, engineered to sit in exactly the regime this tool exists to
catch), and the **original validation study's numbers** for three public
datasets (P3HT-CNT · AgNP · Perovskite, from
[PV-Lab/Benchmarking](https://github.com/PV-Lab/Benchmarking)).

Three things not to change (details in `docs/ARCHITECTURE.md`):

1. **The GP kernel** — exactly one combination reproduces the regression expectations
2. **LOOCV to closed form** — 200× faster, and the gate verdict flips. Slow is correct
3. **The `scikit-learn==1.8.0` pin** — the regression expectations were made under it

## Provenance

This tool grew out of a decision study for a device lab: whether to adopt
sequential Bayesian optimization at all. Measured on three public datasets the
method saved real measurements; applied to the lab's own data, every dataset
failed the gates — so the recommendation was *not yet*, and the gates became
this program. The lab's raw data is **not** included in this repository; the
public datasets and a synthetic stand-in with the same structure are.

## License

MIT — see [LICENSE](LICENSE).
