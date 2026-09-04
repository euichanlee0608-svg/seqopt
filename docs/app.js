/* The playground: click to measure, watch the model learn, let EI pick next.
 *
 * The curve is hidden from the reader, and — this is the part that matters —
 * hidden from the algorithm too. `truth()` is only ever called at a point the
 * user has actually "measured". Nothing here peeks ahead, because a demo that
 * cheats teaches the wrong thing. */
(function () {
  "use strict";

  var cv = document.getElementById("cv");
  if (!cv || !window.GP) return;
  var ctx = cv.getContext("2d");

  var C = {
    axis: "#8a9099", grid: "#eceff1", ink: "#1f2328", muted: "#59636e",
    faint: "#98a1ab",
    mean: "#0969da", band: "rgba(9,105,218,.16)",
    point: "#1f2328", best: "#cf222e", ei: "#f57c00",
    eiFill: "rgba(245,124,0,.20)", truth: "#1a7f37", ghost: "#c8d1da"
  };

  /* The hidden response surface. Deliberately not a single clean bump: a
     smaller local peak on the left is what makes "measure where it looks good"
     alone a losing strategy. */
  function truth(x) {
    return 0.62 * Math.exp(-Math.pow((x - 0.28) / 0.13, 2))
         + 1.00 * Math.exp(-Math.pow((x - 0.74) / 0.10, 2))
         + 0.18 * x + 0.06;
  }
  var NOISE = 0.012;                 // measurement wobble, so replicates differ
  var TRUE_BEST = (function () {
    var b = -Infinity, x;
    for (x = 0; x <= 1.0001; x += 0.0005) b = Math.max(b, truth(x));
    return b;
  })();

  var xs = [], ys = [], revealed = false, suggestion = null, rng = 12345;

  function rand() {                  // small deterministic PRNG: same demo every visit
    rng = (rng * 1103515245 + 12345) & 0x7fffffff;
    return rng / 0x7fffffff;
  }
  function gauss() {
    return Math.sqrt(-2 * Math.log(rand() + 1e-12)) * Math.cos(2 * Math.PI * rand());
  }

  /* ── geometry ───────────────────────────────────────────────────
     A fixed 0.52 aspect turned the panel into a 348x181 letterbox on a
     phone, where the two stacked plots had ~120px and ~55px to live in.
     Narrow screens get a portrait panel instead: height grows past the
     width, and the paddings and type shrink to match. */
  var DPR = Math.min(window.devicePixelRatio || 1, 2);
  var NARROW = 520;
  var W = 0, H = 0, PAD = null, SPLIT = 0.68, GAPY = 26, SMALL = false;

  function resize() {
    var cssW = cv.clientWidth || 860;
    if (!cssW) return;                 // hidden pane: nothing to measure yet
    SMALL = cssW < NARROW;
    var cssH = SMALL
      ? Math.round(Math.min(cssW * 1.16, 440))
      : Math.round(Math.min(Math.max(cssW * 0.48, 320), 430));
    PAD = SMALL ? { l: 32, r: 12, t: 14, b: 26 } : { l: 52, r: 18, t: 18, b: 32 };
    SPLIT = SMALL ? 0.60 : 0.68;
    GAPY = SMALL ? 34 : 30;
    cv.width = Math.round(cssW * DPR);
    cv.height = Math.round(cssH * DPR);
    cv.style.height = cssH + "px";
    W = cssW; H = cssH;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    draw();
  }

  function topBox() {
    return { x: PAD.l, y: PAD.t, w: W - PAD.l - PAD.r,
             h: (H - PAD.t - PAD.b - GAPY) * SPLIT };
  }
  function botBox() {
    var t = topBox();
    return { x: t.x, y: t.y + t.h + GAPY, w: t.w,
             h: (H - PAD.t - PAD.b - GAPY) * (1 - SPLIT) };
  }
  function fnt(px) { return (SMALL ? px - 1 : px) + "px "; }
  var Y_LO = 0.0, Y_HI = 1.30;
  function sx(b, x) { return b.x + x * b.w; }
  function sy(b, y) { return b.y + b.h - ((y - Y_LO) / (Y_HI - Y_LO)) * b.h; }

  /* ── model ──────────────────────────────────────────────────── */
  function model() {
    if (xs.length < 3) return null;
    return window.GP.fit(xs, ys, { ell: 0.15, noise: 0.01 });
  }
  function bestMeasured() {
    return ys.length ? Math.max.apply(null, ys) : -Infinity;
  }
  function eiCurve(m, n) {
    var out = [], i, x, best = bestMeasured();
    for (i = 0; i <= n; i++) {
      x = i / n;
      out.push({ x: x, v: window.GP.ei(m.predict(x), best) });
    }
    return out;
  }

  /* ── drawing ────────────────────────────────────────────────── */
  function axes(b, label, yTicks, xTicks) {
    ctx.strokeStyle = C.grid; ctx.lineWidth = 1;
    ctx.fillStyle = C.muted;
    ctx.font = fnt(11) + "ui-monospace,Menlo,monospace";
    var i, gx, nx = SMALL ? 5 : 10;
    for (i = 0; i <= nx; i++) {
      gx = sx(b, i / nx);
      ctx.beginPath(); ctx.moveTo(gx, b.y); ctx.lineTo(gx, b.y + b.h); ctx.stroke();
    }
    if (yTicks) {
      [0, 0.5, 1.0].forEach(function (v) {
        var gy = sy(b, v);
        ctx.beginPath(); ctx.moveTo(b.x, gy); ctx.lineTo(b.x + b.w, gy); ctx.stroke();
        ctx.textAlign = "right"; ctx.textBaseline = "middle";
        ctx.fillText(v.toFixed(1), b.x - 7, gy);
      });
    }
    ctx.strokeStyle = C.axis; ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(b.x, b.y); ctx.lineTo(b.x, b.y + b.h); ctx.lineTo(b.x + b.w, b.y + b.h);
    ctx.stroke();
    /* The suggestion is announced as "x = 0.94"; without a scale under the
       axis there is no way to find 0.94 on the panel. */
    if (xTicks) {
      ctx.fillStyle = C.muted; ctx.textBaseline = "top";
      [0, 0.5, 1].forEach(function (v) {
        ctx.textAlign = v === 0 ? "left" : (v === 1 ? "right" : "center");
        ctx.fillText(v.toFixed(1), sx(b, v), b.y + b.h + 6);
      });
    }
    ctx.fillStyle = C.muted; ctx.textAlign = "left"; ctx.textBaseline = "top";
    ctx.font = fnt(12) + "-apple-system,system-ui,sans-serif";
    ctx.fillText(label, b.x + 4, b.y + 4);
  }

  /* Everything plotted is clipped to its panel. With three points the +-2s
     band is genuinely taller than the axis range, and without a clip it spills
     over the frame and reads as a rendering fault rather than as doubt. */
  function clipTo(b, fn) {
    ctx.save();
    ctx.beginPath();
    ctx.rect(b.x, b.y, b.w, b.h);
    ctx.clip();
    fn();
    ctx.restore();
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    var top = topBox(), bot = botBox(), m = model(), i, x, p;

    axes(top, T("ax_top"), true, false);

    clipTo(top, function () {
    if (revealed) {                       // the answer, only when asked for
      ctx.strokeStyle = C.truth; ctx.lineWidth = 2; ctx.setLineDash([6, 5]);
      ctx.beginPath();
      for (i = 0; i <= 240; i++) {
        x = i / 240;
        if (i === 0) ctx.moveTo(sx(top, x), sy(top, truth(x)));
        else ctx.lineTo(sx(top, x), sy(top, truth(x)));
      }
      ctx.stroke(); ctx.setLineDash([]);
    }

    if (m) {
      var N = 200, mm = [], ss = [];
      for (i = 0; i <= N; i++) {
        p = m.predict(i / N); mm.push(p.mean); ss.push(p.std);
      }
      ctx.fillStyle = C.band;             // ±2σ band
      ctx.beginPath();
      for (i = 0; i <= N; i++) ctx.lineTo(sx(top, i / N), sy(top, mm[i] + 2 * ss[i]));
      for (i = N; i >= 0; i--) ctx.lineTo(sx(top, i / N), sy(top, mm[i] - 2 * ss[i]));
      ctx.closePath(); ctx.fill();
      ctx.strokeStyle = C.mean; ctx.lineWidth = 2.4;   // predicted mean
      ctx.beginPath();
      for (i = 0; i <= N; i++) {
        if (i === 0) ctx.moveTo(sx(top, 0), sy(top, mm[0]));
        else ctx.lineTo(sx(top, i / N), sy(top, mm[i]));
      }
      ctx.stroke();
    }
    });

    if (!xs.length) {                     // an empty panel should say what to do
      ctx.fillStyle = C.faint;
      ctx.font = fnt(14) + "-apple-system,system-ui,sans-serif";
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(T("pl_empty"), top.x + top.w / 2, top.y + top.h / 2);
      ctx.textAlign = "left";
    }

    var best = bestMeasured();            // measured points
    clipTo(top, function () {
      xs.forEach(function (x, k) {
        var isBest = ys[k] === best;
        ctx.beginPath();
        ctx.arc(sx(top, x), sy(top, ys[k]), isBest ? 7 : 5, 0, 6.2832);
        ctx.fillStyle = isBest ? C.best : C.point;
        ctx.fill();
        ctx.strokeStyle = "#fff"; ctx.lineWidth = 1.6; ctx.stroke();
      });
    });

    axes(bot, T("ax_bot"), false, true);
    if (m) {
      var e = eiCurve(m, 200), emax = 0;
      e.forEach(function (d) { emax = Math.max(emax, d.v); });
      var scale = emax > 1e-9 ? (bot.h - 10) / emax : 0;
      clipTo(bot, function () {
      ctx.fillStyle = C.eiFill;
      ctx.beginPath();
      ctx.moveTo(sx(bot, 0), bot.y + bot.h);
      e.forEach(function (d) { ctx.lineTo(sx(bot, d.x), bot.y + bot.h - d.v * scale); });
      ctx.lineTo(sx(bot, 1), bot.y + bot.h);
      ctx.closePath(); ctx.fill();
      ctx.strokeStyle = C.ei; ctx.lineWidth = 2;
      ctx.beginPath();
      e.forEach(function (d, k) {
        var px = sx(bot, d.x), py = bot.y + bot.h - d.v * scale;
        if (k === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      });
      ctx.stroke();
      });

      if (suggestion !== null) {          // where EI says to go next
        [top, bot].forEach(function (b) {
          ctx.strokeStyle = C.ei; ctx.lineWidth = 1.5; ctx.setLineDash([5, 4]);
          ctx.beginPath();
          ctx.moveTo(sx(b, suggestion), b.y); ctx.lineTo(sx(b, suggestion), b.y + b.h);
          ctx.stroke(); ctx.setLineDash([]);
        });
        ctx.beginPath();
        ctx.moveTo(sx(top, suggestion), sy(top, Y_LO) - 4);
        ctx.lineTo(sx(top, suggestion) - 6, sy(top, Y_LO) - 14);
        ctx.lineTo(sx(top, suggestion) + 6, sy(top, Y_LO) - 14);
        ctx.closePath(); ctx.fillStyle = C.ei; ctx.fill();

        var lx = sx(bot, suggestion), tw, lab = suggestion.toFixed(2);
        ctx.font = fnt(11) + "ui-monospace,Menlo,monospace";
        tw = ctx.measureText(lab).width + 10;
        lx = Math.max(bot.x, Math.min(bot.x + bot.w - tw, lx - tw / 2));
        ctx.fillStyle = C.ei;
        ctx.fillRect(lx, bot.y + bot.h + 3, tw, 15);
        ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(lab, lx + tw / 2, bot.y + bot.h + 11);
        ctx.textAlign = "left";
      }
    } else {
      ctx.fillStyle = C.muted;
      ctx.font = "13px -apple-system,system-ui,sans-serif";
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(T("need3"), bot.x + bot.w / 2, bot.y + bot.h / 2);
      ctx.textAlign = "left";
    }
  }

  /* ── interaction ────────────────────────────────────────────── */
  function measure(x) {
    x = Math.max(0, Math.min(1, x));
    xs.push(x);
    ys.push(truth(x) + NOISE * gauss());
    suggestion = null;
    update();
  }

  function suggest() {
    var m = model();
    if (!m) return null;
    var e = eiCurve(m, 400), bestX = 0, bestV = -Infinity;
    e.forEach(function (d) { if (d.v > bestV) { bestV = d.v; bestX = d.x; } });
    return { x: bestX, v: bestV };
  }

  cv.addEventListener("click", function (ev) {
    var r = cv.getBoundingClientRect(), top = topBox();
    var x = (ev.clientX - r.left - top.x) / top.w;
    if (x < -0.04 || x > 1.04) return;
    measure(x);
  });

  document.getElementById("btnSuggest").addEventListener("click", function () {
    var s = suggest();
    if (!s) return;
    suggestion = s.x;
    draw();
    say(fmt(T("say_suggest"), [s.x.toFixed(2)]), "");
  });

  document.getElementById("btnAuto").addEventListener("click", function () {
    var k = 0;
    (function step() {
      if (k++ >= 5) { update(); return; }
      if (xs.length < 3) measure(rand());
      else { var s = suggest(); measure(s ? s.x : rand()); }
      setTimeout(step, 420);
    })();
  });

  document.getElementById("btnReveal").addEventListener("click", function () {
    revealed = !revealed;
    draw();
    say(revealed ? T("say_reveal") : T("say_hide"), "");
  });

  document.getElementById("btnReset").addEventListener("click", function () {
    xs = []; ys = []; revealed = false; suggestion = null; rng = 12345;
    update();
    say(T("say_0"), "");
  });

  /* ── status ─────────────────────────────────────────────────── */
  function fmt(s, args) {
    return s.replace(/\{(\d)\}/g, function (_, i) { return args[i]; });
  }
  function say(text, cls) {
    var el = document.getElementById("say");
    el.innerHTML = text;
    el.className = "say" + (cls ? " " + cls : "");
    el.removeAttribute("data-k");         // the script owns this line now
  }

  function update() {
    draw();
    var n = xs.length, best = bestMeasured();
    document.getElementById("stN").textContent = String(n);
    document.getElementById("stBest").textContent = n ? best.toFixed(3) : "—";
    document.getElementById("stGap").textContent =
      n ? (TRUE_BEST - best).toFixed(3) : "—";
    document.getElementById("btnSuggest").disabled = n < 3;

    if (n === 0) say(T("say_0"), "");
    else if (n < 3) say(fmt(T("say_few"), [3 - n]), "");
    else if (TRUE_BEST - best < 0.02) say(fmt(T("say_win"), [n]), "ok");
    else if (n === 3) say(T("say_first"), "");
    else say(fmt(T("say_go"), [(TRUE_BEST - best).toFixed(3)]), "");
  }

  /* Strings live in i18n.js; before it loads, fall back to the key. */
  function T(k) {
    return (window.I18N && window.I18N.t(k)) || "";
  }
  window.__playgroundRedraw = update;
  window.__playgroundResize = resize;

  window.addEventListener("resize", resize);
  resize();
  update();
})();
