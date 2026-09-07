# -*- coding: utf-8 -*-
"""Korean for ui/tab_setup.py · ui/tab_data.py · ui/import_wizard.py · core/importer.py · core/profile.py. Keys are the English strings as written in the code (core/i18n.py)."""

KO: dict[str, str] = {
    # --- ui/tab_setup.py — header, variable table ---
    "Setup — what you can turn, and what should improve": "설정 — 무엇을 돌리고 무엇을 좋게 할 것인가",
    "Everything defined here is the premise of every other screen. Invalid values never get in.":
        "여기서 정한 것이 다른 모든 화면의 전제입니다. 틀린 값은 애초에 들어가지 않습니다.",
    "Project name": "프로젝트 이름",
    "Input variables — the knobs you can turn": "입력변수 — 내가 돌릴 수 있는 손잡이",
    "Design variables only. Loads and ambient values a device merely experiences are not knobs.":
        "설계변수만 넣습니다. 소자가 그저 겪는 부하·환경값은 손잡이가 아닙니다.",
    "No variables yet.  Press <b>\"+ Add variable\"</b> to start.<br>e.g. — name <b>power</b> · unit <b>W</b> · type <b>continuous</b> · min <b>150</b> · max <b>200</b>":
        "아직 변수가 없습니다.  <b>「+ 변수 추가」</b> 를 눌러 시작하세요.<br>예 — 이름 <b>power</b> · 단위 <b>W</b> · 형 <b>연속형</b> · 최소 <b>150</b> · 최대 <b>200</b>",
    "continuous": "연속형",
    "integer": "정수형",
    "categorical": "범주형",
    "name": "이름",
    "unit": "단위",
    "type": "형",
    "min": "최소",
    "max": "최대",
    "step": "간격",
    "Variable name. Tables, figures and reports use this name.": "변수 이름. 표·그림·리포트에 이 이름으로 나옵니다.",
    "Unit. May be left empty.": "단위. 비워 둬도 됩니다.",
    "continuous = any value · integer = 3, 4, 5… · categorical = a fixed set":
        "연속형 = 아무 값이나 · 정수형 = 3, 4, 5… · 범주형 = 정해진 몇 가지",
    "The smallest value this knob can be set to": "이 변수를 돌릴 수 있는 가장 작은 값",
    "The largest value this knob can be set to": "이 변수를 돌릴 수 있는 가장 큰 값",
    "The spacing the instrument can actually be set to (continuous only). e.g. 10 if the power supply only moves in 10 W steps.\nLeave it empty and any value can be chosen (infinitely many candidates).\nRequirement ① compares the candidate count on this grid with the budget.":
        "장비가 실제로 맞출 수 있는 간격 (연속형만). 예: 전원이 10 W 단위로만 돌아가면 10.\n비우면 아무 값이나 고를 수 있는 것으로 봅니다 (후보 무한).\n요건 ① 은 이 간격으로 센 후보 수를 예산과 비교합니다.",
    "+ Add variable": "+ 변수 추가",
    "− Remove selected": "− 선택 삭제",
    "Fill ranges from data": "데이터에서 범위 채우기",
    "Fills min/max from the measurements you already entered.\nTyping them by hand is tedious, and a typo sends the\nrecommendation somewhere absurd.":
        "이미 넣은 측정값의 최소·최대로 범위를 채웁니다.\n손으로 하나씩 적는 것은 성가시고, 잘못 적으면\n추천이 엉뚱한 곳으로 갑니다.",
    # --- ui/tab_setup.py — sum constraint ---
    "Sum constraint — variables with a fixed total (optional)": "합 제약 — 합이 정해진 변수 (선택)",
    "Turn on when a few variables must add up to a fixed total, as a composition does. The initial design, the candidates and the recommendations all stay inside it.":
        "조성처럼 몇 변수의 합이 정해져 있으면 켭니다. 초기 설계·후보·추천이 전부 그 안에서만 나옵니다.",
    "Use a sum constraint": "합 제약 사용",
    "e.g. A + B + C = 100 (%)  ·  additive1 + additive2 ≤ 5 (wt%)":
        "예: A + B + C = 100 (%)  ·  첨가제1 + 첨가제2 ≤ 5 (wt%)",
    "Variables in the sum (2 or more)": "합에 들어갈 변수 (2개 이상)",
    "The constraint applies to the sum of the checked variables. Categorical variables cannot take part.":
        "체크한 변수들의 합에 제약을 겁니다. 범주형은 걸 수 없습니다.",
    "The sum is": "합이",
    "= exactly": "= 정확히",
    "≤ at most": "≤ 최대",
    "The total. For a composition, 100 (%) or 1.": "합의 값. 조성이면 100 (%) 또는 1.",
    "check at least 2 variables to put in the sum": "합에 들어갈 변수를 2개 이상 체크하세요",
    "constraint: <b>{rule}</b>": "제약: <b>{rule}</b>",
    "{n} measured rows already violate this constraint — check that the constraint, and the values, are right.":
        "이미 잰 측정 {n}행이 이 제약을 어깁니다 — 제약이 맞는지, 값이 맞는지 확인하세요.",
    # --- ui/tab_setup.py — response, budget ---
    "Response — the value you want to improve": "출력변수 — 좋아지길 바라는 값",
    "Exactly one. Improving several values at once is outside this tool.":
        "하나만 정합니다. 여러 값을 동시에 좋게 하는 것은 이 도구 밖입니다.",
    "Maximize — bigger is better": "최대화 — 클수록 좋다",
    "Minimize — smaller is better": "최소화 — 작을수록 좋다",
    "Work in log scale": "로그 변환해서 다루기",
    "Turn on when the response spans orders of magnitude (say 1e-4 to 1e2).\nThe setting is saved with the project and written into the report — it changes the verdicts.":
        "응답이 자릿수로 걸쳐 있을 때(예: 1e-4 ~ 1e2) 켭니다.\n설정은 프로젝트에 저장되고 리포트에도 적힙니다 — 판정이 달라지기 때문입니다.",
    "Name": "이름",
    "Unit": "단위",
    "Goal": "목표",
    "The response spans two or more orders of magnitude — <b>turning on the log scale is the better choice</b> (Advanced).":
        "응답이 두 자릿수 이상 걸쳐 있습니다 — <b>로그 변환을 켜는 편이 낫습니다</b> (고급 설정).",
    "Working in log10 scale. The report says so too.": "로그(log10) 변환해서 다룹니다. 리포트에도 적힙니다.",
    "Budget — how many measurements in total": "예산 — 총 몇 번 잴 것인가",
    "This count against the condition count decides whether optimization means anything at all.":
        "이 횟수와 조건 수를 비교해 최적화가 뜻이 있는지부터 봅니다.",
    "Total measurements": "총 측정 횟수",
    "Initial design points": "초기 설계 점 수",
    "Generate initial design → export CSV": "초기 설계 생성 → CSV 내보내기",
    "Draws the first measurement points space-filling (maximin LHS).\nMeasured on a grid, curved terrain looks flat — and more replicates do not fix that.":
        "공간을 고루 채우는 방식(maximin LHS)으로 첫 측정 지점을 뽑습니다.\n격자로 재면 굽은 지형이 평평해 보이고, 반복을 늘려도 해결되지 않습니다.",
    "The first batch draws <b>{n} points</b> space-filling ({rec} recommended — 25–30% of the budget).":
        "첫 배치는 <b>{n}점</b>을 공간을 고루 채우도록 뽑습니다 (예산의 25~30%인 {rec}점 권장).",
    "initial design: {n} points": "초기 설계 {n}점",
    "Export initial design": "초기 설계 내보내기",
    "CSV (*.csv)": "CSV 파일 (*.csv)",
    "Exported": "내보냈습니다",
    "Saved {n} points.\nMeasure them, then fill in the values on the Data tab.":
        "{n}점을 저장했습니다.\n측정한 뒤 데이터 탭에서 값을 채우세요.",
    # --- ui/tab_setup.py — validation messages ---
    "No measurements": "측정값이 없습니다",
    "Enter values on the Data tab first, then the ranges can be filled.":
        "데이터 탭에서 값을 먼저 넣으면 범위를 채울 수 있습니다.",
    "row {row}: the name is empty": "{row}행: 이름이 비었습니다",
    "{name}: categorical variables cannot be built on this screen yet — use continuous or integer":
        "{name}: 범주형은 아직 이 화면에서 만들 수 없습니다 — 연속형이나 정수형을 쓰세요",
    "{name}: min/max is not a number": "{name}: 최소·최대가 숫자가 아닙니다",
    "{name}: min ({lo}) must be < max ({hi})": "{name}: 최소({lo}) < 최대({hi}) 여야 합니다",
    "{name}: the step is not a number": "{name}: 간격이 숫자가 아닙니다",
    "duplicate names: {names}": "이름이 겹칩니다: {names}",
    "define at least one input variable": "입력변수를 최소 1개 정의하세요",
    "at most 10 input variables (currently {n})": "입력변수는 10개까지입니다 (현재 {n}개)",
    "Finish the variable definitions first": "변수 정의를 마저 해 주세요",
    "Finish the sum constraint first": "합 제약을 마저 정해 주세요",
    "{where} ≤ budget {budget} — <b>requirement ① unmet</b>: measuring everything is better. A finer step or a wider range gives more candidates.":
        "{where} ≤ 예산 {budget}회 — <b>요건 ① 미달</b>: 전수 측정이 더 낫습니다. 간격을 촘촘히 하거나 범위를 넓히면 후보가 늘어납니다.",
    "{where} — more than the budget of {budget}, so requirement ① passes.":
        "{where} — 예산 {budget}회보다 많아 요건 ① 은 통과합니다.",
}
