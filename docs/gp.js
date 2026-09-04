/* Gaussian process + expected improvement, small enough to read.
 *
 * This is the same math the desktop program runs, with one difference: the
 * hyperparameters are fixed here instead of being fitted. Fitting them needs an
 * optimizer, and a teaching page does not need one — but it does need to be
 * right, so the fixed-hyperparameter path is checked numerically against
 * scikit-learn (tools/make_gp_fixture.py → tools/check_gp.js).
 *
 * Kernel: Matern 5/2 + white noise, on inputs normalized to [0, 1].
 *   k(r) = (1 + √5·r/ℓ + 5r²/3ℓ²) · exp(−√5·r/ℓ)
 */
(function (root) {
  "use strict";

  var SQRT5 = Math.sqrt(5);

  function matern52(a, b, ell) {
    var r = Math.abs(a - b) / ell;
    return (1 + SQRT5 * r + (5 / 3) * r * r) * Math.exp(-SQRT5 * r);
  }

  /* Cholesky, lower triangular. The jitter keeps a near-singular matrix
     (two measurements at almost the same place) from stopping the page. */
  function cholesky(A, n) {
    var L = [], i, j, k, s;
    for (i = 0; i < n; i++) L.push(new Float64Array(n));
    for (i = 0; i < n; i++) {
      for (j = 0; j <= i; j++) {
        s = A[i][j];
        for (k = 0; k < j; k++) s -= L[i][k] * L[j][k];
        if (i === j) L[i][i] = Math.sqrt(Math.max(s, 1e-12));
        else L[i][j] = s / L[j][j];
      }
    }
    return L;
  }

  function forwardSolve(L, b, n) {          // L·x = b
    var x = new Float64Array(n), i, k, s;
    for (i = 0; i < n; i++) {
      s = b[i];
      for (k = 0; k < i; k++) s -= L[i][k] * x[k];
      x[i] = s / L[i][i];
    }
    return x;
  }

  function backSolve(L, b, n) {             // Lᵀ·x = b
    var x = new Float64Array(n), i, k, s;
    for (i = n - 1; i >= 0; i--) {
      s = b[i];
      for (k = i + 1; k < n; k++) s -= L[k][i] * x[k];
      x[i] = s / L[i][i];
    }
    return x;
  }

  /* Fit on measured points. xs and ys are plain arrays of the same length.
     ys is standardized internally, the way the desktop program normalizes y. */
  function fit(xs, ys, opts) {
    opts = opts || {};
    var ell = opts.ell === undefined ? 0.15 : opts.ell;
    var noise = opts.noise === undefined ? 0.01 : opts.noise;
    var standardize = opts.standardize !== false;
    var n = xs.length, i, j;

    var mu = 0, sd = 1;
    if (standardize && n > 0) {
      for (i = 0; i < n; i++) mu += ys[i];
      mu /= n;
      var v = 0;
      for (i = 0; i < n; i++) v += (ys[i] - mu) * (ys[i] - mu);
      sd = n > 1 ? Math.sqrt(v / n) : 1;
      if (!(sd > 1e-9)) sd = 1;
    }
    var yz = new Float64Array(n);
    for (i = 0; i < n; i++) yz[i] = (ys[i] - mu) / sd;

    var K = [];
    for (i = 0; i < n; i++) {
      K.push(new Float64Array(n));
      for (j = 0; j < n; j++) {
        K[i][j] = matern52(xs[i], xs[j], ell) + (i === j ? noise : 0);
      }
    }
    var L = cholesky(K, n);
    var alpha = backSolve(L, forwardSolve(L, yz, n), n);

    return {
      xs: xs.slice(), ell: ell, noise: noise, n: n,
      yMean: mu, yStd: sd, L: L, alpha: alpha,
      /* Predict at one point → {mean, std} in original units. */
      predict: function (x) {
        var k = new Float64Array(this.n), t;
        for (t = 0; t < this.n; t++) k[t] = matern52(x, this.xs[t], this.ell);
        var m = 0;
        for (t = 0; t < this.n; t++) m += k[t] * this.alpha[t];
        var w = forwardSolve(this.L, k, this.n);
        var vv = 1 + this.noise;
        for (t = 0; t < this.n; t++) vv -= w[t] * w[t];
        return {
          mean: m * this.yStd + this.yMean,
          std: Math.sqrt(Math.max(vv, 0)) * this.yStd
        };
      }
    };
  }

  /* Standard normal pdf/cdf. The cdf uses Abramowitz-Stegun 7.1.26 through
     erf — plenty for drawing a curve, and it is what EI needs. */
  function pdf(z) { return Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI); }

  function erf(x) {
    var s = x < 0 ? -1 : 1, ax = Math.abs(x);
    var t = 1 / (1 + 0.3275911 * ax);
    var y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t
                  - 0.284496736) * t + 0.254829592) * t * Math.exp(-ax * ax);
    return s * y;
  }
  function cdf(z) { return 0.5 * (1 + erf(z / Math.SQRT2)); }

  /* Expected improvement over the best MEASURED value (never a true value). */
  function ei(pred, best) {
    var s = Math.max(pred.std, 1e-9);
    var z = (pred.mean - best) / s;
    return (pred.mean - best) * cdf(z) + s * pdf(z);
  }

  root.GP = { fit: fit, ei: ei, matern52: matern52, cdf: cdf, pdf: pdf };
})(typeof globalThis !== "undefined" ? globalThis : this);
