# -*- coding: utf-8 -*-
"""Reference values for docs/gp.js, produced by scikit-learn.

    .venv/bin/python docs/tools/make_gp_fixture.py

The page's Gaussian process runs with fixed hyperparameters, so the reference
fixes them too (optimizer=None) and the comparison is exact rather than
approximate. Checked by docs/tools/check_gp.js.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel

ELL, NOISE = 0.15, 0.01
HERE = Path(__file__).resolve().parent

X = np.array([0.05, 0.22, 0.41, 0.58, 0.73, 0.94]).reshape(-1, 1)
Y = np.array([0.31, 0.85, 0.62, 1.42, 1.10, 0.28])
GRID = np.linspace(0.0, 1.0, 50).reshape(-1, 1)

kernel = Matern(length_scale=ELL, nu=2.5) + WhiteKernel(noise_level=NOISE,
                                                        noise_level_bounds="fixed")
gp = GaussianProcessRegressor(kernel=kernel, optimizer=None,
                              normalize_y=True, alpha=0.0).fit(X, Y)
mean, std = gp.predict(GRID, return_std=True)

out = {
    "ell": ELL, "noise": NOISE,
    "xs": X.ravel().tolist(), "ys": Y.tolist(),
    "grid": GRID.ravel().tolist(),
    "mean": mean.tolist(), "std": std.tolist(),
}
(HERE / "gp_fixture.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(f"wrote gp_fixture.json  mean[0]={mean[0]:.6f}  std[0]={std[0]:.6f}")
