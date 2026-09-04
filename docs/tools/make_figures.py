# -*- coding: utf-8 -*-
"""Figures for the explainer page — produced by the program's own code.

    .venv/bin/python docs/tools/make_figures.py

Every number drawn here comes from core/diagnostics.py, not from a drawing
made to look convincing. Two pairs, each showing the same check passing and
failing, because the page's whole point is that the failing case is real.

Text inside the figures stays minimal and symbolic (σ, R²) so one image
serves both the Korean and English versions of the page.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib                                                    # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                      # noqa: E402

from core.diagnostics import discriminability, loocv_r2              # noqa: E402
from core.plotstyle import (C_AXIS, C_BEST, C_MEAN, C_POINT, C_RAW,  # noqa: E402
                            apply_style)

OUT = Path(__file__).resolve().parent.parent / "figures"
SEED = 7


def learnability_pair():
    """Left: the surrogate learns the shape. Right: it cannot, and R² goes negative."""
    rng = np.random.default_rng(SEED)
    n = 16
    XN = np.sort(rng.random((n, 1)), axis=0)

    smooth = np.sin(4.2 * XN[:, 0]) + 0.6 * XN[:, 0] + rng.normal(0, 0.03, n)
    noisy = rng.normal(0, 0.35, n)          # no structure at all: pure scatter

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.5))
    for ax, y, title in ((axes[0], smooth, "learnable"),
                         (axes[1], noisy, "not learnable")):
        r = loocv_r2(XN, y)
        ax.scatter(y, r.pred, s=42, c=C_POINT, edgecolors="white",
                   linewidths=0.8, zorder=5)
        lim = [min(y.min(), r.pred.min()), max(y.max(), r.pred.max())]
        pad = 0.08 * (lim[1] - lim[0])
        lim = [lim[0] - pad, lim[1] + pad]
        ax.plot(lim, lim, color=C_AXIS, lw=1.2, zorder=3)
        ax.axhline(y.mean(), color=C_BEST, ls="--", lw=1.4, zorder=4)
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.set_xlabel("measured")
        ax.set_ylabel("predicted (leave-one-out)")
        ax.set_title(f"{title}      R² = {r.r2:+.2f}",
                     color=("#1a7f37" if r.r2 > 0 else "#cf222e"))
        print(f"  learnability/{title}: R² = {r.r2:+.3f}")
    fig.tight_layout()
    fig.savefig(OUT / "learnability.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def discriminability_pair():
    """Left: condition differences clear the wobble. Right: they drown in it."""
    rng = np.random.default_rng(8)
    k, reps_each = 9, 4
    means = np.linspace(0.0, 1.0, k)

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.5))
    for ax, noise, title in ((axes[0], 0.06, "distinguishable"),
                             (axes[1], 0.90, "drowned in noise")):
        rng = np.random.default_rng(8)          # same draw both panels: only the noise differs
        reps = [means[i] + rng.normal(0, noise, reps_each) for i in range(k)]
        d = discriminability(reps)
        for i, v in enumerate(reps):
            ax.scatter([i] * len(v), v, s=26, c=C_RAW, zorder=3)
        ax.plot(range(k), [v.mean() for v in reps], color=C_MEAN, lw=1.8,
                marker="o", ms=5, zorder=4)
        ax.set_xlabel("condition")
        ax.set_ylabel("measured value")
        ax.set_xticks(range(k))
        ax.set_xticklabels([])
        ax.set_title(f"{title}      D = {d.D[1]:.1f}",
                     color=("#1a7f37" if d.D[1] > 1 else "#cf222e"))
        print(f"  discriminability/{title}: D = {d.D[1]:.2f} "
              f"(σb={d.sigma_b:.3f}, σw={d.sigma_w:.3f})")
    fig.tight_layout()
    fig.savefig(OUT / "discriminability.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    apply_style()
    plt.rcParams.update({"axes.grid": True, "axes.titlesize": 11,
                         "axes.titleweight": "bold"})
    learnability_pair()
    discriminability_pair()
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name:24s} {p.stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
