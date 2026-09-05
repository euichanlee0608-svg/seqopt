# Global search — why the screen still offers only EI · UCB · Thompson

> The worry: expected improvement (EI) could settle on a local peak and never look at the
> rest of the space. Four global-search acquisition strategies were benchmarked against the
> three that ship. None earned a place on screen. This document records the rule, the
> candidates, the numbers, and how to re-run the check.

Baseline: `docs/bench_global.json` (2026-09-05), produced by `packaging/bench_global.py`.
The numbers the help tab quotes come from one place, `core/acquisition.py: BENCH_CLAIMS`, and
`tests/test_global.py` checks them against the JSON.

## The rule — fixed before measuring

*A strategy goes on screen only if it beats EI on the multimodal functions without losing
on the unimodal ones.* Concretely: multimodal mean hit rate higher than EI's, and
unimodal/rugged mean hit rate no more than 10 points below EI's. Set first, measured
second, so the result could not be argued into the menu afterwards.

## What was compared

| Name in the JSON | Strategy | Where it lives |
|---|---|---|
| `EI` | Expected improvement (the default) | `core/acquisition.py` |
| `UCB2` | Upper confidence bound, b = 2 | `core/acquisition.py` |
| `TS` | Thompson sampling | `core/acquisition.py` |
| `MES` | Max-value entropy search (Wang & Jegelka, ICML 2017) — f* sampled through a Gumbel fit of the posterior maximum over the candidate grid, 16 samples | `packaging/bench_global.py` |
| `MIX4` | EI with periodic pure exploration — every 4th recommendation goes to the point of maximum σ (a deterministic ε-greedy, after De Ath et al., ACM TELO 2021) | `packaging/bench_global.py` |
| `MIX4-TS` | The same mixing, with a Thompson draw instead of max σ on the exploration turn | `packaging/bench_global.py` |
| `GPUCB` | GP-UCB with the β_t schedule of Srinivas et al. (ICML 2010), scaled by 1/5 as in the paper | `packaging/bench_global.py` |

The candidates run through the **real recommendation path** — `core.recommend.recommend()`,
not a separate loop. The one addition that makes this possible is the `prepare()` hook in
`core/acquisition.py`: called once per recommendation before any scoring, so a stateful
candidate (MES's f* samples, MIX4's "is this an exploration turn") settles its state there
instead of inside `score()`, which the maximizer calls thousands of times. The three shipped
acquisitions are stateless and pass straight through it.

## Design

- Budget 40 runs = 11 initial points (maximin LHS) + 29 sequential recommendations.
- Observation noise: Gaussian, σ = 3% of the function's value range.
- After the budget: take the condition whose **observed** value was best (principle P3),
  and score its **true** value: `regret = (global max − true value) / range`;
  `hit = regret < 5%`. 10 seeds per function and strategy.
- Test functions, all rescaled to [0,1]^d and maximized. A first round used only the four
  2–3-D functions plus the two unimodal/rugged ones; on Branin, six-hump camel and
  Hartmann-3 every strategy scored 100% — a ceiling, nothing to separate — so Hartmann-6
  and Levy-4 were added. The original functions and the rule stayed as they were.

| Function | d | Kind | Note |
|---|---|---|---|
| branin | 2 | multimodal | 3 global optima, wide valley |
| camel6 | 2 | multimodal | 4 local + 2 global |
| hartmann3 | 3 | multimodal | 4 local, 1 global |
| twopeak | 2 | multimodal | broad low peak + narrow high peak (deceptive) |
| hartmann6 | 6 | multimodal | 6 local, 1 global — a device with many variables |
| levy4 | 4 | multimodal | many local + wide funnel |
| rosen2 | 2 | unimodal | curved valley — checks there is no loss |
| ackley2 | 2 | rugged | so fine the GP reads it as noise |

## Results — hit rate % / median regret %

| Function | EI | UCB2 | TS | MES | MIX4 | MIX4-TS | GPUCB |
|---|---|---|---|---|---|---|---|
| branin | 100/0.5 | 100/0.4 | 100/0.4 | 100/0.5 | 100/0.6 | 100/0.7 | 100/0.7 |
| camel6 | 100/0.7 | 90/0.6 | 90/1.1 | 100/0.3 | 100/0.5 | 100/0.7 | 100/0.8 |
| hartmann3 | 100/0.7 | 100/0.9 | 90/1.2 | 100/0.4 | 90/0.8 | 100/0.4 | 90/0.6 |
| twopeak | 40/40.4 | 40/40.5 | 40/40.4 | 40/40.5 | 40/40.3 | 40/40.4 | 40/40.4 |
| hartmann6 | 10/17.5 | 0/16.2 | 0/24.6 | 0/27.3 | 0/18.0 | 0/16.0 | 0/13.5 |
| levy4 | 80/2.7 | 40/5.3 | 90/3.3 | 80/3.0 | 80/2.4 | 70/3.2 | 60/4.5 |
| rosen2 | 100/0.2 | 100/0.2 | 100/0.2 | 100/0.2 | 100/0.1 | 100/0.4 | 100/0.2 |
| ackley2 | 40/8.0 | 50/5.1 | 50/5.2 | 30/5.8 | 50/4.8 | 40/5.7 | 70/3.7 |
| **multimodal mean (6)** | **71.7** | 61.7 | 68.3 | 70.0 | 68.3 | 68.3 | 65.0 |
| unimodal/rugged mean (2) | 70.0 | 75.0 | 75.0 | 65.0 | 75.0 | 70.0 | 85.0 |

## Reading the table

- **No candidate beat EI on the multimodal set.** The best, MES at 70.0, is below EI's 71.7.
  TS scores 90 vs 80 on Levy-4, but that is one seed, and TS loses on Hartmann-6 and the
  camel. By the rule, nothing was promoted. The candidate code stays in
  `packaging/bench_global.py` only — no unvalidated path goes into `core/`.
- **Two-peak (the needle)** is 40% for everyone. The narrow high peak covers roughly 1% of
  the domain; only seeds whose initial design dropped a point into it find it, and 40% is
  that fraction of seeds. The initial design and the budget decide this, not the acquisition.
- **Hartmann-6** is found by nobody within 40 runs (EI 10%, the rest 0). Six variables and
  40 runs do not work with any acquisition — this is the basis for the help tab's advice
  that with six or more variables the budget comes first.
- On the unimodal/rugged pair GP-UCB (85) is above EI (70), but it failed the first condition
  (multimodal), and the gain comes from a single function (Ackley).
- **GA · PSO · CMA-ES were not candidates in the first place.** Population methods evaluate
  dozens of points per generation; with a 40-run budget that is one or two generations —
  in effect random search. This tool's global reach comes from two other things:
  ① the space-filling initial design, and ② multi-start maximization of the acquisition
  (the top 20 of 2000 LHS points, each polished with L-BFGS-B).

## The inner maximizer is not the weak link

A separate check, in case the acquisition maximization itself were getting stuck. At
8 functions × 3 seeds × 3 points in time (15, 25, 35 training points) = 72 cases, the
multi-start L-BFGS-B maximum of EI was compared with scipy's `differential_evolution` on
the same model. At a relative tolerance of 1e-3, multi-start was equal or higher in
**72/72**. With a tolerance of 1e-6, four Hartmann-6 cases were flagged, with relative gaps
between 2e-6 and 1.2e-4 — finishing differences of the local polish, not a different peak —
so the tolerance was set to 1e-3 (`INNER_TOL`). `tests/test_global.py` re-checks every row
of the JSON against that tolerance.

## Thompson speed-up (found while running the bench)

A single Thompson recommendation took 8 s (50 s under load). sklearn's `sample_y` draws
through numpy's `multivariate_normal`, which factorizes the covariance by **SVD** — a
4000 × 4000 SVD for the candidate pool. `GaussianProcessSurrogate.sample` in
`core/surrogate.py` now draws from the same posterior by **Cholesky**: 0.3 s. If the
covariance is numerically singular it adds a small jitter to the diagonal (in place — a
4000 × 4000 copy is 128 MB) and retries; if that still fails it falls back to `sample_y`.
The kernel is untouched. `tests/test_surrogate.py` checks that the draws have the same
pointwise mean and standard deviation as `predict()`, and that one draw over 4000 points
stays under 5 s.

## Re-running the baseline

```
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python packaging/bench_global.py                 # full run → docs/bench_global.json
.venv/bin/python packaging/bench_global.py --quick           # 1 function · 2 seeds, a smoke test
.venv/bin/python packaging/bench_global.py --inner-only      # redo only the inner-maximizer check
```

- The thread caps matter. numpy on macOS uses Accelerate, which `threadpoolctl` cannot see;
  with 8 workers fighting over threads a single Thompson run stretched to 1200 s.
- Each worker takes 1–1.5 GB; 8 workers swap on a 16 GB Mac mini. The full run took
  4133 s (about 70 minutes) with 8 workers there.
- The JSON is a **baseline**: never hand-edited, never refreshed automatically. Re-run it
  when the budget, the noise, the functions or a strategy change, and commit the new file
  with the reason.
- If a re-run shows a candidate beating EI under the rule,
  `tests/test_global.py::test_only_strategies_that_beat_ei_on_multimodal_are_on_screen`
  fails. That failure is the trigger to promote it: register the class in
  `core/acquisition.py`, update `BENCH_CLAIMS`, and extend `SHIPPED` in the test.
