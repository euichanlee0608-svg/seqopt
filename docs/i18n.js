/* Korean lives in the HTML; English lives here.
 *
 * Static text is swapped by `data-k` (the Korean original is stashed in
 * `data-ko` on first switch, so toggling back is lossless). Strings the
 * playground writes at runtime are looked up through I18N.t(). */
(function () {
  "use strict";

  var EN = {
    brand_sub: "· sequential optimization",
    nav_gh: "GitHub",

    hero_kick: "SEQUENTIAL OPTIMIZATION, EXPLAINED",
    hero_h1: "When one measurement is expensive,<br>what should you measure next?",
    hero_lead: "If a single experiment costs a day and consumes a sample, you cannot sweep every setting. <b>Sequential optimization</b> measures a few points, guesses the terrain from them, and picks <b>the one point to measure next</b>. Five minutes in the playground below is faster than any explanation.",
    hero_lead2: "The second half of this page is a different story — about <b>refusing to advise when the data cannot support advice.</b>",

    s1_step: "PART 1 · TRY IT",
    s1_h: "Find the highest point on a hidden curve",
    s1_sub: "Think of the panel below as your lab. Choosing a setting (horizontal axis) produces a result (vertical axis), but <b>the relationship is invisible.</b> Only measuring reveals it, and measuring costs. Click the panel to measure.",
    pl_hint: "Click the panel to measure that setting",
    pl_suggest: "Suggest the next point",
    pl_auto: "Run 5 automatically",
    pl_reveal: "Reveal the true curve",
    pl_reset: "Reset",
    st_n: "measurements",
    st_best: "best so far",
    st_gap: "gap to the true best",

    s1_h2: "Two things the model draws",
    s1_p1: "The <b>blue line</b> is the model's guess at the response surface. The <b>pale band</b> around it is uncertainty — \"I am not sure around here\". Near measured points the band is narrow; where nobody has been, it widens.",
    s1_p2: "The <b>orange curve</b> below is the heart of it. It scores every setting by \"how much would measuring here gain me\", and it is called <b>expected improvement (EI)</b>. Because it weighs looking-good against being-unknown together, already-measured places score near zero and the peak lands where something <b>looks promising and nobody has been yet</b>. Sequential optimization measures at that peak.",
    s1_note: "<b>How this differs from sweeping a grid</b> — a grid plans everything up front. Sequential lets <b>each result change the next plan.</b> Which is exactly why peeking at a value you have not measured is never allowed — that would be cheating.",

    s2_step: "PART 2 · WHAT MAKES THIS TOOL DIFFERENT",
    s2_h: "Before advising, check whether the advice can be trusted",
    s2_sub: "The curve in the playground was smooth. Real experimental data often is not. And yet <b>an ordinary optimization tool will hand you a smooth surface and a plausible next candidate anyway.</b> Trust that, and you spend time and samples on noise.",

    s2_h1: "① Is the model actually learning?",
    s2_p1: "Leave each condition out in turn, fit on the rest, and have it predict the one left out. When it learns, the points hug the diagonal. When it does not, they collapse onto the <b>red horizontal line (the overall mean)</b> — the state of \"answering the average no matter what you ask\" — and R² goes negative.",
    fig1_cap: "Left is learning (R² = +0.90). Right has learned nothing (R² = −0.14) — and in that state <b>changing the model will not help.</b> The signal is not in the data.",

    s2_h2: "② Do condition differences exceed the measurement wobble?",
    s2_p2: "Re-measure the same condition and the value shifts a little. If the difference made by changing conditions is smaller than that wobble, which condition is better cannot be told from noise. It is like separating two people 1 kg apart on a scale that jumps ±2 kg per reading — the scale's fault, not yours.",
    fig2_cap: "Gray dots are individual measurements, the blue line is the condition means. On the left the differences stand clearly above the wobble (D = 5.8); on the right they have drowned (D = 0.9). Below 1, there is no reason to run an optimizer at all.",

    s2_h3: "The four requirements",
    s2_p3: "seqopt checks these four before giving any recommendation. Fail any one and <b>the recommendation locks.</b>",
    t_h1: "requirement", t_h2: "what it checks", t_h3: "when it fails",
    t_r1a: "condition count", t_r1b: "more candidates than budget?", t_r1c: "measuring everything is better",
    t_r2a: "surface learnability", t_r2b: "is the model learning the terrain?", t_r2c: "changing the model will not help",
    t_r3a: "discriminability", t_r3b: "differences above the wobble?", t_r3c: "raise the replicate count",
    t_r4a: "replicates", t_r4b: "has any condition been re-measured?", t_r4c: "the wobble itself is unknowable",
    s2_note: "<b>Refusing is the feature.</b> That is where this program came from — a study of whether one device lab should adopt sequential optimization. On public datasets the method genuinely saved measurements; on that lab's own data, every dataset failed the four requirements. So the answer was \"not yet\", and the criteria used to reach it became this program's gate.",

    s3_step: "PART 3 · THE PROGRAM",
    s3_h: "So, what seqopt does",
    s3_sub: "A desktop program: open your spreadsheet, put the measurements in, and it judges whether this data can be used — handing you the next condition to measure only when it can. It runs from a single executable on PCs with no Python.",
    fig3_cap: "<b>The Diagnose screen</b> — each requirement's verdict is a sentence, and every number unfolds into its calculation. The prescription table on the right back-computes how many more replicates per condition the recommended level would cost.",
    fig4_cap: "<b>When the requirements are unmet</b> — no recommendation appears, but the reasons do. The suggestions are not hidden from the screen; they are <b>never constructed in the first place.</b> You can force a run anyway, but the resulting report is stamped on every page.",
    fig5_cap: "<b>The Model screen</b> — the same surface, uncertainty and EI you saw in Part 1, drawn from real data. Three or more variables switch it to slices with sliders, and an unlearned surface gets a stamp so a screenshot carries the warning with it.",
    s3_h2: "There is nothing to choose",
    s3_p1: "Other tools make you pick a surrogate, an acquisition function, a solver. Here they are all fixed. <b>The gate is what makes fixing them affordable</b> — when the data is bad, you do not have to wander between models, because the tool rules that changing the model will not help. Everything is still there under each screen's <i>Advanced</i> fold. Deferred, not deleted.",
    cta_dl: "Download for Windows",
    cta_repo: "View the source",
    s3_foot: "How to use it lives in the program's own help — each topic cites the code behind it. MIT licensed.",

    ft_1: "The math on this page really runs in your browser. Part 1's Gaussian process is checked numerically against scikit-learn, and Part 2's figures were produced by the program's own diagnostic code.",
    ft_2: "See the full portfolio →",

    /* runtime strings for the playground */
    ax_top: "result",
    ax_bot: "expected improvement (EI)",
    need3: "three measurements and the model starts drawing",
    say_0: "Click anywhere three times. Once three points are in, the model starts drawing the terrain.",
    say_few: "{0} more to go — the model needs three points before it can guess anything.",
    say_first: "There it is. The blue line is the guess, the band around it is doubt, and the orange peak below is where measuring would teach the most. Try \"Suggest the next point\".",
    say_go: "Still {0} short of the true best. Where would you measure next — where it looks highest, or where nobody has been?",
    say_win: "Found it, in {0} measurements. Try again with the grid: even steps left to right, and count how many it takes.",
    say_suggest: "EI peaks at x = {0}. Click near there to measure it.",
    say_reveal: "That is the true curve. Notice the smaller peak on the left — measuring only where things already look good would have stopped there.",
    say_hide: "Curve hidden again."
  };

  var KO = {
    ax_top: "결과값",
    ax_bot: "기대개선량 (EI)",
    need3: "세 번 재면 모델이 그리기 시작합니다",
    say_0: "아무 데나 세 번 눌러 보세요. 세 점이 모이면 모델이 지형을 그리기 시작합니다.",
    say_few: "{0}번 더 — 모델은 세 점이 있어야 무언가를 짐작할 수 있습니다.",
    say_first: "이제 보입니다. 파란 선이 짐작, 그 둘레 띠가 의심, 아래 주황 봉우리가 “여기를 재면 가장 많이 배운다”는 곳입니다. ‘다음 지점 제안받기’를 눌러 보세요.",
    say_go: "진짜 최고값까지 아직 {0} 남았습니다. 다음엔 어디를 재시겠어요 — 높아 보이는 곳일까요, 아무도 안 가 본 곳일까요?",
    say_win: "{0}회 만에 찾았습니다. 이번엔 격자로 해보세요 — 왼쪽부터 일정 간격으로 재면 몇 번이 걸리는지.",
    say_suggest: "EI 가 x = {0} 에서 가장 큽니다. 그 근처를 눌러 재 보세요.",
    say_reveal: "이게 진짜 곡선입니다. 왼쪽의 작은 봉우리를 보세요 — 높아 보이는 곳만 따라갔다면 거기서 멈췄을 겁니다.",
    say_hide: "곡선을 다시 감췄습니다."
  };

  var lang = "ko";

  function apply(next) {
    lang = next;
    document.documentElement.lang = next;
    document.querySelectorAll("[data-k]").forEach(function (el) {
      var key = el.getAttribute("data-k");
      if (!el.hasAttribute("data-ko")) el.setAttribute("data-ko", el.innerHTML);
      var val = next === "en" ? EN[key] : el.getAttribute("data-ko");
      if (val !== undefined && val !== null) el.innerHTML = val;
    });
    document.getElementById("ko").classList.toggle("on", next === "ko");
    document.getElementById("en").classList.toggle("on", next === "en");
    document.title = next === "en"
      ? "What is sequential optimization? — seqopt"
      : "순차 최적화란 무엇인가 — seqopt";
    try { localStorage.setItem("seqopt_lang", next); } catch (e) {}
    if (window.__playgroundRedraw) window.__playgroundRedraw();
  }

  window.I18N = {
    t: function (key) { return (lang === "en" ? EN[key] : KO[key]) || EN[key] || ""; },
    lang: function () { return lang; }
  };

  document.getElementById("ko").addEventListener("click", function () { apply("ko"); });
  document.getElementById("en").addEventListener("click", function () { apply("en"); });

  var start = "ko";
  try {
    var saved = localStorage.getItem("seqopt_lang");
    if (saved === "ko" || saved === "en") start = saved;
  } catch (e) {}
  if (location.search.indexOf("lang=en") !== -1) start = "en";
  if (location.search.indexOf("lang=ko") !== -1) start = "ko";
  apply(start);
})();
