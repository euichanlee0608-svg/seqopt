/* Three acts, one at a time.
 *
 * The page used to be 4300px of continuous scroll, which asked the reader to
 * commit before they knew whether any of it was for them. Each act is now its
 * own view: the tab bar is the table of contents, and the button at the foot
 * of each act is the way forward, so nobody has to scroll back up to advance.
 *
 * The hash is the address (#2), so a link into part 2 lands in part 2. */
(function () {
  "use strict";

  var N = 3;
  var tabs = [], panes = [];
  var i;
  for (i = 1; i <= N; i++) {
    tabs.push(document.getElementById("tab" + i));
    panes.push(document.getElementById("act" + i));
  }
  if (tabs.indexOf(null) >= 0 || panes.indexOf(null) >= 0) return;

  var current = 1, warmed = false;

  /* A hidden element never enters the viewport, so loading="lazy" holds the
     gallery's other two screenshots forever and switching tabs shows a blank.
     Warm them when part 3 opens — not before, so a reader who never gets
     there never pays for them. */
  function warmGallery() {
    if (warmed) return;
    warmed = true;
    var seen = {};
    document.querySelectorAll("#shots img").forEach(function (im) {
      var u = im.getAttribute("src");
      if (u && !seen[u]) { seen[u] = 1; new Image().src = u; }
    });
  }

  function show(n, scroll) {
    n = Math.max(1, Math.min(N, n | 0));
    current = n;
    for (var k = 0; k < N; k++) {
      var on = k === n - 1;
      panes[k].classList.toggle("on", on);
      tabs[k].classList.toggle("on", on);
      tabs[k].setAttribute("aria-selected", on ? "true" : "false");
    }
    /* The canvas sizes itself from clientWidth, which is 0 while its pane is
       display:none — so a canvas first revealed by a tab click must be
       remeasured, or it keeps the width it was born with. */
    if (n === 1 && window.__playgroundResize) window.__playgroundResize();

    var hero = document.querySelector(".hero");
    if (hero) hero.hidden = n !== 1;
    if (n === 3) warmGallery();

    if (scroll) {
      var bar = document.querySelector(".tabs");
      var y = bar ? bar.offsetTop : 0;
      window.scrollTo({ top: y, behavior: "smooth" });
    }
    if (history.replaceState) history.replaceState(null, "", "#" + n);
    else location.hash = "#" + n;
  }

  tabs.forEach(function (t, k) {
    t.addEventListener("click", function () { show(k + 1, true); });
  });

  document.querySelectorAll("[data-go]").forEach(function (b) {
    b.addEventListener("click", function () {
      show(parseInt(b.getAttribute("data-go"), 10), true);
    });
  });

  window.addEventListener("hashchange", function () {
    var n = parseInt((location.hash || "").replace(/[^0-9]/g, ""), 10);
    if (n >= 1 && n <= N && n !== current) show(n, false);
  });

  var start = parseInt((location.hash || "").replace(/[^0-9]/g, ""), 10);
  show(start >= 1 && start <= N ? start : 1, false);

  window.__actsCurrent = function () { return current; };

  /* ── the screenshot gallery: same idea, one level down ───────── */
  var gal = document.getElementById("shots");
  if (gal) {
    var gbtns = [].slice.call(gal.querySelectorAll(".gtabs button"));
    var figs = [].slice.call(gal.querySelectorAll("figure[data-shot]"));
    gbtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var want = btn.getAttribute("data-shot");
        gbtns.forEach(function (o) { o.classList.toggle("on", o === btn); });
        figs.forEach(function (f) { f.hidden = f.getAttribute("data-shot") !== want; });
      });
    });
    window.__galleryCurrent = function () {
      for (var k = 0; k < figs.length; k++) if (!figs[k].hidden) return k;
      return -1;
    };
  }
})();
