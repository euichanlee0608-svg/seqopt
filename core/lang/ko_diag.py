# -*- coding: utf-8 -*-
"""Korean for ui/tab_diag.py · core/diagnostics.py. Keys are the English strings as written in the code (core/i18n.py)."""

KO: dict[str, str] = {

    # ── core/diagnostics.py — D level marks · nugget scale · gate reasons ─
    "Gate (minimum)": "관문 (최소)",
    "difference = wobble": "차이 = 흔들림",
    "Follows from the definition of D. With σb < σw, condition differences are smaller than replicate wobble":
        "판별력 D 의 정의에서 바로 나옵니다. σb < σw 이면 조건 차이가 반복 측정의 흔들림보다 작습니다",
    "Recommended": "권장",
    "difference ≈ wobble × 2": "차이 ≈ 흔들림 × 2",
    "Two means about two standard errors apart — the usual boundary for 'different' (95%, z≈1.96)":
        "두 평균이 표준오차 2배쯤 떨어진 상태 — '다르다'고 말하는 통상의 경계 (95%, z≈1.96)",
    "Comfortable": "넉넉",
    "difference ≈ wobble × 3.5": "차이 ≈ 흔들림 × 3.5",
    "Matches the AIAG MSA distinct-category requirement ndc = 1.41·σb/σw ≥ 5":
        "측정시스템분석(AIAG MSA)의 구분 범주 요건 ndc = 1.41·σb/σw ≥ 5 에 해당합니다",
    "strong structure": "강한 구조",
    "moderate": "보통",
    "weak structure": "약한 구조",
    "σb is ≤ 0 — there is no difference between the conditions": "σb 가 0 이하입니다 — 조건 사이에 차이가 없습니다",
    "Selectable conditions {n} ≤ budget {budget} runs → measuring everything is better":
        "고를 수 있는 조건 {n}개 ≤ 예산 {budget}회 → 전수 측정이 더 낫습니다",
    "Learnability R² still computing": "학습가능성 R² 계산 중",
    "Learnability R² = {r2} ≤ 0 → worse than always answering the overall mean":
        "학습가능성 R² = {r2} ≤ 0 → 전체 평균만 답하기보다 나쁩니다",
    "Discriminability interval upper bound {hi} < 1.0 → conditions cannot be told apart":
        "판별력 구간 상한 {hi} < 1.0 → 조건을 구별할 수 없습니다",
    "The discriminability interval straddles 1.0 → undecided": "판별력 구간이 1.0 을 걸칩니다 → 판정불가",
    "No replicate measurements, so discriminability cannot be computed": "반복 측정이 없어 판별력을 계산할 수 없습니다",

    # ── ui/tab_diag.py — the page, the gate table, the D card ─────────────
    "Diagnose — can this data be trusted": "진단 — 이 데이터를 믿어도 되는가",
    "Four requirements are checked before any recommendation. Failing any one locks it.":
        "추천을 내기 전에 네 가지 요건을 검사합니다. 하나라도 미달이면 추천을 잠급니다.",
    "The four requirements?": "요건 4가지란?",
    "Discriminability?": "판별력이란?",
    "Why 1 · 2 · 3.5?": "기준값 1 · 2 · 3.5 는?",
    "R² is negative?": "R² 가 음수면?",
    "Gate verdict": "요건 판정",
    "All four lines must be ○ for recommendations to open. The right side is each requirement's criterion.":
        "네 줄이 모두 ○ 여야 추천이 열립니다. 오른쪽은 각 요건의 기준입니다.",
    "① candidate count": "① 후보 수",
    "candidates > budget": "후보 > 예산",
    "② surface learnability": "② 응답면 학습",
    "③ discriminability": "③ 판별력",
    "D > {gate} · recommended ≥ {rec}": "D > {gate} · 권장 ≥ {rec}",
    "④ replicates": "④ 반복 측정",
    "≥ 50% with replicates": "반복 있는 조건 ≥ 50%",
    "{where} > budget {budget} — there is room to choose": "{where} > 예산 {budget}회 — 고를 여지가 있습니다",
    "{where} ≤ budget {budget} — <b>measuring everything is better</b> (the gain from optimizing is zero in principle). A finer step or a wider range gives more candidates.":
        "{where} ≤ 예산 {budget}회 — <b>전수 측정이 더 낫습니다</b> (최적화의 이득이 원리적으로 0). 간격을 촘촘히 하거나 범위를 넓히면 후보가 늘어납니다.",
    "Computing… (many conditions can take tens of seconds)": "계산 중입니다… (조건 수가 많으면 수십 초 걸립니다)",
    " · fewer than 8 conditions, so the sample is thin": " · 조건 8개 미만이라 표본이 부족합니다",
    "Learnability R² = {r2} — the surface is being learned{note}": "학습가능성 R² = {r2} — 응답면을 배우고 있습니다{note}",
    "Learnability R² = {r2} ≤ 0 — <b>worse than always answering the overall mean</b>. The model has learned nothing{note}":
        "학습가능성 R² = {r2} ≤ 0 — <b>'전체 평균만 답하기'보다 나쁩니다</b>. 모델이 아무것도 못 배운 상태입니다{note}",
    "No replicate measurements, so it cannot be computed. No assumed value is substituted — measure the same condition at least twice.":
        "반복 측정이 없어 계산할 수 없습니다. 가정값을 넣지 않습니다 — 같은 조건을 두 번 이상 재세요.",
    "{base} — condition differences can be told apart": "{base} — 조건 간 차이를 구별할 수 있습니다",
    ". Past the gate, but short of the recommended {rec} — raising replicates per the prescription steadies the recommendations":
        ". 관문은 넘었지만 권장 {rec} 에는 못 미칩니다 — 처방대로 반복을 늘리면 추천이 더 안정됩니다",
    "{base} — the measurement wobble exceeds the condition differences": "{base} — 측정 흔들림이 조건 간 차이보다 큽니다",
    "{base} — <b>undecided</b>. The 95% interval straddles the gate at {gate}. This data cannot settle passed-or-failed either way.":
        "{base} — <b>판정불가</b>. 95% 구간이 관문 {gate} 을 걸칩니다. 지금 데이터로는 넘었다/못 넘었다를 단정할 수 없습니다.",
    "conditions with replicates {n}/{total} ({pct}%)": "반복 있는 조건 {n}/{total} ({pct}%)",
    "<b>Recommendations are locked</b> — {n} requirement(s) unmet<br>{why}":
        "<b>추천 기능이 잠겨 있습니다</b> — 미달 {n}건<br>{why}",
    "<b>Requirements met.</b> Get your next candidates on the Recommend tab.":
        "<b>요건을 통과했습니다.</b> 추천 탭에서 다음 후보를 받을 수 있습니다.",
    "Discriminability D — which zone are you in": "판별력 D — 지금 어느 구간인가",
    "The difference that changing conditions makes (σb), divided by the wobble of re-measuring the same condition (σw). The larger it is, the further condition differences rise above the noise.":
        "조건을 바꿔서 생기는 차이(σb)를 같은 조건을 다시 재서 생기는 흔들림(σw)으로 나눈 값입니다. 클수록 조건 간 차이가 잡음 위로 드러납니다.",
    "Replicate measurements are needed to compute discriminability.": "반복 측정이 있어야 판별력을 계산할 수 있습니다.",
    "The condition differences are <b>smaller</b> than the measurement wobble. Right now, which condition is better cannot be told from noise.":
        "조건 간 차이가 측정 흔들림보다 <b>작습니다</b>. 지금은 어느 조건이 나은지 잡음과 구별되지 않습니다.",
    "Past the gate, but <b>borderline</b>. Differences are only 1–2× the wobble, so rankings can flip. See the prescription on the right to reach the recommended {rec}.":
        "관문은 넘었지만 <b>경계</b>입니다. 조건 차이가 흔들림의 1~2배라 순위가 뒤바뀔 수 있습니다. 권장 {rec} 까지 올리려면 오른쪽 처방을 보세요.",
    "The condition differences stand <b>clearly</b> above the wobble.":
        "조건 간 차이가 흔들림 위로 <b>또렷이</b> 드러납니다.",
    " The 95% interval straddles the gate at {gate}, so with this data the verdict is <b>undecided</b> — more replicates narrow the interval.":
        " 95% 구간이 관문 {gate} 을 걸치므로 지금 데이터로는 <b>판정불가</b>입니다 — 반복을 늘리면 구간이 좁아집니다.",
    "thresholds and their basis": "기준값과 그 근거",

    # ── ui/tab_diag.py — the calculation card, the prescription, terrain ──
    "The calculation — where this number came from": "계산 과정 — 이 숫자가 어디서 왔는가",
    "The general formula first, then the same formula with this data's values. Unfold the per-condition table to see the raw material.":
        "먼저 일반식, 그다음 이 데이터의 값을 넣은 식입니다. 조건별 표를 펼치면 재료가 보입니다.",
    "Unfold the per-condition table ▾": "조건별 표 펼치기 ▾",
    "Fold the per-condition table ▴": "조건별 표 접기 ▴",
    "<b>How to read this table</b> — one row is one condition. <b>n</b> is how many times it was measured, <b>sample SD</b> how much those replicates wobbled, and <b>(n−1)·var</b> that wobble's share of the total σw. The σw · σb · D in the formulas above come straight from these numbers.":
        "<b>표 읽는 법</b> — 한 행이 조건 하나입니다. <b>n</b> 은 그 조건을 몇 번 쟀는지, <b>표본SD</b> 는 그 반복들이 얼마나 흔들렸는지, <b>(n−1)·var</b> 는 그 흔들림이 전체 σw 에 기여하는 몫입니다. 위 수식의 σw · σb · D 가 이 표의 숫자에서 바로 나옵니다.",
    "condition": "조건",
    "n\n(replicates)": "n\n(반복 횟수)",
    "mean": "평균",
    "sample SD\n(wobble)": "표본SD\n(흔들림)",
    "(n−1)·var\n(σw share)": "(n−1)·var\n(σw 기여분)",
    "The combination of input values, in the order defined on the Setup tab.":
        "입력 변수 값의 조합. 설정 탭에 정의한 순서대로 적힙니다.",
    "How many times this condition was measured. 1 means its wobble is unknowable.":
        "이 조건을 몇 번 쟀는가. 1이면 흔들림을 알 수 없습니다.",
    "The mean of those replicates — the raw material of σb.": "그 반복들의 평균 — 조건간 차이 σb 를 만드는 재료입니다.",
    "How much those replicates scatter (sample standard deviation).": "그 반복들이 서로 얼마나 흩어져 있는가 (표본표준편차).",
    "This condition's share of σw. Summed and divided by the dof, it gives σw².":
        "이 조건이 σw 에 기여하는 몫. 전부 더해 자유도로 나누면 σw² 입니다.",
    "Only one replicate, so this condition does not enter the σw calculation.":
        "반복이 1회뿐이라 이 조건은 σw 계산에 들어가지 않습니다.",
    "The condition carrying the largest share of within-condition variance (see the warning on the right).":
        "조건내 분산을 가장 많이 차지하는 조건입니다 (오른쪽 경고 참조).",
    "No condition has replicates, so σw cannot be computed. Measure the same condition at least twice.":
        "반복이 있는 조건이 없어 σw 를 계산할 수 없습니다. 같은 조건을 두 번 이상 재야 합니다.",
    "95% interval [{lo}, {hi}] — condition bootstrap, {draws} draws":
        "95% 구간 [{lo}, {hi}] — 조건 단위 부트스트랩 {draws}회",
    "too few conditions for an interval": "구간을 낼 만큼 조건이 많지 않습니다",
    "within-condition wobble — the dof-weighted average of the replicated conditions' variances, square-rooted":
        "조건내 흔들림 — 반복이 2회 이상인 조건의 분산을 자유도로 가중평균한 뒤 제곱근",
    "between-condition difference — the sample SD of the condition means": "조건간 차이 — 조건 평균들의 표본표준편차",
    "discriminability — with n replicates per condition, the mean's wobble shrinks to σw/√n":
        "판별력 — 조건당 n 회 재면 평균의 흔들림이 σw/√n 으로 줄어듭니다",
    "Σ(n−1)·s² = {ss}, dof Σ(n−1) = {df}": "Σ(n−1)·s² = {ss}, 자유도 Σ(n−1) = {df}",
    "the means of the {k} conditions (condition order: {order})": "조건 {k}개의 평균 (조건 표기 순서: {order})",
    "Prescription — how many replicates": "처방 — 반복을 몇 번 하면 되나",
    "For each target discriminability: replicates per condition, and how many more measurements that costs. The recommended row is green.":
        "목표 판별력마다 조건당 반복 횟수와 추가로 재야 하는 횟수입니다. 권장 줄이 초록입니다.",
    "target D": "목표 D",
    "meaning": "뜻",
    "reps\nper condition": "조건당\n반복",
    "extra\nruns": "추가\n측정",
    "The discriminability you want to reach.": "도달하려는 판별력입니다.",
    "What that mark means (core/diagnostics.py: D_LEVELS).":
        "그 눈금이 뜻하는 바입니다 (core/diagnostics.py: D_LEVELS).",
    "How many times each condition would have to be measured.": "조건마다 몇 번씩 재야 하는지입니다.",
    "How many measurements that adds, over every condition together.": "모든 조건을 합쳐 추가로 재야 하는 횟수입니다.",
    "enough": "충분",
    "Replicate measurements are needed to compute this.": "반복 측정이 있어야 계산할 수 있습니다.",
    "Based on {n} conditions. Replicates n solves D(n) = σb/(σw/√n) for n, and it is a projection <b>assuming σw stays what it is now</b>. More replicates change the σw estimate too, so measure up to the recommended row and diagnose again.":
        "조건 {n}개 기준. 조건당 반복 n 은 D(n) = σb/(σw/√n) 을 n 에 대해 푼 값이며, <b>σw 가 지금과 같다는 가정</b> 위의 예상값입니다. 반복을 늘리면 σw 추정도 바뀌므로 권장 줄까지 재고 다시 진단하세요.",
    "Compute for another target": "다른 목표로 계산",
    "Target discriminability": "목표 판별력",
    "Target D = {target} → measure each condition <b>{n}×</b> and D becomes {becomes}. With {cond} conditions that is <b>{extra} extra measurements</b>.":
        "목표 D = {target} → 조건마다 <b>{n}회씩</b> 재면 D 가 {becomes} 이 됩니다. 조건 {cond}개 기준 <b>추가 측정 {extra}회</b>.",
    "Warning — one condition dominates D": "경고 — 조건 하나가 D 를 좌우합니다",
    "One condition, <b>{where}</b>, carries <b>{pct}%</b> of the within-condition variance.":
        "조건 <b>{where}</b> 하나가 조건내 분산의 <b>{pct}%</b> 를 차지합니다.",
    "Without it, σw is {sigma} and D is {d}.": "그 조건을 빼면 σw {sigma} · D {d} 입니다.",
    "The discriminability estimate leans heavily on one condition. Re-measuring that condition is the cheapest check.":
        "판별력 추정이 조건 하나에 크게 의존합니다. 그 조건을 다시 재 보는 것이 가장 값싼 확인입니다.",
    "Terrain — is the response surface smooth": "지형 — 응답면이 매끄러운가",
    "When even nearby conditions differ wildly (a large nugget), the model has little to learn from.":
        "가까운 조건끼리도 값이 크게 다르면(너깃이 크면) 모델이 배울 것이 적습니다.",
    "Computed once there are at least 3 conditions.": "조건이 3개 이상이어야 계산합니다.",
    "nugget ratio = nugget {nugget} / sill {sill} = <b>{ratio}</b>":
        "너깃비 = 너깃 {nugget} / 문턱값 {sill} = <b>{ratio}</b>",
    "<b>{pct}%</b> of the visible variation is measurement wobble.": "보이는 차이의 <b>{pct}%</b> 가 측정 흔들림입니다.",
    "A rough surface — raise replicates first.": "거친 응답면입니다 — 반복을 먼저 늘려야 합니다.",
    "A smooth surface.": "매끄러운 응답면입니다.",
    "This tool's criterion: nugget ratio > {limit} counts as rough. Reference scale (geostatistics, Cambardella 1994): &lt;0.25 strong structure · 0.25–0.75 moderate · &gt;0.75 weak — currently «{cls}».":
        "이 도구의 기준: 너깃비 > {limit} 이면 거칠다고 봅니다. 참고 눈금(지구통계, Cambardella 1994): &lt;0.25 강한 구조 · 0.25~0.75 보통 · &gt;0.75 약한 구조 — 지금은 «{cls}».",
    "Replicate measurements are needed to compute D": "반복 측정이 있어야 판별력 D 를 계산할 수 있습니다",
    "indistinguishable": "구별 불가",
    "borderline": "경계",
    "usable": "쓸 만함",
    "comfortable": "넉넉",
}
