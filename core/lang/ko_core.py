# -*- coding: utf-8 -*-
"""Korean for core/spec.py · core/project.py · core/dataset.py · core/design.py. Keys are the English strings as written in the code (core/i18n.py)."""

KO: dict[str, str] = {

    # ── core/project.py · core/design.py ──────────────────────────────────
    "New project": "새 프로젝트",
    "Unknown project file version: {found} (this program writes {ours})":
        "모르는 프로젝트 파일 버전입니다: {found} (이 프로그램이 쓰는 버전은 {ours} 입니다)",
    "No point satisfying the constraint {what} could be found": "제약 {what} 을 만족하는 점을 찾지 못했습니다",

    # ── core/spec.py — variable and sum-constraint validation ─────────────
    "{name}: a categorical variable needs levels": "{name}: 범주형 변수에는 값 목록이 필요합니다",
    "{name}: min and max are required": "{name}: 최소·최대가 필요합니다",
    "{name}: min ({lo}) must be < max ({hi})": "{name}: 최소({lo}) < 최대({hi}) 여야 합니다",
    "{name}: a step is only for continuous variables": "{name}: 간격은 연속형 변수에만 둡니다",
    "{name}: the step must be > 0": "{name}: 간격은 0보다 커야 합니다",
    "{name}: step ({step}) is larger than the range ({span})": "{name}: 간격({step})이 범위({span})보다 큽니다",
    "A sum constraint needs at least 2 variables": "합 제약은 변수 2개 이상에 겁니다",
    "The same variable appears twice in the sum constraint": "합 제약에 같은 변수가 두 번 들어 있습니다",
    "The constraint names variables that do not exist: {names}": "제약이 없는 변수를 가리킵니다: {names}",
    "A sum constraint cannot include categorical variables: {names}": "범주형 변수에는 합 제약을 걸 수 없습니다: {names}",
    "A sum of {total} cannot be made from these ranges (minimum sum {lo} ~ maximum sum {hi})":
        "합 {total} 은 이 범위들로 만들 수 없습니다 (최소 합 {lo} ~ 최대 합 {hi})",
    "Sum ≤ {total} cannot be made from these ranges (minimum sum {lo})":
        "합 ≤ {total} 은 이 범위들로 만들 수 없습니다 (최소 합 {lo})",
    "The variables of a sum = constraint must share the same step": "합 = 제약의 변수들은 간격이 서로 같아야 합니다",
    "A sum of {total} cannot be made with step {step} (it must be a whole number of steps above the minimum sum {lo})":
        "합 {total} 은 간격 {step} 으로 만들 수 없습니다 (최소 합 {lo} 에서 간격의 정수배여야 합니다)",
    "infinitely many candidates — continuous variable(s) {names} have no step":
        "후보 무한 — 연속 변수 {names} 에 간격 없음",
    " (constraint {what})": " (제약 {what})",
    "{cap} candidate conditions or more ({parts})": "후보 조건 {cap}개 이상 ({parts})",
    ", within constraint {what}": ", 제약 {what} 안",
    "{n} candidate conditions ({parts})": "후보 조건 {n}개 ({parts})",
}
