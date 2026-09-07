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
}
