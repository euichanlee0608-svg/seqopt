# -*- coding: utf-8 -*-
"""Korean for ui/tab_help.py. Keys are the English strings as written in the code (core/i18n.py)."""

KO: dict[str, str] = {
    "What is this program": "이 프로그램은 무엇인가",
    "overview start introduction": "개요 시작 소개",
    "<b>Enter your measurements and it tells you which condition to "
    "measure next — and whether that advice can be trusted at all.</b>":
        "<b>측정한 값을 넣으면 다음에 어떤 조건을 재야 하는지 알려 주고, "
        "그 조언을 믿어도 되는지까지 같이 알려 주는 프로그램</b>입니다.",
    "The second half is the point. Plenty of tools already suggest the "
    "next condition. This one <b>checks the advice's reliability first, "
    "and refuses to advise when the data falls short.</b>":
        "뒷문장이 핵심입니다. 다음 조건만 알려 주는 도구는 이미 많습니다. "
        "이 프로그램은 <b>조언의 신뢰도를 먼저 검사하고, 미달이면 조언을 내주지 않습니다.</b>",
    "<h3>Why it was built this way</h3>": "<h3>이렇게 만든 이유</h3>",
    "While validating this method, the same question was answered <b>four "
    "times and got it wrong three times.</b> The cause was never a code "
    "bug — it was <b>never asking whether the data could support the "
    "question at all.</b>":
        "이 방법이 쓸 만한지 검증하면서 같은 질문에 <b>네 번 답했고 세 번 틀렸습니다.</b> "
        "그런데 틀린 이유가 매번 코드 버그가 아니라 <b>‘이 데이터로 그걸 잴 수 있는가’를 안 물어봐서</b>였습니다.",
    "One real lab dataset from that study had a learnability of "
    "R² = −0.272 — worse than always answering the overall mean. Feed it "
    "to an ordinary optimization tool and you get <b>a smooth response "
    "surface and a plausible next candidate anyway.</b> Trust that, and "
    "you spend time and samples on noise.":
        "그 연구에서 실제로 쓴 실험 데이터 하나는 학습가능성 R² = −0.272 였습니다 — "
        "늘 전체 평균으로만 답하는 것보다도 못한 값입니다. 이를 일반적인 최적화 도구에 넣어도 "
        "<b>매끄러운 응답면과 그럴듯한 다음 후보를 내놓습니다.</b> "
        "그걸 믿으면 시간과 시료를 소음에 낭비하게 됩니다.",
    "Why are there so few choices": "왜 고를 것이 이렇게 적나요",
    "simple choices advanced defaults algorithm kernel": "단순함 선택지 고급설정 기본값 알고리즘 커널",
    "Deliberately. Compared with other optimization tools:":
        "일부러 그렇게 만들었습니다. 다른 최적화 도구와 비교하면 이렇습니다.",
    "tool": "도구",
    "what the user must choose": "사용자가 골라야 하는 것",
    "AutoOED": "AutoOED",
    "surrogate · acquisition · multi-objective solver · selection strategy — four dropdowns":
        "대리모델 · 획득함수 · 다목적 solver · 선택전략 — 드롭다운 4개",
    "MADGUI": "MADGUI",
    "ElasticNet / RandomForest / XGBoost · cross-validation scheme":
        "ElasticNet / RandomForest / XGBoost · 교차검증 방식",
    "OPTIMEO": "OPTIMEO",
    "DoE type · model · acquisition": "DoE 종류 · 모델 · 획득함수",
    "<b>this program</b>": "<b>이 프로그램</b>",
    "<b>none</b> — fixed kernel · fixed EI · fixed model":
        "<b>없음</b> — 커널 고정 · EI 고정 · 모델 고정",
    "<h3>Why fixing them is affordable</h3>": "<h3>고정할 수 있는 이유</h3>",
    "<b>Because the gate exists.</b> Other tools hand you choices so you "
    "can wander between models when the data is bad. This program rules "
    "<b>\"changing the model will not help\"</b> — so there is nothing to choose.":
        "<b>관문이 있기 때문입니다.</b> 다른 도구는 데이터가 나쁠 때 사용자가 모델을 바꿔가며 "
        "헤매도록 선택지를 줍니다. 이 프로그램은 <b>‘모델을 바꿔도 소용없다’</b>고 판정해 버리므로 "
        "선택지를 줄 이유가 없습니다.",
    "In the validation study, six model families were tried on a bad "
    "dataset and <b>not one</b> reached R² > 0. Offer a menu there, and "
    "people spend their time hunting for an answer that does not exist.":
        "실제로 검증에서 모델 6종을 전부 돌렸는데 R² > 0 인 것이 하나도 없었습니다. "
        "고를 수 있게 해 놓으면 없는 답을 찾아 시간을 씁니다.",
    "<h3>If you still want to change things</h3>": "<h3>그래도 바꾸고 싶다면</h3>",
    "Unfold <b>\"Advanced ▸\"</b> on each screen — acquisition function, "
    "batch size, target discriminability, log transform and the initial "
    "design size are all there. Not removed. <b>Deferred.</b>":
        "각 화면의 <b>「고급 설정 ▸」</b> 을 펼치면 획득함수·배치 크기·목표 판별력·로그 변환·"
        "초기 설계 점수를 조정할 수 있습니다. 없앤 것이 아니라 <b>미뤄 둔</b> 것입니다.",
    "In what order do I use it": "어떤 순서로 쓰나",
    "order flow workflow first": "순서 흐름 워크플로 처음",
    "<h3>Starting a new experiment</h3>": "<h3>새 실험을 시작할 때</h3>",
    "<b>Setup</b> — define your knobs (inputs), the objective, and the budget":
        "<b>설정</b> — 손잡이(입력변수)와 목표, 예산을 정합니다",
    "<b>Setup → generate initial design</b> — get the first measurement points as CSV":
        "<b>설정 → 초기 설계 생성</b> — 첫 측정 지점을 CSV 로 받습니다",
    "Measure them in the lab": "실험실에서 측정합니다",
    "<b>Data</b> — enter the values (paste · import · type)":
        "<b>데이터</b> — 측정값을 넣습니다 (붙여넣기·가져오기·직접 입력)",
    "<b>Diagnose</b> — check the four requirements ← <b>this is the fork</b>":
        "<b>진단</b> — 요건 4가지를 확인합니다 ← <b>여기가 갈림길</b>",
    "Pass → get the next condition on <b>Recommend</b>, and repeat 4–6":
        "통과하면 <b>추천</b> 에서 다음 조건을 받고, 4~6 을 반복합니다",
    "Fail → fix the data first, following the <b>prescription</b> on the Diagnose tab":
        "미달이면 진단 탭의 <b>처방</b> 대로 먼저 데이터를 고칩니다",
    "<h3>Diagnosing a spreadsheet you already have</h3>": "<h3>이미 있는 엑셀을 진단할 때</h3>",
    "<b>Data → import from file</b> and map the columns":
        "<b>데이터 → 파일에서 가져오기</b> 로 열 매핑",
    "Read the verdict table on <b>Diagnose</b>": "<b>진단</b> 에서 판정표를 봅니다",
    "Keep the evidence as a PDF with <b>Report</b>": "<b>리포트</b> 로 근거를 PDF 로 남깁니다",
    "Help — the questions this tool is likely to raise": "도움말 — 이 도구에 대해 생길 만한 질문들",
    "Each topic ends with the code locations that back its explanation.":
        "각 항목 끝에는 그 설명의 근거가 되는 코드 위치가 적혀 있습니다.",
    "Search  (e.g. discriminability, locked, excel, slow)": "검색  (예: 판별력, 잠김, 엑셀, 느림)",
    "The README covers installation and the Windows build.": "설치와 윈도우용 빌드는 README 에 있습니다.",
    "Nothing matches '{q}'.": "'{q}'에 맞는 항목이 없습니다.",
    "<h3>Backing code and documents</h3><ul class='src'>{items}</ul>":
        "<h3>근거 코드·문서</h3><ul class='src'>{items}</ul>",
}
