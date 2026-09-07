# -*- coding: utf-8 -*-
"""Korean for app.py · ui/main_window.py · ui/start_screen.py · ui/stepper.py · ui/tab_report.py · ui/widgets/. Keys are the English strings as written in the code (core/i18n.py)."""

KO: dict[str, str] = {
    # ── app.py — crash dialog, selftest, splash ──────────────────────────
    "Something went wrong": "오류가 났습니다",
    "The details were written to the file below. Send that file and this can be fixed.\n\n{log}":
        "자세한 내용을 아래 파일에 적었습니다. 이 파일을 보내 주시면 고칠 수 있습니다.\n\n{log}",
    "an example project is missing ({where}: {found})": "예제 프로젝트가 빠졌습니다 ({where}: {found})",
    "the example opened but has too few conditions: {name}": "예제를 열었지만 조건이 부족합니다: {name}",
    "could not open the example: {name}: {why}": "예제를 열지 못했습니다: {name}: {why}",
    "the discriminability calculation produced nothing": "판별력 계산이 값을 내지 못했습니다",
    "the math bundle does not work: {why}": "계산 묶음이 동작하지 않습니다: {why}",
    "OK": "정상",
    "Sequential optimization — requirements first": "순차 최적화 — 조언 전에 요건부터 봅니다",
    "Opening…": "여는 중…",
    "Loading the math engine… (numpy · scipy · scikit-learn)":
        "계산 엔진 불러오는 중… (numpy · scipy · scikit-learn)",
    "Building the screens…": "화면 구성하는 중…",
    "Opening the project…": "프로젝트 여는 중…",

    # ── ui/start_screen.py ───────────────────────────────────────────────
    "Enter your measurements and it tells you what to measure next —\nand whether that advice can be trusted at all.":
        "측정한 값을 넣으면 다음에 잴 조건을 알려 주고,\n그 조언을 믿어도 되는지까지 알려 줍니다.",
    "Start a new project": "새 프로젝트로 시작",
    "Define your variables and objective, then draw the first measurement points.":
        "변수와 목표를 정하고, 첫 측정 지점을 뽑는 것부터 시작합니다.",
    "Open an example  —  Synthetic annealing (crystallinity)": "예제 열어 보기  —  모의 열처리 (결정성)",
    "Simulated data, 42 runs (temperature × time). This one <b>passes all four requirements and yields a recommendation</b>, so you can see what the next condition looks like and why.":
        "가상 데이터 42회 (온도 × 시간). 네 요건을 <b>모두 통과해 추천이 나오는</b> 예제라, 다음에 잴 조건이 어떻게 나오고 왜 그런지 볼 수 있습니다.",
    "Open an example  —  P3HT:CNT conductivity": "예제 열어 보기  —  P3HT:CNT 전도도",
    "Real published measurements of a thin-film composite (<i>Adv. Funct. Mater.</i> 2021, public dataset). Watch the gate pass and a recommendation come out — or lock, once you thin the data.":
        "박막 복합재의 실제 공개 측정값입니다 (<i>Adv. Funct. Mater.</i> 2021, 공개 데이터셋). 관문을 통과해 추천이 나오는 모습과, 데이터를 줄이면 잠기는 모습을 함께 볼 수 있습니다.",
    "Open an example  —  {name}": "예제 열어 보기  —  {name}",
    "Open a saved project": "저장한 프로젝트 열기",
    "Open a .seqopt file you made earlier.": "전에 만든 .seqopt 파일을 엽니다.",
    "Recent files": "최근 파일",

    # ── ui/main_window.py — tabs · menu · header ─────────────────────────
    "Setup": "설정",
    "Diagnose": "진단",
    "Model": "모델",
    "Recommend": "추천",
    "Report": "리포트",
    "Help": "도움말",
    "seqopt — sequential optimization": "seqopt — 순차 최적화",
    "File": "파일",
    "Open…": "열기…",
    "Save": "저장",
    "Save as…": "다른 이름으로 저장…",
    "Import data…": "데이터 가져오기…",
    "Start screen": "시작 화면",
    "Language": "언어",
    "Untitled project": "이름 없는 프로젝트",
    "not saved yet": "아직 저장 안 됨",
    "{file} · modified": "{file} · 수정됨",
    "{file} · saved": "{file} · 저장됨",
    "measured <b>{used}</b> / budget {total}": "측정 <b>{used}</b> / 예산 {total}회",
    "measured <b style='color:{c}'>{used}</b> / budget {total} · <span style='color:{c}'>over</span>":
        "측정 <b style='color:{c}'>{used}</b> / 예산 {total}회 · <span style='color:{c}'>초과</span>",
    " · over budget": " · 예산 초과",
    "There are more measurements than the planned budget. Fix the budget on the Setup tab.":
        "이미 잰 측정이 계획 예산보다 많습니다. 설정 탭에서 예산을 실제에 맞게 고치세요.",
    "Preparing the {name} screen…": "{name} 화면을 준비하는 중입니다…",

    # ── ui/main_window.py — status bar · gate badges · files ─────────────
    "requirements": "요건",
    "requirements —": "요건 —",
    "candidates": "후보",
    "learnability": "학습가능성",
    "recommendation LOCKED": "추천 잠김",
    "recommendation available": "추천 가능",
    "Enter measurements and the requirements get judged.": "측정값을 넣으면 요건을 판정합니다.",
    "Diagnosis needs at least 2 conditions.": "조건이 2개 이상이어야 진단할 수 있습니다.",
    "⏳ computing…": "⏳ 계산 중…",
    "discriminability {t}s · ⏳ learnability…": "판별력 {t}s · ⏳ 학습가능성 계산 중…",
    "✓ diagnosis done · learnability {t}s": "✓ 진단 완료 · 학습가능성 {t}s",
    "computation failed": "계산 실패",
    "Diagnosis failed: {why}": "진단 실패: {why}",
    "<b>Next</b> — {action}": "<b>다음에 할 일</b> — {action}",
    "There are unsaved changes": "저장하지 않은 변경이 있습니다",
    "Save them?": "저장할까요?",
    "Open project": "프로젝트 열기",
    "Save project": "프로젝트 저장",
    "Projects (*{ext})": "프로젝트 (*{ext})",
    "Could not open": "열지 못했습니다",
    "Could not save": "저장하지 못했습니다",
    "Saved — {path}": "저장했습니다 — {path}",
}
