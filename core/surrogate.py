# -*- coding: utf-8 -*-
"""Surrogate model — tells you the value, and the uncertainty, where you have not measured.

**The default kernel is fixed** (SPEC_AMENDMENTS A1). It is the one combination
that reproduces the §9-1 regression expectations from the validation study.

The registry does **not** mean the kernel is free to edit. If you need a new
model, **add a new class** with `@SURROGATES.register("name")` and leave the
existing one alone. Using two definitions for the same metric is the failure
this project ran into four times before it started (handover §4-4).
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

from .protocols import Surrogate
from .registry import Registry

SURROGATES: Registry[Surrogate] = Registry("surrogate")
DEFAULT_SURROGATE = "gp-matern-ard"

# Constants of the fixed kernel — change these and the §9-1 regression tests
# break. That is the intended tripwire.
LENGTH_SCALE_INIT = 0.4
LENGTH_SCALE_BOUNDS = (1e-2, 1e2)
NOISE_INIT = 0.01
NOISE_BOUNDS = (1e-6, 1e2)
RANDOM_STATE = 0          # restarts>0, so removing this makes the regression tests non-deterministic


@SURROGATES.register(DEFAULT_SURROGATE)
class GaussianProcessSurrogate:
    """ARD Matern(nu=2.5) + WhiteKernel Gaussian process.

    It learns **condition means** (SPEC_AMENDMENTS A3). The noise magnitude that
    replicates reveal is used by discriminability D (gate ③); here the
    WhiteKernel absorbs it.
    """

    label = "Gaussian process (Matern · ARD)"        # i18n: key — translated where shown (recommend(): tr(label_of(...)))

    def __init__(self, n_restarts: int = 2):
        self.n_restarts = n_restarts
        self._model: GaussianProcessRegressor | None = None

    @staticmethod
    def _kernel(dim: int):
        return (ConstantKernel(1.0, (1e-3, 1e3))
                * Matern(np.ones(dim) * LENGTH_SCALE_INIT, LENGTH_SCALE_BOUNDS, nu=2.5)
                + WhiteKernel(NOISE_INIT, NOISE_BOUNDS))

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GaussianProcessSurrogate":
        self._model = GaussianProcessRegressor(
            kernel=self._kernel(X.shape[1]), normalize_y=True,
            n_restarts_optimizer=self.n_restarts, random_state=RANDOM_STATE).fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        mean, std = self._raw.predict(X, return_std=True)
        return mean, std

    def sample(self, X: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        """Draw one function from the posterior — by Cholesky.

        sklearn's `sample_y` goes through numpy `multivariate_normal` (SVD),
        which took 8 s per draw on a 4000-point candidate pool and made a
        Thompson recommendation look hung (docs/GLOBAL_SEARCH.md, "Thompson
        speed-up"). Same distribution, drawn by Cholesky, 40× faster. If the
        covariance is numerically singular, add a little to the diagonal and
        retry; if that still fails, fall back to the original path.
        """
        mean, cov = self._raw.predict(X, return_cov=True)
        scale = max(float(np.mean(np.diag(cov))), 1e-12)
        diag = np.diag_indices_from(cov)
        added = 0.0
        for jitter in (0.0, 1e-10, 1e-8, 1e-6):
            cov[diag] += jitter * scale - added          # a 4000×4000 copy is 128 MB — work in place
            added = jitter * scale
            try:
                L = np.linalg.cholesky(cov)
            except np.linalg.LinAlgError:
                continue
            return mean + L @ rng.standard_normal(len(mean))
        seed = int(rng.integers(2 ** 31))
        return self._raw.sample_y(X, n_samples=1, random_state=seed)[:, 0]

    def length_scales(self) -> np.ndarray | None:
        for part in self._raw.kernel_.get_params().values():
            ls = getattr(part, "length_scale", None)
            if ls is not None:
                return np.atleast_1d(np.asarray(ls, dtype=float))
        return None

    @property
    def _raw(self) -> GaussianProcessRegressor:
        if self._model is None:
            raise RuntimeError("Not fitted yet — call fit() first")      # i18n: skip
        return self._model


@SURROGATES.register("random-forest")
class RandomForestSurrogate:
    """Tree ensemble. Uncertainty comes from the spread across trees.

    **Not the default.** It is here for comparison when the response surface is
    step-like or interactions are severe. It has no length scales, so the
    sensitivity view (F-33) is not shown — and the screen says so plainly.
    """

    label = "Random forest (for comparison)"         # i18n: key

    def __init__(self, n_estimators: int = 300):
        self.n_estimators = n_estimators
        self._model: RandomForestRegressor | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomForestSurrogate":
        self._model = RandomForestRegressor(
            n_estimators=self.n_estimators, random_state=RANDOM_STATE).fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        assert self._model is not None
        per_tree = np.stack([t.predict(X) for t in self._model.estimators_])
        return per_tree.mean(axis=0), per_tree.std(axis=0)

    def sample(self, X: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        assert self._model is not None
        tree = self._model.estimators_[int(rng.integers(len(self._model.estimators_)))]
        return tree.predict(X)

    def length_scales(self) -> np.ndarray | None:
        return None


# ══════════════════════════════════════════════════════════════════════
# Short names — the entry points existing call sites use
# ══════════════════════════════════════════════════════════════════════
def make_surrogate(name: str = DEFAULT_SURROGATE, **kwargs) -> Surrogate:
    return SURROGATES.create(name, **kwargs)


def fit(X: np.ndarray, y: np.ndarray, name: str = DEFAULT_SURROGATE, **kwargs) -> Surrogate:
    """One fitted surrogate. With no name given, the fixed default model is used."""
    return make_surrogate(name, **kwargs).fit(X, y)
