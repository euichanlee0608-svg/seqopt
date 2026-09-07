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
    "The four requirements — what and why": "요건 4가지 — 무엇을 왜 보는가",
    "gate requirements verdict locked": "관문 요건 판정 잠김",
    "All four must pass before recommendations open. "
    "A single <b>×</b> locks them.": "네 가지를 모두 통과해야 추천이 열립니다. 하나라도 <b>×</b> 면 잠깁니다.",
    "requirement": "요건",
    "what it checks": "무엇을 보는가",
    "when it fails": "미달이면",
    "candidate count": "후보 수",
    "are there more <b>conditions to choose from</b> in the design space than budget":
        "설계 공간에서 <b>고를 수 있는 조건 수</b>가 예산보다 많은가",
    "measuring everything is better (the gain from optimizing is zero in principle). "
    "A finer step or a wider range gives more candidates":
        "전수 측정이 낫습니다 (최적화의 이득이 원리적으로 0). 간격을 촘촘히 하거나 범위를 넓히면 후보가 늘어납니다",
    "surface learnability": "응답면 학습가능성",
    "is the model learning the terrain (LOOCV R² > 0)": "모델이 지형을 배우고 있는가 (LOOCV R² > 0)",
    "changing the model will not help. The data is the problem": "모델을 바꿔도 소용없습니다. 데이터가 문제입니다",
    "discriminability": "판별력",
    "do condition differences exceed the measurement wobble": "조건 간 차이가 측정 흔들림보다 큰가",
    "raise the replicate count": "반복 측정을 늘려야 합니다",
    "replicates": "반복 측정",
    "has the same condition ever been re-measured": "같은 조건을 다시 잰 적이 있는가",
    "the wobble's size is unknowable (a warning — it does not lock)":
        "흔들림 크기 자체를 알 수 없습니다 (경고만, 잠그지는 않음)",
    "<b>Any of ①②③ failing locks the gate.</b> ④ is a warning.":
        "<b>①②③ 중 하나라도 미달이면 잠깁니다.</b> ④ 는 경고입니다.",
    "① counts <b>not the conditions already measured</b> but the Setup tab's ranges · "
    "steps · sum constraint — integer, categorical and stepped variables multiply their "
    "level counts, and a single continuous variable without a step makes the count "
    "infinite, which passes. The count is always shown under the variable table on the Setup tab.":
        "① 은 <b>이미 측정한 조건 수가 아니라</b> 설정 탭의 범위·간격·합 제약으로 셉니다 — "
        "정수형·범주형·간격이 있는 변수는 각각의 값 개수를 곱하고, 간격이 없는 연속형 변수가 "
        "하나라도 있으면 후보가 무한이 되어 통과합니다. 그 수는 설정 탭 변수표 아래에 항상 표시됩니다.",
    "Learnability R² is slow, so it runs in the background. "
    "<b>The lock holds while it computes</b> — the unknown is never counted as a pass.":
        "학습가능성 R² 는 계산이 오래 걸려 백그라운드로 돕니다. "
        "<b>계산 중에도 잠금은 유지됩니다</b> — 아직 모르는 것을 통과로 치지 않습니다.",
    "What is discriminability (D)": "판별력(D)이란 무엇인가",
    "discriminability D sigma noise wobble replicates bootstrap": "판별력 D 시그마 노이즈 흔들림 반복측정 부트스트랩",
    "<b>The difference that changing the condition makes</b>, divided by "
    "<b>the wobble of re-measuring the same condition.</b> Above 1 means "
    "\"neighboring conditions can be told apart\".":
        "<b>조건을 바꿔서 생기는 차이</b>를 <b>같은 조건을 다시 재서 생기는 흔들림</b>으로 나눈 값입니다. "
        "1보다 크면 ‘옆 조건과 구별할 수 있다’는 뜻입니다.",
    "<pre>σw = √( Σ(n−1)·var(replicates per condition) / Σ(n−1) )   ← conditions with ≥2 replicates only\n"
    "σb = std( condition means , ddof=1 )\n"
    "D(n) = σb / (σw / √n)</pre>":
        "<pre>σw = √( Σ(n−1)·var(replicates per condition) / Σ(n−1) )   ← 반복이 2회 이상인 조건만\n"
        "σb = std( condition means , ddof=1 )\n"
        "D(n) = σb / (σw / √n)</pre>",
    "<b>An analogy</b> — telling apart two people who differ by 1 kg, on a "
    "scale that jumps ±2 kg per reading. No amount of cleverness helps. "
    "It is the scale's fault.":
        "<b>비유</b> — 잴 때마다 ±2 kg 씩 튀는 저울로 1 kg 차이 나는 두 사람을 구별하려는 것과 같습니다. "
        "아무리 똑똑해도 못 합니다. 저울 탓입니다.",
    "<h3>Why the point estimate is not enough</h3>": "<h3>왜 점추정만 보지 않는가</h3>",
    "Conditions are resampled with replacement and D is recomputed "
    "<b>4000 times</b> for a 95% interval. When that interval straddles "
    "the threshold of 1.0, the screen says <b>\"undecided\"</b>.":
        "조건을 복원추출로 다시 뽑아 D 를 <b>4000번</b> 다시 계산해 95% 구간을 냅니다. "
        "그 구간이 임계값 1.0 을 걸치면 화면에 <b>‘판정불가’</b>라고 표시됩니다.",
    "The validation study hit exactly this case — D = 1.03 looked passed, "
    "but the interval was [0.49, 1.80], so <b>neither passed nor failed "
    "could honestly be claimed.</b>":
        "그 검증 연구가 정확히 이 경우였습니다 — D = 1.03 이라 겉보기엔 통과한 듯했지만 "
        "구간이 [0.49, 1.80] 이라 <b>통과했다고도 못 했다고도 말할 수 없었습니다.</b>",
    "Where do the thresholds 1 · 2 · 3.5 come from": "기준값 1 · 2 · 3.5 는 어디서 왔나",
    "threshold recommended basis prescription replicates how many": "기준값 권장 근거 처방 반복측정 몇번",
    "The discriminability gauge carries three marks. <b>The gate is 1, "
    "alone</b>; the other two are marks for reading \"how comfortable\". "
    "None of them is arbitrary.":
        "판별력 눈금에는 세 가지 기준이 있습니다. <b>관문은 1 하나뿐</b>이고, "
        "나머지 둘은 ‘얼마나 넉넉한가’를 읽는 눈금입니다. 어느 것도 임의로 정한 숫자가 아닙니다.",
    "mark": "기준",
    "name": "이름",
    "meaning": "뜻",
    "basis": "근거",
    "gate (minimum)": "관문 (최소)",
    "difference = wobble": "차이 = 흔들림",
    "Follows from the definition. With σb &lt; σw, the difference made by "
    "changing conditions is smaller than the wobble of re-measuring — "
    "rankings may be noise.":
        "판별력의 정의 자체에서 나오는 결과입니다. σb &lt; σw 이면 조건을 바꿔 생긴 차이가 "
        "같은 조건을 다시 잰 흔들림보다 작다는 뜻이므로 — 순위가 잡음일 수 있습니다.",
    "recommended": "권장",
    "difference ≈ wobble × 2": "차이 ≈ 흔들림 × 2",
    "Two means about two standard errors apart — the usual statistical "
    "boundary for \"different\" (95%, z ≈ 1.96).":
        "두 평균이 표준오차의 2배만큼 떨어져 있다는 뜻입니다 — 통계에서 ‘다르다’고 보는 "
        "통상의 경계(95%, z ≈ 1.96)와 같습니다.",
    "comfortable": "넉넉",
    "difference ≈ wobble × 3.5": "차이 ≈ 흔들림 × 3.5",
    "Matches measurement-system analysis (AIAG MSA), where a usable "
    "instrument needs ndc = 1.41·σb/σw ≥ 5 distinct categories.":
        "측정시스템분석(AIAG MSA)에서 쓸 만한 측정기의 기준인 구분 범주 수 "
        "ndc = 1.41·σb/σw ≥ 5 와 일치합니다.",
    "<h3>How the prescription table is computed</h3>": "<h3>처방 표는 어떻게 계산하나</h3>",
    "With n replicates per condition the mean's wobble shrinks to σw/√n, "
    "so D(n) = σb/(σw/√n). Solving for n gives <b>n = ⌈(target D · σw / σb)²⌉</b>. "
    "\"Extra runs\" sums, per condition, the gap between its current "
    "replicates and n.":
        "조건당 n 회 측정하면 평균의 흔들림은 σw/√n 으로 줄어들어 D(n) = σb/(σw/√n) 이 됩니다. "
        "이를 n 에 대해 풀면 <b>n = ⌈(목표 D · σw / σb)²⌉</b> 입니다. "
        "‘추가 측정’은 조건마다 현재 반복 횟수와 n 의 차이를 더한 값입니다.",
    "<b>Caution</b> — the calculation assumes <b>σw stays what it is now.</b> "
    "More replicates change the σw estimate itself, so measure up to the "
    "recommended row and <b>diagnose again</b>.":
        "<b>주의</b> — 이 계산은 <b>σw 가 지금 그대로 유지된다고 가정합니다.</b> "
        "반복을 늘리면 σw 추정치 자체가 바뀌므로, 권장 줄까지 측정한 뒤 <b>다시 진단하세요</b>.",
    "<h3>And the nugget-ratio threshold of 0.3?</h3>": "<h3>너깃비 기준 0.3 은?</h3>",
    "This tool calls a surface rough above a nugget ratio of 0.3. The widely "
    "used geostatistics scale (Cambardella 1994) — &lt;0.25 strong spatial "
    "structure · 0.25–0.75 moderate · &gt;0.75 weak — is shown alongside "
    "on the Diagnose tab.":
        "이 도구는 너깃비가 0.3 을 넘으면 거친 응답면으로 봅니다. 널리 쓰이는 지구통계학 눈금"
        "(Cambardella 1994) — &lt;0.25 강한 공간구조 · 0.25–0.75 보통 · &gt;0.75 약한 구조 — "
        "도 진단 탭에 함께 표시됩니다.",
    "What does a negative learnability R² mean": "학습가능성 R² 가 음수면 무슨 뜻인가",
    "R2 learnability LOOCV negative surface": "R2 학습가능성 LOOCV 음수 응답면",
    "Each condition is left out in turn, the model is fitted on the rest, "
    "and the left-out condition is predicted (LOOCV). "
    "R² = 1 − SS_res/SS_tot.":
        "조건을 하나씩 빼고 나머지로 모델을 학습해 그 조건을 예측합니다(LOOCV). "
        "R² = 1 − SS_res/SS_tot 입니다.",
    "<b>R² ≤ 0 means worse than always answering the overall mean.</b> "
    "The model has learned nothing.":
        "<b>R² ≤ 0 은 ‘전체 평균만 답하기’보다 나쁘다</b>는 뜻입니다. 모델이 아무것도 못 배운 상태입니다.",
    "<h3>Why changing the model will not help</h3>": "<h3>왜 모델을 바꿔도 소용없나</h3>",
    "The validation study ran six families (constant, linear, quadratic, GP, "
    "RF, …) on such a dataset, and <b>not one reached R² > 0.</b> When the "
    "signal is not in the data, no model can learn it.":
        "검증에서 6종(상수·선형·2차·GP·RF 등)을 전부 돌렸는데 <b>R² > 0 인 것이 하나도 없었습니다.</b> "
        "배울 신호가 데이터에 없으면 어떤 모델도 배울 수 없습니다.",
    "Look at the scatter on the <b>Validation tab</b>. Points clustering "
    "around the red \"always answer the mean\" line instead of the diagonal — "
    "that is what R² < 0 looks like.":
        "<b>검증 탭의 산점도</b>를 보세요. 점이 대각선이 아니라 빨간 ‘전체 평균선’ 주위에 "
        "흩어져 있으면 그게 R² < 0 의 모습입니다.",
    "Nugget ratio · terrain roughness": "너깃비 · 지형 거칠기",
    "nugget sill semivariogram terrain roughness": "너깃 문턱값 세미베리오그램 지형 거칠기",
    "A semivariogram is built from condition-pair distances and value "
    "differences: how much difference survives even at near-zero "
    "distance (<b>the nugget</b>), as a share of the height reached far "
    "away (<b>the sill</b>).":
        "조건 쌍의 거리와 값 차이로 세미베리오그램을 그려, 거리가 거의 0 일 때도 남는 차이"
        "(<b>너깃</b>)가 멀리서 도달하는 높이(<b>문턱값</b>)의 몇 %인지를 봅니다.",
    "<pre>nugget ratio = nugget / sill      &gt; 0.3 counts as a 'rough surface'</pre>":
        "<pre>nugget ratio = nugget / sill      &gt; 0.3 이면 '거친 응답면'</pre>",
    "A large nugget ratio means <b>most of the visible variation is "
    "measurement wobble.</b> The lab dataset in the validation study sat at "
    "0.489, with a noise share of <b>95%</b>.":
        "너깃비가 크다는 것은 <b>눈에 보이는 변동 대부분이 측정 흔들림</b>이라는 뜻입니다. "
        "그 검증 연구의 실험 데이터는 0.489 였고, 잡음 비중은 <b>95%</b>였습니다.",
    "<h3>Caution — it does not predict the ordering</h3>": "<h3>주의 — 순서까지 맞히지는 못합니다</h3>",
    "The original write-up claimed the nugget-ratio ordering matches the R² "
    "ordering exactly. Checked against the actual values, <b>it does not "
    "hold</b> (one dataset has the lower nugget ratio and the lower R²). "
    "What does hold is the <b>separation between the smooth and the rough.</b>":
        "원래 설명에는 ‘너깃비 순서가 R² 순서와 정확히 일치한다’고 되어 있었지만, "
        "실제 값으로 확인해 보니 <b>그렇지 않았습니다</b>(너깃비도 R² 도 함께 낮은 데이터셋이 있었습니다). "
        "성립하는 것은 <b>매끄러운 쪽과 거친 쪽이 갈린다는 분리</b>뿐입니다.",
    "My spreadsheets differ every time": "엑셀 형식이 매번 다른데요",
    "import excel column mapping preset format csv": "가져오기 엑셀 열 매핑 프리셋 형식 csv",
    "Which is why the program does not guess the format. "
    "<b>The original shows on the left, and you assign the columns' "
    "meanings on the right.</b>":
        "그래서 프로그램이 형식을 알아서 짐작하게 하지 않습니다. "
        "<b>왼쪽에 원본을 그대로 보여 주고, 오른쪽에서 열의 뜻을 지정합니다.</b>",
    "Changing a role recolors the left column instantly (blue=input · green=response · gray=ignore)":
        "역할을 바꾸면 왼쪽 열 색이 즉시 바뀝니다 (파랑=입력 · 초록=출력 · 회색=무시)",
    "<b>Before you press Import</b>, the bottom shows \"N conditions · N "
    "measurements · N missing\". Check that those match what you expect, then press":
        "<b>가져오기를 누르기 전에</b> 아래에 ‘조건 N개 · 측정 N회 · 결측 N건’이 표시됩니다. "
        "예상과 맞는지 확인한 뒤 누르세요",
    "<b>Save a preset</b> and the next file from the same instrument loads in one step":
        "<b>프리셋을 저장</b>해 두면 같은 장비의 다음 파일은 한 번에 불러올 수 있습니다",
    "The mapping is also stored in the project file, so reopening reads identically":
        "매핑은 프로젝트 파일에도 저장되어, 다시 열어도 똑같이 읽힙니다",
    "<h3>How the role guessing works</h3>": "<h3>역할은 어떻게 추측하나</h3>",
    "<b>Design axes recycle their values; measurement columns differ on "
    "almost every row.</b> Only numeric columns with a low distinct-value "
    "ratio become input candidates. This one rule keeps intermediate "
    "measurement columns (raw band intensities and the like) from being "
    "mistaken for inputs.":
        "<b>설계축은 값이 되풀이되고, 측정값 열은 거의 모든 행에서 다릅니다.</b> "
        "고유값 비율이 낮은 숫자 열만 입력 후보로 봅니다. 이 한 가지 규칙 덕분에 "
        "원시 밴드 강도 같은 중간 측정값 열이 입력변수로 잘못 인식되지 않습니다.",
    "May I enter the same condition several times": "같은 조건을 여러 번 넣어도 되나요",
    "replicates duplicates rows": "반복측정 중복 행",
    "<b>You should.</b> One row = one measurement, and the same "
    "condition on several rows is automatically read as <b>replicates</b>.":
        "<b>넣어야 합니다.</b> 한 행 = 한 번의 측정이고, 같은 조건이 여러 행에 있으면 "
        "자동으로 <b>반복 측정</b>으로 인식합니다.",
    "Without replicates, σw (the measurement wobble) cannot be computed "
    "and requirement ③ shows <b>\"not computable\"</b>. The program "
    "<b>does not substitute an assumed value</b> — it refuses to "
    "pretend to know what it does not.":
        "반복이 없으면 σw(측정 흔들림)를 계산할 수 없어 요건 ③ 이 <b>‘계산 불가’</b>가 됩니다. "
        "이때 프로그램은 <b>가정값을 대신 넣지 않습니다</b> — 모르는 것을 아는 척하지 않습니다.",
    "What do the table colors mean": "표의 색이 무슨 뜻인가요",
    "colors background yellow red gray legend table": "색 배경 노랑 빨강 회색 범례 표",
    "color": "색",
    "meaning": "뜻",
    "where": "어디서",
    "<span style='background:{c}'>&nbsp;yellow&nbsp;</span>": "<span style='background:{c}'>&nbsp;노랑&nbsp;</span>",
    "a zero-response row · a condition with only one replicate": "응답이 0 인 행 · 반복이 1회뿐인 조건",
    "Data · Diagnose": "데이터 · 진단",
    "<span style='background:{c}'>&nbsp;pink&nbsp;</span>": "<span style='background:{c}'>&nbsp;분홍&nbsp;</span>",
    "an excluded row · the variance-dominating condition": "제외한 행 · 분산을 지배하는 조건",
    "<span style='background:{c}'>&nbsp;blue&nbsp;</span>": "<span style='background:{c}'>&nbsp;파랑&nbsp;</span>",
    "a row pre-filled from a recommendation (not yet measured)": "추천으로 미리 채운 행 (아직 측정 전)",
    "Data": "데이터",
    "<span style='background:{c}'>&nbsp;sky&nbsp;</span>": "<span style='background:{c}'>&nbsp;하늘색&nbsp;</span>",
    "a column assigned as an input": "입력변수로 지정한 열",
    "Import": "가져오기",
    "<span style='background:{c}'>&nbsp;green&nbsp;</span>": "<span style='background:{c}'>&nbsp;초록&nbsp;</span>",
    "the column assigned as the response": "출력변수로 지정한 열",
    "<h3>Figure colors</h3>": "<h3>그림의 색</h3>",
    "<b>μ (predicted mean)</b> — viridis. Magnitude": "<b>μ (예측 평균)</b> — viridis. 값의 높낮이",
    "<b>σ (uncertainty)</b> — grayscale. It is \"how unknown\", not a value":
        "<b>σ (불확실성)</b> — 무채색. 값이 아니라 ‘얼마나 모르는가’라서",
    "<b>EI (acquisition)</b> — warm. The one color that calls for action":
        "<b>EI (획득함수)</b> — 따뜻한 색. 유일하게 ‘행동을 부르는’ 색",
    "No rainbow (jet) — it invents boundaries that do not exist":
        "무지개색(jet)은 쓰지 않습니다 — 없는 경계선을 만들어 냅니다",
}
