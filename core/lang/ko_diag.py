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
}
