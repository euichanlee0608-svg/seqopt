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
    "✓ learnability {t}s": "✓ 학습가능성 {t}s",
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

    # ── ui/tab_report.py ─────────────────────────────────────────────────
    "Report — leave the whole evidence trail": "리포트 — 근거 일체를 남깁니다",
    "Exports the gate verdict, calculation log, figures and raw-data summary as PDF and text — plus a script that reproduces the same numbers.":
        "요건 판정 · 계산 과정 · 그림 · 원자료 요약을 PDF 와 텍스트로 내보냅니다. 같은 숫자를 다시 내는 스크립트도 함께 나옵니다.",
    "Build report": "리포트 만들기",
    "Press \"Build report\" to assemble the full evidence from the current data.":
        "‘리포트 만들기’ 를 누르면 지금 데이터로 근거 일체를 만듭니다.",
    "Export": "내보내기",
    "PDF report": "PDF 리포트",
    "Gate verdict + calculation log + figures + raw-data summary.\nEmbeds the font, so it renders the same on any PC.":
        "요건 판정 + 계산 과정 + 그림 + 원자료 요약.\n글꼴을 파일 안에 넣으므로 어느 PC 에서도 같게 보입니다.",
    "Calculation log (txt)": "계산 로그 (txt)",
    "Every number's formula and intermediate values. Followable by hand.":
        "모든 수치의 산출식과 중간값. 손으로 따라갈 수 있습니다.",
    "Reproduction script (py)": "재현 스크립트 (py)",
    "This one file reproduces the same numbers.": "이 파일 하나로 같은 숫자를 다시 냅니다.",
    "Calculation-log preview": "계산 과정 미리보기",
    "No measurements": "측정값이 없습니다",
    "Enter values on the Data tab first.": "데이터 탭에서 값을 먼저 넣으세요.",
    "Computing… (includes learnability LOOCV, so many conditions take tens of seconds)":
        "계산 중입니다… (학습가능성 LOOCV 를 포함하므로 조건이 많으면 수십 초 걸립니다)",
    "<b>Ready.</b> {n} usable conditions · {m} measurements · {what} {verdict}":
        "<b>준비됐습니다.</b> 유효 조건 {n}개 · 측정 {m}회 · {what} {verdict}",
    "Requirements unmet — the PDF cover and every page get a \"{stamp}\" stamp.":
        "요건 미달 상태입니다 — PDF 표지와 모든 쪽에 ‘{stamp}’ 도장이 찍힙니다.",
    "Could not build the report — {why}": "리포트를 만들지 못했습니다 — {why}",
    "Could not build the PDF": "PDF 를 만들지 못했습니다",
    "Saved": "저장했습니다",
    "PDF (*.pdf)": "PDF (*.pdf)",
    "Text (*.txt)": "텍스트 (*.txt)",
    "Python (*.py)": "파이썬 (*.py)",
    "{path}\n\nRun `python {name}` inside the seqopt folder\nand the report's numbers come out again.":
        "{path}\n\nseqopt 폴더 안에서 `python {name}` 으로 돌리면\n리포트와 같은 숫자가 다시 나옵니다.",

    # ── ui/stepper.py — the four steps, why a step is blocked, what to do next ──
    "Define the variables and the objective": "변수와 목표를 정합니다",
    "Enter your measurements": "측정값을 넣습니다",
    "See whether this data can be used": "이 데이터를 써도 되는지 봅니다",
    "Get the next condition to measure": "다음에 잴 조건을 받습니다",
    "Define your input variables on the Setup tab first.": "먼저 설정 탭에서 입력 변수를 정의하세요.",
    "Diagnosis needs at least 2 conditions. Enter measurements on the Data tab.":
        "조건이 2개 이상이어야 진단할 수 있습니다. 데이터 탭에서 측정값을 넣으세요.",
    "Drawing the response surface needs at least 3 conditions.": "응답면을 그리려면 조건이 3개 이상이어야 합니다.",
    "Recommendations become available once diagnosis has run.": "진단이 끝나야 추천을 낼 수 있습니다.",
    "A report needs at least one measurement.": "측정값이 있어야 리포트를 만들 수 있습니다.",
    "Define at least one input variable — \"+ Add variable\"": "입력 변수를 1개 이상 정의하세요 — 「+ 변수 추가」",
    "Enter measurements — import a file · Ctrl+V · add rows": "측정값을 넣으세요 — 파일 가져오기 · Ctrl+V · 행 추가",
    "Diagnosis needs at least 2 conditions": "조건이 2개 이상이어야 진단할 수 있습니다",
    "Diagnosing…": "진단하는 중입니다…",
    "Requirements unmet — see the prescription on the Diagnose tab": "요건 미달입니다 — 진단 탭의 처방을 보세요",
    "Check the requirements": "요건을 확인하세요",
    "1 recommended condition is waiting on the Data tab (gray row) — measure it and fill in the value, and it enters the next diagnosis":
        "데이터 탭에 추천 조건 1개가 기다리고 있습니다 (회색 행) — 재서 값을 채우면 다음 진단에 들어갑니다",
    "{n} recommended conditions are waiting on the Data tab (gray rows) — measure them and fill in the values, and they enter the next diagnosis":
        "데이터 탭에 추천 조건 {n}개가 기다리고 있습니다 (회색 행) — 재서 값을 채우면 다음 진단에 들어갑니다",
    "Requirements met — get your next candidates": "요건을 통과했습니다 — 다음 후보를 받으세요",

    # ── ui/widgets/ — the "Advanced" fold, the step rail's state tags ────
    "Advanced": "고급 설정",
    "locked": "잠김",
    "next": "다음",
}
