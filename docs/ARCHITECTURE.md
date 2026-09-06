# Architecture — what can be swapped, and what cannot

> Reading this one document should tell you where a new feature attaches.

## In one line

**The UI never judges. The core never knows the screen exists. The gate is not a plugin.**

---

## 1. The layers

```
app.py                 entry point
│
├── ui/                screens — display and accept input. Never judge.
│   ├── main_window.py     tab container · status-bar gate badges · state-flow conductor
│   ├── tab_setup.py       ① variables · objective · budget
│   ├── tab_data.py        ② measurement table · paste · undo
│   ├── tab_diag.py        ③ gate verdict · unfolded calculations · prescription
│   ├── tab_model.py       ④ response surface · validation figures
│   ├── tab_recommend.py   ⑤ next candidates · instruction sheet
│   ├── import_wizard.py   data-structure setup
│   ├── worker.py          slow computation off the UI thread
│   └── widgets/plots.py   single source for figure colors and fonts
│
└── core/              computation — never imports the GUI. Everything runs from the CLI.
    ├── protocols.py       contracts of the swappable parts (Surrogate · Acquisition)
    ├── registry.py        name → part registry
    ├── spec.py            VarSpec · ObjSpec · Dataset
    ├── importer.py        xlsx/csv reading
    ├── profile.py         "how to read this spreadsheet" (reusable presets)
    ├── dataset.py         condition grouping · exclusions · normalization
    ├── surrogate.py       surrogate models     ← swappable
    ├── acquisition.py     acquisition functions ← swappable
    ├── design.py          initial design (maximin LHS)
    ├── diagnostics.py     discriminability · LOOCV · nugget ratio · sensitivity · **the gate**
    ├── surface.py         response-surface grids (the material of the figures)
    ├── recommend.py       **the one entrance to a recommendation**
    └── project.py         .seqopt save/load
```

**One rule** — `from PySide6 ...` appearing inside `core/` is a bug. The tests
must run on `core/` alone; that is also what keeps a CLI, web, or notebook
frontend possible later.

---

## 2. Swappable

### 2-1. Surrogates (`core/surrogate.py`)

```python
@SURROGATES.register("my-model")
class MyModel:
    label = "My model"
    def fit(self, X, y) -> "MyModel": ...
    def predict(self, X) -> tuple[np.ndarray, np.ndarray]:   # (mean, std)
    def sample(self, X, rng) -> np.ndarray: ...
    def length_scales(self) -> np.ndarray | None: ...        # None if the model has none
```

That is all. The screen list, the report and the recommendation path follow
automatically.

- `predict` returning **uncertainty alongside the mean** is the heart of the
  contract. A model that cannot produce it cannot feed an acquisition function.
- `length_scales() → None` makes the sensitivity bars quietly disappear —
  **zeros are never invented** (`RandomForestSurrogate` is the example).

### 2-2. Acquisitions (`core/acquisition.py`)

```python
@ACQUISITIONS.register("PI")
class ProbabilityOfImprovement:
    label = "PI — probability of improvement"
    supports_continuous = True
    def score(self, model, X, best, rng=None) -> np.ndarray: ...
    def describe(self) -> str: ...        # lands in the report, parameters included
```

- `supports_continuous=False` restricts maximization to candidate enumeration
  (Thompson sampling is the example).
- `best` is always **the best measured value** (principle P3) — never a true
  or corrected value.

---

## 3. Not swappable — the gate

The only path to a recommendation is `core.recommend.recommend()`, and it
returns `Recommendation | Locked`. `Locked` **has no suggestion fields**, so a
screen cannot take out what is not there. A forced run (`override=True`) works
but marks the result, and the report stamps every page.

Do not add a convenience function that skips the gate. Making the gate
replaceable erases the tool.

## 4. State flow (§7-3)

One direction only:

```
measurement change → Dataset.build() → diagnostics (fast) → diagnostics (slow, background) → gate → screens
```

No partial updates — a stale-state screen is the most dangerous bug this
program can have. The slow half (LOOCV) runs on a worker thread, and only the
newest request survives (`DiagnosticsRunner`).

## 5. Hard-won constraints

| do not | because |
|---|---|
| rebuild the GP kernel | exactly one combination reproduces the regression expectations |
| replace LOOCV with the closed form | 200× faster, and the gate verdict flips (R² −0.27 → +0.23 on real data) |
| raise the `scikit-learn==1.8.0` pin | GP hyperparameter optimization drifts >1e-3 across versions; expectations break |
| return PyInstaller to onefile | 61 s to first window (measured); onedir shows in 4 s |
| import matplotlib before the window shows | the font-cache scan froze startup for 100+ s (measured) |
| repaint hidden tabs / whole tables per keystroke | 972 ms per edited cell before the fix, 1 ms after |
| auto-update a regression expectation | that is how regressions get through — say what changed first |

## 6. Two languages — English is the key, Korean is the catalog

Every string a user can see goes through `tr()` (`core/i18n.py`). The English
text **is** the key; the Korean lives next to it in `core/lang/ko_*.py`, one
file per area (`shell` · `data` · `model` · `diag` · `help` · `report` ·
`core`), merged into one dictionary at import. A missing key falls back to the
English and is recorded (`i18n.missing()`), so a forgotten translation never
crashes — it fails a test instead.

```python
from core.i18n import tr

lbl.setText(tr("Budget used: {used} of {total}", used=n, total=budget))
```

Rules that keep this working:

- **Never call `tr()` at import time** — no module constants, class attributes
  or default arguments. The language is chosen after the settings are read, and
  the window is rebuilt when it changes. Turn the constant into a function.
- **No f-strings as keys.** Use `{field}` placeholders and pass keyword
  arguments; the Korean text reorders them freely.
- A literal that is *looked up later* (`tr(variable)`) is marked `# i18n: key`
  on its line so the scanner counts it as a key; developer-only text (log
  markers, object names, file names) is marked `# i18n: skip`.
- `core/` stays GUI-free: `i18n.py` imports nothing from Qt, and the language
  choice (`default_language`) is `SEQOPT_LANG` → saved setting → OS locale.
- Figures and PDFs are translated too; `core/plotstyle.py` and `core/fonts.py`
  pick a CJK font when the text needs one (Helvetica fallback otherwise).

What enforces it — three tests, all red on a plain string:

| test | fails when |
|---|---|
| `tests/test_i18n.py` (scanner `tests/i18n_scan.py`) | a user-visible literal is not wrapped in `tr()`; a key has no Korean; a Korean entry is stale; placeholders disagree; a "translation" is still English; a private-lab token leaks in |
| `tests/test_layout.py` (`tests/clipcheck.py`) | any label, button, tab, column header, figure title or table is cut off — every tab of every bundled example, **en × ko × 1024×660 × 1366×768** |
| CI `windows-build` | the shipped exe is captured on a real Windows display in both languages (`seqopt-windows-shots/en`, `/ko`), 19 screens each |

Adding a string therefore means: write it in English inside `tr()`, add the
Korean line to the area's `ko_*.py`, and run the two tests. Adding a language
means one more `core/lang/<code>_*.py` set and one entry in `LANGUAGES`.
