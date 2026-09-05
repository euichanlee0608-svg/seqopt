# -*- coding: utf-8 -*-
"""Diagnostics — the evidence behind the gate verdict (spec §5-3 ~ §5-6, F-11 ~ F-17).

The values in this module decide whether the recommendation feature is locked.
**Every number is returned together with its worked calculation table**
(principle P4, traceability) — the screen has to be able to unfold it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.model_selection import LeaveOneOut

from .protocols import Surrogate
from .surrogate import LENGTH_SCALE_BOUNDS, fit

BOOTSTRAP_DRAWS = 4000
BOOTSTRAP_SEED = 0
D_THRESHOLD = 1.0
NUGGET_THRESHOLD = 0.3

# ── Discriminability reference marks and their basis ─────────────────
# The gate is 1.0 alone (spec F-12). The other two are not gates but
# **marks a newcomer can aim for.**
#   1.0  gate        : between-condition difference (σb) equals the measurement
#                      wobble (σw). Below this, differences drown in noise.
#   2.0  recommended : two condition means about two standard errors apart —
#                      the usual boundary for calling things "different"
#                      (95%, z≈1.96).
#   3.5  comfortable : matches the AIAG MSA requirement of ndc = 1.41·σb/σw ≥ 5
#                      distinct categories (σb/σw ≥ 3.5) — the measurement
#                      system can split condition differences into five steps.
D_RECOMMENDED = 2.0
D_COMFORTABLE = 3.5
D_LEVELS = [
    (D_THRESHOLD, "Gate (minimum)", "difference = wobble",
     "Follows from the definition of D. With σb < σw, condition differences are smaller than replicate wobble"),
    (D_RECOMMENDED, "Recommended", "difference ≈ wobble × 2",
     "Two means about two standard errors apart — the usual boundary for 'different' (95%, z≈1.96)"),
    (D_COMFORTABLE, "Comfortable", "difference ≈ wobble × 3.5",
     "Matches the AIAG MSA distinct-category requirement ndc = 1.41·σb/σw ≥ 5"),
]

# Nugget-ratio scale (geostatistics, Cambardella et al. 1994) — a reference
# scale, separate from this tool's own gate (0.3)
NUGGET_CLASSES = [(0.25, "strong structure"), (0.75, "moderate"), (float("inf"), "weak structure")]


# ══════════════════════════════════════════════════════════════════════
# Discriminability (§5-3 · F-11 · F-12 · F-13)
# ══════════════════════════════════════════════════════════════════════
@dataclass
class DiscResult:
    sigma_w: float | None
    sigma_b: float
    D: dict[int, float]                      # discriminability by replicate count n
    ci_lo: float | None
    ci_hi: float | None
    n_median: float
    top_condition: int | None                # index of the condition dominating within-condition variance
    top_share: float | None                  # its share [%]
    sigma_w_drop_top: float | None
    sigma_b_drop_top: float | None
    D_drop_top: float | None
    table: list[dict] = field(default_factory=list)   # per-condition n · mean · SD · (n-1)var
    total_ss: float = 0.0
    total_df: int = 0

    @property
    def verdict(self) -> str:
        """When the interval straddles the threshold, the verdict is UNDECIDED (principle P5).
        A point estimate alone never earns a pass or a fail."""
        if self.sigma_w is None:
            return "UNCOMPUTABLE"            # no replicates at all → we do not substitute an assumed value
        if self.ci_lo is None:
            return "UNDECIDED"
        if self.ci_lo > D_THRESHOLD:
            return "OK"
        if self.ci_hi < D_THRESHOLD:
            return "FAIL"
        return "UNDECIDED"


def discriminability(reps: list[np.ndarray], ns: tuple[int, ...] = (1, 2, 3, 4, 5, 6)) -> DiscResult:
    """σw · σb · D(n) · bootstrap interval · dominating condition.

        σw = sqrt( Σ_c (n_c−1)·var(y_c) / Σ_c (n_c−1) )      # conditions with ≥2 replicates only
        σb = std( {mean(y_c)}_c , ddof=1 )
        D(n) = σb / (σw / √n)
    """
    means = np.array([v.mean() for v in reps])
    sigma_b = float(means.std(ddof=1))

    table = []
    for i, v in enumerate(reps):
        n = len(v)
        contrib = float((n - 1) * v.var(ddof=1)) if n > 1 else 0.0
        table.append(dict(index=i, n=n, mean=float(v.mean()),
                          sd=float(v.std(ddof=1)) if n > 1 else None,
                          ss=contrib))

    multi = [(i, v) for i, v in enumerate(reps) if len(v) > 1]
    n_median = float(np.median([len(v) for v in reps]))

    if not multi:
        # Without replicates, σw cannot be computed. Never substitute an
        # assumed value (§10 risk table).
        return DiscResult(None, sigma_b, {}, None, None, n_median,
                          None, None, None, None, None, table, 0.0, 0)

    total_ss = float(sum((len(v) - 1) * v.var(ddof=1) for _, v in multi))
    total_df = int(sum(len(v) - 1 for _, v in multi))
    sigma_w = float(np.sqrt(total_ss / total_df))
    D = {n: sigma_b / (sigma_w / np.sqrt(n)) for n in ns}

    # Dominating condition (F-13) — how much of the within-condition variance
    # one single condition carries
    top_i, top_v = max(multi, key=lambda kv: (len(kv[1]) - 1) * kv[1].var(ddof=1))
    top_ss = float((len(top_v) - 1) * top_v.var(ddof=1))
    ss2 = total_ss - top_ss
    df2 = total_df - (len(top_v) - 1)
    sw2 = float(np.sqrt(ss2 / df2)) if df2 > 0 else None
    m2 = np.array([v.mean() for i, v in enumerate(reps) if i != top_i])
    sb2 = float(m2.std(ddof=1)) if len(m2) > 1 else None

    ci_lo, ci_hi = _bootstrap_ci(reps)

    return DiscResult(
        sigma_w=sigma_w, sigma_b=sigma_b, D=D, ci_lo=ci_lo, ci_hi=ci_hi,
        n_median=n_median, top_condition=top_i, top_share=top_ss / total_ss * 100,
        sigma_w_drop_top=sw2, sigma_b_drop_top=sb2,
        D_drop_top=(sb2 / sw2) if (sw2 and sb2) else None,
        table=table, total_ss=total_ss, total_df=total_df,
    )


def _bootstrap_ci(reps: list[np.ndarray]) -> tuple[float | None, float | None]:
    """Resample conditions with replacement, recompute D(n=1), take the 2.5/97.5 percentiles (F-12).

    A resample with fewer than 3 replicated conditions, or a zero variance sum,
    is discarded (it would send σw to 0 and D to infinity).
    """
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n_cond = len(reps)
    draws = []
    for _ in range(BOOTSTRAP_DRAWS):
        idx = rng.integers(0, n_cond, n_cond)
        sample = [reps[i] for i in idx]
        m = np.array([v.mean() for v in sample])
        multi = [v for v in sample if len(v) > 1]
        if len(multi) < 3:
            continue
        ss = sum((len(v) - 1) * v.var(ddof=1) for v in multi)
        df = sum(len(v) - 1 for v in multi)
        if df == 0 or ss == 0:
            continue
        draws.append(m.std(ddof=1) / np.sqrt(ss / df))
    if not draws:
        return None, None
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return float(lo), float(hi)


def required_reps(sigma_b: float, sigma_w: float, target_D: float) -> int:
    """Replicates needed for a target discriminability (F-16). Solves D(n)=σb/(σw/√n) for n."""
    if sigma_b <= 0:
        raise ValueError("σb is ≤ 0 — there is no between-condition difference")
    n = (target_D * sigma_w / sigma_b) ** 2
    return max(1, int(np.ceil(n)))


def replicate_plan(sigma_b: float, sigma_w: float, rep_counts: list[int],
                   targets: tuple[float, ...] = (D_THRESHOLD, D_RECOMMENDED, D_COMFORTABLE)
                   ) -> list[dict]:
    """For each target D: replicates per condition n · extra measurements · resulting D.

    A projection **assuming σw stays what it is now.** More replicates change
    the σw estimate itself, so the screen always states that assumption.
    """
    rows = []
    for t in targets:
        n = required_reps(sigma_b, sigma_w, t)
        extra = sum(max(0, n - c) for c in rep_counts)
        rows.append({"target": t, "n": n, "extra": extra,
                     "D": sigma_b / (sigma_w / np.sqrt(n))})
    return rows


# ══════════════════════════════════════════════════════════════════════
# Surface learnability (§5-4 · F-14)
# ══════════════════════════════════════════════════════════════════════
@dataclass
class LoocvResult:
    r2: float
    ss_res: float
    ss_tot: float
    pred: np.ndarray
    low_sample_warning: bool


def loocv_r2(XN: np.ndarray, y: np.ndarray) -> LoocvResult:
    """Leave one condition out, **refit** the GP on the rest, predict it.

    ⚠ Do not replace this with closed-form LOO (fixed hyperparameters) —
       SPEC_AMENDMENTS A2. On real lab data it flipped R² from −0.272 to
       +0.228, reversing the gate verdict. Yes it is slow; that is why it
       runs in the background.
    """
    pred = np.zeros_like(y, dtype=float)
    for tr, te in LeaveOneOut().split(XN):
        pred[te] = fit(XN[tr], y[tr]).predict(XN[te])[0]
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return LoocvResult(r2=1 - ss_res / ss_tot, ss_res=ss_res, ss_tot=ss_tot,
                       pred=pred, low_sample_warning=len(y) < 8)


# ══════════════════════════════════════════════════════════════════════
# Nugget ratio — surface roughness (§5-5 · F-15)
# ══════════════════════════════════════════════════════════════════════
@dataclass
class NuggetResult:
    nugget: float
    sill: float
    ratio: float
    noise_share: float | None
    bin_centers: np.ndarray
    bin_gamma: np.ndarray
    bin_count: np.ndarray

    @property
    def rough(self) -> bool:
        return self.ratio > NUGGET_THRESHOLD


def nugget_ratio(XN: np.ndarray, y: np.ndarray, bins: int = 12,
                 sigma_w: float | None = None, min_pairs: int = 8) -> NuggetResult | None:
    """Measure terrain roughness with a semivariogram. Too few pairs → **None** (not computable).

    With few conditions, each distance bin holds only a handful of pairs and the
    semivariogram loses its meaning (4 conditions give just 6 pairs). Forcing a
    value there would be inventing "rough/smooth" — the same reason σw is never
    computed without replicates.

        h_ij = ‖x_i − x_j‖ / max(h),  γ_ij = (y_i − y_j)² / 2
        bin-averaged γ normalized by variance → nugget = first bin, sill = median of the bins with h>0.45
    """
    n = len(y)
    ii, jj = np.triu_indices(n, 1)
    d = np.linalg.norm(XN[ii] - XN[jj], axis=1)
    d = d / d.max()
    dy = (y[ii] - y[jj]) ** 2
    sy = float(y.std(ddof=1))

    edges = np.linspace(0, 1, bins + 1)
    gm, cnt, ctr = [], [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (d >= a) & (d < b)
        if m.sum() >= min_pairs:
            gm.append(0.5 * dy[m].mean() / sy ** 2)
            cnt.append(int(m.sum()))
            ctr.append((a + b) / 2)
    if not gm:
        return None
    gm, ctr, cnt = np.array(gm), np.array(ctr), np.array(cnt)

    far = ctr > 0.45
    sill = float(np.median(gm[far])) if far.any() else float(gm[-1])
    nugget = float(gm[0])
    noise = float(sigma_w ** 2 / sy ** 2) if sigma_w is not None else None

    return NuggetResult(nugget=nugget, sill=sill, ratio=nugget / sill,
                        noise_share=noise, bin_centers=ctr, bin_gamma=gm, bin_count=cnt)


# ══════════════════════════════════════════════════════════════════════
# Sensitivity (§5-6 · F-33)
# ══════════════════════════════════════════════════════════════════════
def sensitivity(model: Surrogate, names: list[str]) -> list[tuple[str, float]]:
    """ARD length scales → normalized 1/ℓ percentages.

    A length scale is **more sensitive the smaller it is**, so the screen draws
    the inverse (1/ℓ). An axis stuck at the upper bound scores 0. The transform
    matches the direction of a parameter-study bar chart; raw ℓ shows only in
    the tooltip.
    """
    ls = model.length_scales()
    if ls is None:
        # A model without length scales (random forest etc.) yields no
        # sensitivity. We do not invent zeros.
        return []
    hi = LENGTH_SCALE_BOUNDS[1]
    inv = np.where(ls >= hi * 0.999, 0.0, 1.0 / ls)
    total = inv.sum()
    pct = inv / total * 100 if total > 0 else np.zeros_like(inv)
    return list(zip(names, [float(v) for v in pct]))


# ══════════════════════════════════════════════════════════════════════
# Gate verdict table (§12-1 · F-17)
# ══════════════════════════════════════════════════════════════════════
@dataclass
class Gate:
    cond_count: str = "OK"
    learnable: str = "OK"
    discrim: str = "OK"
    replicates: str = "OK"
    locked: bool = False
    reasons: list[str] = field(default_factory=list)


def gate(n_candidates: int | None, budget: int, r2: float | None, disc: DiscResult,
         frac_with_reps: float) -> Gate:
    """The gate verdict. Any FAIL locks the recommendation (F-20) — principle P1.

    n_candidates is **the number of conditions that can be chosen in the design
    space** (`core.spec.count_candidates`). None means infinite (a continuous
    variable without a step) and passes ①. Never pass the number of conditions
    already measured — every new project would lock, with the wrong advice that
    "measuring everything is better" (SPEC_AMENDMENTS A6).

    r2=None means "still computing", and the lock **stays on** — it never opens
    optimistically.
    """
    g = Gate()

    # ① Candidate count. Choosing only makes sense when there are more selectable conditions than budget
    g.cond_count = "OK" if n_candidates is None or n_candidates > budget else "FAIL"
    if g.cond_count == "FAIL":
        g.reasons.append(f"Selectable conditions {n_candidates} ≤ budget {budget} runs → "
                         f"measuring everything is better")

    # ② Learnability
    if r2 is None:
        g.learnable = "PENDING"
        g.reasons.append("Learnability R² still computing")
    else:
        g.learnable = "OK" if r2 > 0 else "FAIL"
        if g.learnable == "FAIL":
            g.reasons.append(
                f"Learnability R² = {r2:+.3f} ≤ 0 → worse than always answering the overall mean")

    # ③ Discriminability
    g.discrim = disc.verdict
    if g.discrim == "FAIL":
        g.reasons.append(
            f"Discriminability interval upper bound {disc.ci_hi:.2f} < 1.0 → conditions cannot be told apart")
    elif g.discrim == "UNDECIDED":
        g.reasons.append("The discriminability interval straddles 1.0 → undecided")
    elif g.discrim == "UNCOMPUTABLE":
        g.reasons.append("No replicate measurements, so discriminability cannot be computed")

    # ④ Replicates
    g.replicates = "OK" if frac_with_reps >= 0.5 else "WARN"

    g.locked = (g.learnable != "OK") or (g.cond_count == "FAIL") or (g.discrim != "OK")
    return g
