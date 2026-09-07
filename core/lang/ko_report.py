# -*- coding: utf-8 -*-
"""Korean for core/report.py · core/plotstyle.py · core/fonts.py. Keys are the English strings as written in the code (core/i18n.py)."""

KO: dict[str, str] = {
    # --- calculation_log ---
    "{name} — full calculation disclosure": "{name} — 계산 과정 전체 공개",
    "generated {ts}": "생성 {ts}",
    "  conditions {all} total · {usable} usable (excluded {excl}) · {meas} measurements":
        "  전체 조건 {all}개 · 유효 {usable}개 (제외 {excl}개) · 측정 {meas}회",
    "  replicate distribution : {dist}": "  반복 분포 : {dist}",
    "  objective : {name} {goal}{log}": "  목표 : {name} {goal}{log}",
    "maximize": "최대화",
    "minimize": "최소화",
    " · log10 transform": " · log10 변환",
    "[step 1] within-condition spread sigma_w — NOT COMPUTABLE (no replicate measurements)":
        "[1단계] 조건내 산포 sigma_w — 계산 불가 (반복 측정이 없다)",
    "No assumed value is substituted. Measure the same condition at least twice.":
        "가정값을 넣지 않는다. 같은 조건을 두 번 이상 재야 한다.",
    "[step 1] within-condition spread sigma_w — the wobble from re-measuring the same condition":
        "[1단계] 조건내 산포 sigma_w — 같은 조건을 다시 재서 생기는 흔들림",
    "condition": "조건",
    "mean": "평균",
    "sample SD": "표본SD",
    "total": "합계",
    "(dof {n})": "(자유도 {n})",
    "[step 2] between-condition spread sigma_b — the difference that changing the condition makes":
        "[2단계] 조건간 산포 sigma_b — 조건을 바꿔서 생기는 차이",
    "sample SD of the {n} condition means": "조건 평균 {n}개의 표본표준편차",
    "sigma_b = {b}   (grand mean {g})": "sigma_b = {b}   (전체 평균 {g})",
    "[step 3] discriminability D = sigma_b / (sigma_w / sqrt(n))":
        "[3단계] 판별력 D = sigma_b / (sigma_w / sqrt(n))",
    "<- current (single-replicate basis)": "<- 현재 (반복 1회 기준)",
    "note: values for larger n are projections — they hold only if sigma_w stays the same.":
        "※ n 을 늘렸을 때의 값은 '예상값'이다. sigma_w 가 그대로라는 가정 위에서만 성립한다.",
    "[step 3-1] how solid is this estimate": "[3-1] 이 추정은 얼마나 단단한가",
    "condition bootstrap, 4000 draws : D(n=1) 95% interval = [{lo}, {hi}]":
        "조건 부트스트랩 4000회 : D(n=1) 95% 구간 = [{lo}, {hi}]",
    "clears the threshold": "임계를 넘는다",
    "falls short of the threshold": "임계에 못 미친다",
    "the threshold sits inside the interval — cannot be settled": "임계가 구간 안에 있다 — 단정할 수 없다",
    "against threshold {t} : {v}": "임계 {t} 기준 : {v}",
    "{pct}% of the within-condition variance comes from one condition ({top}).":
        "조건내 분산의 {pct}% 가 조건 하나({top})에서 나온다.",
    "dropping it gives sigma_w={a} · D(n=1)={b}": "그 조건을 빼면 sigma_w={a} · D(n=1)={b}",
    "[step 4] surface learnability — LOOCV prediction of the condition means":
        "[4단계] 응답면 학습가능성 — 조건 평균을 LOOCV 로 예측",
    "leave one condition out, fit on the rest ({n} conditions)":
        "조건을 하나씩 빼고 나머지로 학습 (조건 {n}개)",
    "R^2 <= 0 means worse than always answering the overall mean.":
        "R^2 <= 0 은 '전체 평균만 답하기'보다 나쁘다는 뜻이다.",
    "note: fewer than 8 conditions — low-sample warning": "※ 조건 8개 미만 — 표본 부족 경고",
    "[step 5] terrain roughness — semivariogram": "[5단계] 지형 거칠기 — 반변이도",
    "nugget {a} / sill {b} = nugget ratio {c}": "너깃 {a} / 문턱값(sill) {b} = 너깃비 {c}",
    "rough surface": "거친 응답면",
    "smooth surface": "매끄러운 응답면",
    "{pct}% of the visible variation is measurement wobble.": "보이는 차이의 {pct}% 가 측정 흔들림이다.",
    "[gate verdict]": "[요건 판정]",
    "① evidence : {ev} vs budget {b} runs": "① 근거 : {ev} vs 예산 {b}회",
    "constraint : {c}": "제약 : {c}",
    "① candidate count": "① 후보 수",
    "② learnability": "② 학습가능성",
    "③ discriminability": "③ 판별력",
    "④ replicates": "④ 반복 측정",
    "→ recommendation {r}": "→ 추천 {r}",
    "LOCKED": "잠김",
    "available": "가능",
    "[caution] this report was force-generated with requirements unmet.":
        "[주의] 이 리포트는 요건 미달 상태에서 강제로 생성됐다.",
}
