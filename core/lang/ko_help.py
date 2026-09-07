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
    "It is locked — can I not just use it anyway": "추천이 잠겼는데 그냥 쓰면 안 되나요",
    "locked force override bypass unmet": "잠김 강행 무시 우회 미달",
    "You can. Turn on <b>\"Force a recommendation despite unmet "
    "requirements\"</b> on the Recommend tab.":
        "쓸 수는 있습니다. 추천 탭의 <b>‘요건 미달이어도 강제로 추천받기’</b>를 켜면 됩니다.",
    "But <b>it leaves a mark</b> — on the result screen, in the "
    "instruction-sheet CSV, and as a <b>\"REQUIREMENTS UNMET\" stamp on "
    "every page of the PDF report.</b> Screenshot a single page into a "
    "slide and the warning travels with it.":
        "다만 <b>자국이 남습니다</b> — 결과 화면과 지시서 CSV, 그리고 PDF 리포트의 "
        "<b>모든 쪽에 ‘요건 미달’ 도장</b>이 찍힙니다. 한 장만 캡처해 슬라이드에 붙여도 경고가 함께 따라갑니다.",
    "<h3>Try these first</h3>": "<h3>그 전에 해 볼 것</h3>",
    "Put a target discriminability into the <b>prescription</b> on the "
    "Diagnose tab — it back-computes how many more replicates you need":
        "진단 탭의 <b>처방</b>에 목표 판별력을 넣어 보세요 — 몇 번 더 재야 하는지 역산해 줍니다",
    "If the <b>warning</b> box says one condition carries N% of the "
    "variance, re-measuring that condition is the cheapest check":
        "<b>경고</b> 상자에 ‘조건 하나가 분산의 N%를 차지한다’고 뜨면, "
        "그 조건을 다시 재 보는 것이 가장 값싼 확인입니다",
    "If requirement ① is the problem, make the step finer or the range wider on the "
    "Setup tab. If the candidates are still fewer than the budget, <b>measuring everything "
    "is right</b> — this program is not needed in that case":
        "요건 ① 이 문제라면 설정 탭에서 간격을 촘촘히 하거나 범위를 넓히세요. "
        "그래도 후보가 예산보다 적다면 <b>전수 측정이 맞습니다</b> — 이 프로그램이 필요 없는 경우입니다",
    "Which of the three methods should I use": "고르는 방식 셋 중 뭘 써야 하나요",
    "acquisition EI UCB Thompson beta explore method global local benchmark":
        "획득함수 EI UCB Thompson 베타 탐색 방법 전역 지역 벤치마크",
    "Chosen at the <b>top of the Recommend tab</b>. Without a specific "
    "reason, keep the default.":
        "<b>추천 탭 위쪽</b>에서 고릅니다. 특별한 이유가 없으면 기본값을 그대로 두세요.",
    "what": "무엇",
    "when": "언제",
    "<b>Default (EI)</b>": "<b>기본값 (EI)</b>",
    "Expected improvement — how much a candidate should beat the best so far":
        "기대개선량(EI) — 후보가 지금까지의 최고값을 얼마나 넘어설지의 기댓값",
    "Almost always. On 8 standard test functions it reached the neighbourhood of the "
    "global optimum within a 40-run budget — "
    "multimodal average {multi} · unimodal average {uni} (table below)":
        "거의 항상 적합합니다. 표준 시험함수 8개에서 40회 예산 안에 전역 최적점 근방에 도달했습니다 — "
        "다봉 함수 평균 {multi} · 단봉 함수 평균 {uni} (아래 표)",
    "<b>Explore wider (UCB)</b>": "<b>더 넓게 탐색 (UCB)</b>",
    "μ + b·σ. A larger b pushes into uncertainty": "μ + b·σ. b 를 키울수록 불확실한 쪽으로 더 밀고 들어갑니다",
    "When the terrain is still unknown. Mind the caution below": "지형을 아직 잘 모를 때. 아래 주의사항을 참고하세요",
    "<b>Diversify (Thompson)</b>": "<b>다양화 (Thompson)</b>",
    "draw one function from the posterior, take its maximum": "사후분포에서 함수 하나를 뽑아 그 최댓값을 취합니다",
    "When receiving several at once — candidates do not pile up in one spot":
        "한 번에 여러 개를 받을 때 — 후보가 한곳에 몰리지 않습니다",
    "<h3>Does it get stuck in a local optimum</h3>": "<h3>국소 최적에 빠지지 않나요</h3>",
    "Two layers guard against it. ① The initial design is space-filling (maximin LHS), so "
    "the whole range is swept from the start, and ② the acquisition maximisation is "
    "<b>multi-start</b> (L-BFGS-B from the best 20 of 2000 space-filling points), so it does "
    "not settle on the nearest peak — at all 72 check points it found a value at least as "
    "good as differential evolution (a global optimiser).":
        "두 겹으로 막습니다. ① 초기 설계가 공간충진(maximin LHS)이라 처음부터 범위 전체를 훑고, "
        "② 획득함수 최대화는 <b>다중 시작</b>(공간충진 점 2000개 중 상위 20곳에서 L-BFGS-B)이라 "
        "가장 가까운 봉우리에 머물지 않습니다 — 검사 지점 72곳 전부에서 미분진화(전역 최적화기) "
        "이상의 값을 찾았습니다.",
    "Still, <b>some terrain it cannot find</b>. The 2026-09-05 benchmark "
    "(budget 40 = 11 initial + 29 sequential, 3% noise, 10 seeds, hit = regret below 5%):":
        "그래도 <b>못 찾는 지형</b>은 있습니다. 2026-09-05 벤치마크(예산 40 = 초기 11 + 순차 29, "
        "잡음 3%, 시드 10개, 도달 = 후회 5% 미만):",
    "test function": "시험함수",
    "EI hit rate": "EI 도달률",
    "what it measures": "무엇을 재는가",
    "Branin · six-hump camel · Hartmann-3 · Rosenbrock": "Branin · 낙타등 6 · Hartmann-3 · Rosenbrock",
    "several peaks (2–3 dimensions) — standard multimodal · a curved valley":
        "봉우리 여럿 (2~3차원) — 표준 다봉 · 굽은 골짜기",
    "Levy-4": "Levy-4",
    "many local peaks (4 dimensions)": "국소 봉우리 다수 (4차원)",
    "Two peaks (needle)": "두 봉우리 (바늘)",
    "a narrow valley covering barely 1% of the space — only the seeds whose initial "
    "design landed in it found it":
        "전체의 1% 남짓한 좁은 골짜기 — 초기 설계가 거기 떨어진 시드만 찾아냈습니다",
    "Ackley": "Ackley",
    "a rough surface (terrain dense with small bumps)": "거친 표면 (잔봉우리가 촘촘한 지형)",
    "Hartmann-6": "Hartmann-6",
    "6 dimensions — no method finds it within a 40-run budget": "6차원 — 예산 40회로는 어떤 방식도 찾지 못합니다",
    "So with <b>6 or more variables, or a very narrow optimum</b>, a 40-run budget is not "
    "enough. The answer then is not a different acquisition function but the "
    "<b>initial design size (25–30% of the budget) · the budget · the range</b>.":
        "즉 <b>변수가 6개 이상이거나 최적점이 아주 좁다면</b> 예산 40회로는 부족합니다. "
        "이때 답은 획득함수를 바꾸는 것이 아니라 <b>초기 설계 크기(예산의 25~30%) · 예산 · 범위</b>입니다.",
    "<h3>Why there is no separate global-search acquisition</h3>": "<h3>왜 전역 탐색용 획득함수를 따로 두지 않았나</h3>",
    "Four alternatives (MES · EI mixed with exploration · a GP-UCB schedule · Thompson) were "
    "measured under the same conditions. The best multimodal average was "
    "{best_alt}, which did not beat "
    "EI ({ei}), and the narrow valley and the 6-dimensional "
    "function defeated the alternatives just the same. The rule — 'it goes on screen only if it "
    "beats EI on multimodal functions and loses nothing on unimodal ones' — was fixed "
    "<b>before measuring</b>, and nothing passed it, so nothing went on screen. The candidate "
    "code and the result file stay in the repo — re-measure, and if one passes, a test says so.":
        "대안 4종(MES · 탐색을 섞은 EI · GP-UCB 일정 · Thompson)을 같은 조건에서 측정했습니다. "
        "다봉 평균 최고값이 {best_alt} 로 EI({ei})를 넘지 못했고, 좁은 골짜기와 6차원 함수는 "
        "대안들도 똑같이 찾지 못했습니다. ‘다봉 함수에서 EI 를 이기고 단봉 함수에서 손해가 없어야 "
        "화면에 올린다’는 규칙을 <b>측정하기 전에</b> 정했는데, 이를 통과한 것이 없어 화면에 올리지 "
        "않았습니다. 후보 코드와 결과 파일은 레포에 그대로 남아 있습니다 — 다시 측정해서 통과하는 "
        "것이 나오면 테스트가 알려 줍니다.",
    "<h3>Caution — pushing exploration harder does not help</h3>": "<h3>주의 — 탐색을 더 밀어붙인다고 좋아지지 않습니다</h3>",
    "In the original validation (2026-08), raising UCB's b from 1 to 4 dropped the "
    "global-optimum hit rate from <b>90% to 61%</b>, and pure space-filling was the "
    "worst at 1–7%. In this benchmark too, UCB (b=2) averaged "
    "{ucb} on the multimodal functions, below "
    "EI's {ei}. "
    "Do not casually raise the default b = 2.0.":
        "원래 검증(2026-08)에서 UCB 의 b 를 1에서 4로 키우자 전역 최적 도달률이 <b>90%에서 61%</b>로 "
        "떨어졌고, 순수한 공간충진은 1~7%로 가장 나빴습니다. 이번 벤치마크에서도 UCB(b=2)는 "
        "다봉 함수에서 평균 {ucb} 로 EI 의 {ei} 보다 낮았습니다. 기본값 b = 2.0 을 함부로 올리지 마세요.",
    "Can I get several at once": "여러 개를 한꺼번에 받을 수 있나요",
    "batch several at once": "배치 여러개 한번에",
    "Up to 10, via <b>\"At a time\"</b> under Advanced on the Recommend tab.":
        "추천 탭의 고급 설정 <b>‘한 번에 N개’</b>로 최대 10개까지 받을 수 있습니다.",
    "They are picked sequentially, each picked point <b>assuming its "
    "predicted mean as if observed</b> before the model refits for the "
    "next pick (kriging believer). No unmeasured value is ever "
    "consulted, so the <b>no-lookahead rule</b> holds.":
        "순차로 뽑되, 이미 뽑은 점은 <b>예측 평균을 관측값처럼 가정</b>하고 모델을 다시 학습한 뒤 "
        "다음 점을 고릅니다(kriging believer). 아직 측정하지 않은 값은 절대 참조하지 않으므로 "
        "<b>선행 참조 금지 규칙</b>이 지켜집니다.",
    "Why does the recommendation carry a suggested replicate count": "추천에 ‘권장 반복’ 이 왜 붙나요",
    "suggested replicates instruction count": "권장반복 지시서 횟수",
    "Measure a new condition <b>only once and discriminability drops</b>, "
    "worsening the next verdict. So \"measure it n times\" goes on the "
    "instruction sheet.":
        "새 조건을 <b>한 번만 재면 판별력이 떨어져</b> 다음 판정이 나빠집니다. "
        "그래서 ‘n번 재라’를 지시서에 함께 적습니다.",
    "The value follows the <b>median</b> replicate count of the current data.":
        "이 값은 현재 데이터의 반복 횟수 <b>중앙값</b>을 따릅니다.",
    "What is the \"step\", and must I fill it in": "‘간격’은 무엇이고 꼭 채워야 하나요",
    "step grid resolution instrument setting candidates": "간격 그리드 해상도 장비 설정 후보",
    "The <b>step</b> in the Setup tab's variable table is <b>the spacing the instrument "
    "can actually be set to</b>. If the power dial moves in 10 W units, enter 10; if the "
    "temperature setting moves in 5 °C units, enter 5. Only continuous variables have "
    "one — integer variables have a built-in step of 1.":
        "설정 탭 변수표의 <b>간격</b>은 <b>장비가 실제로 낼 수 있는 조정 단위</b>입니다. "
        "전력 다이얼이 10 W 단위로 움직인다면 10을, 온도 설정이 5 °C 단위로 움직인다면 5를 넣습니다. "
        "연속형 변수에만 있고, 정수형 변수는 간격 1이 기본으로 내장되어 있습니다.",
    "<h3>What changes once it is filled in</h3>": "<h3>넣으면 달라지는 것</h3>",
    "<b>Recommendations land on the grid</b>. A value like 173.6 W cannot go on an instruction sheet":
        "<b>추천값은 간격에 맞는 값</b>으로만 나옵니다. 173.6 W 같은 값은 지시서에 쓸 수 없습니다",
    "<b>The candidate count of requirement ①</b> becomes countable — with even one continuous "
    "variable without a step, the candidates are infinite and ① always passes":
        "<b>요건 ① 의 후보 수</b>를 셀 수 있게 됩니다 — 간격이 없는 연속형 변수가 하나라도 있으면 "
        "후보가 무한이 되어 ① 은 항상 통과합니다",
    "The initial design points are snapped to the grid too. If snapping makes two coincide, "
    "they stay — a coincidence is simply a replicate":
        "초기 설계점도 간격에 맞춰 스냅됩니다. 스냅으로 두 점이 겹치면 그대로 둡니다 — "
        "겹침은 곧 반복 측정입니다",
    "Leave it empty and the variable is treated as continuous. That is not wrong, but the "
    "recommendations will be finer than the instrument can set.":
        "비워 두면 그 변수는 연속형으로 다룹니다. 틀린 것은 아니지만, "
        "장비가 실제로 낼 수 있는 것보다 더 촘촘한 값을 추천받게 됩니다.",
    "Can I add a constraint like composition sum = 100 %": "조성 합 = 100 % 같은 제약을 걸 수 있나요",
    "constraint sum composition 100 mixture blend": "제약 합 조성 100 혼합물 배합",
    "Yes. Under <b>\"Sum constraint\"</b> on the Setup tab, pick 2 or more variables and "
    "enter <b>= exactly</b> or <b>≤ at most</b> with the total. From then on the initial "
    "design points and the recommendations come out <b>only as values that satisfy "
    "the constraint</b>.":
        "됩니다. 설정 탭의 <b>‘합 제약’</b>에서 변수를 2개 이상 고르고 <b>= 정확히</b> 또는 "
        "<b>≤ 최대</b>와 합계를 넣으세요. 그 뒤로는 초기 설계점과 추천이 <b>전부 그 제약을 "
        "만족하는 값</b>으로만 나옵니다.",
    "<h3>How it is kept</h3>": "<h3>어떻게 지키는가</h3>",
    "Points are drawn evenly on the constraint plane (Dirichlet) and the ones far apart "
    "from each other become the initial design":
        "제약 평면 위에서 고르게 점을 뽑고(Dirichlet), 서로 멀리 떨어진 점들을 초기 설계로 씁니다",
    "If snapping to the grid breaks the sum, the values are moved <b>in whole steps</b> to "
    "restore it — which is why <b>\"= exactly\" needs the constrained variables to share "
    "one step</b> (the Setup tab tells you)":
        "간격에 맞추다가 합이 어긋나면 <b>간격 단위로</b> 값을 옮겨 합을 되돌립니다 — 그래서 "
        "<b>‘= 정확히’는 제약에 걸린 변수들의 간격이 같아야</b> 합니다 (설정 탭이 알려 줍니다)",
    "The candidate count of requirement ① is also counted inside the constraint "
    "(A·B·C with step 10, sum 100 → 66 candidates)":
        "요건 ① 의 후보 수도 이 제약 안에서 셉니다 (A·B·C 간격 10, 합 100 → 66개)",
    "<h3>If measured values already violate the constraint</h3>": "<h3>이미 측정한 값이 제약을 어길 때</h3>",
    "The Setup tab shows how many rows violate it. Those rows are still used for learning "
    "(they were actually measured); only the new recommendations stay inside the constraint.":
        "설정 탭에 몇 개 행이 제약을 어기는지 표시됩니다. 그 행도 실제로 측정한 값이므로 "
        "학습에는 그대로 쓰이고, 새 추천만 제약 안에서 나옵니다.",
    "What happens at startup (the boot log)": "켤 때 무슨 일이 일어나나요 (시작 기록)",
    "startup slow loading splash black window terminal log": "시작 느림 로딩 스플래시 검은창 터미널 로그",
    "On launch a small card appears and says in one line what it is doing — <b>loading "
    "the computation engine</b> is the longest part (numpy · scipy · scikit-learn, "
    "usually 2–6 seconds). Then the window opens.":
        "실행하면 작은 카드가 뜨고 지금 하는 일을 한 줄로 보여 줍니다 — "
        "<b>계산 엔진을 불러오는 중</b>이 가장 오래 걸립니다 (numpy·scipy·scikit-learn, 보통 2~6초). "
        "그다음 창이 열립니다.",
    "<h3>The black console windows that used to flash</h3>": "<h3>예전에 번쩍이던 검은 콘솔 창</h3>",
    "Earlier builds flashed black windows on launch. They were not our code but the "
    "<code>cmd</code> · <code>powershell</code> processes that the computation packages "
    "spawn while being imported (the Python standard library's <code>platform</code> module "
    "and joblib's CPU count). Every child process is now forced to start <b>without a "
    "window</b>, and whatever was spawned is written to the log.":
        "예전 버전은 실행할 때 검은 창이 번쩍이며 떴다 사라지곤 했습니다. 이는 우리 코드가 아니라, "
        "계산 패키지들이 임포트되는 동안 띄우는 <code>cmd</code>·<code>powershell</code> 프로세스였습니다 "
        "(파이썬 표준 라이브러리의 <code>platform</code> 모듈과 joblib 의 CPU 개수 확인). "
        "이제는 모든 자식 프로세스가 <b>창 없이</b> 실행되도록 강제되며, 무엇이 실행됐는지는 로그에 기록됩니다.",
    "<h3>The log file</h3>": "<h3>로그 파일</h3>",
    "<code>home folder\\.seqopt\\seqopt.log</code> records how long each stage took. "
    "When someone says 'it is slow to start' or 'a strange window appeared', this file is "
    "the place to look. Errors go to <code>error.log</code> in the same folder.":
        "<code>홈 폴더\\.seqopt\\seqopt.log</code> 에 각 단계가 걸린 시간이 기록됩니다. "
        "‘시작이 느리다’거나 ‘이상한 창이 떴다’는 말이 나오면 이 파일을 보면 됩니다. "
        "오류는 같은 폴더의 <code>error.log</code> 에 남습니다.",
    "It says \"outside measured range\"": "‘실측 범위 밖’ 이라고 뜨는데요",
    "extrapolation outside range warning": "외삽 범위밖 경고",
    "The model learned <b>the range you actually measured.</b> Where the "
    "declared range on the Setup tab is wider, the outside is somewhere "
    "the model has never seen.":
        "모델은 <b>실제로 측정한 범위</b>를 학습했습니다. 설정 탭에 선언한 범위가 그보다 넓다면, "
        "그 바깥은 모델이 한 번도 보지 못한 곳입니다.",
    "<b>It is not blocked</b> — widening the range and measuring there "
    "is sometimes exactly the right move. But it is always marked.":
        "<b>막지는 않습니다</b> — 범위를 넓혀서 그 바깥을 측정하는 것이 오히려 옳은 선택일 때도 "
        "있기 때문입니다. 다만 항상 표시됩니다.",
    "What is it computing inside": "안에서 무슨 계산을 하나요",
    "logic algorithm GP kernel EI principle formulas": "로직 알고리즘 GP 커널 EI 원리 수식",
    "<h3>In one line</h3>": "<h3>한 줄로</h3>",
    "From the measured conditions it estimates the <b>response surface</b> "
    "(input → output), with a model that also reports its own "
    "<b>uncertainty</b>. Then \"how much would measuring here teach\" is "
    "scored, and the highest scorer wins.":
        "측정한 조건들로부터 <b>응답면</b>(입력 → 출력)을 추정하되, 스스로의 <b>불확실성</b>도 함께 "
        "보고하는 모델을 씁니다. 그다음 ‘여기를 재면 얼마나 배우게 될까’를 점수로 매겨 가장 높은 "
        "점수를 받은 곳이 이깁니다.",
    "<h3>1. The surrogate — a Gaussian process</h3>": "<h3>1. 대리모델 — 가우시안 프로세스</h3>",
    "<b>Matern ν=2.5</b> — smooth but not overly smooth. A common fit for experimental surfaces":
        "<b>Matern ν=2.5</b> — 매끄럽지만 너무 매끄럽지는 않은 곡면. 실험 응답면에 흔히 맞습니다",
    "<b>ARD</b> — one length scale per variable. The sensitivity view comes from here":
        "<b>ARD</b> — 변수마다 길이척도를 따로 둡니다. 민감도 보기가 여기서 나옵니다",
    "<b>WhiteKernel</b> — absorbs measurement noise. It earns its keep once replicates exist":
        "<b>WhiteKernel</b> — 측정 잡음을 흡수합니다. 반복 측정이 있어야 제 몫을 합니다",
    "The model learns <b>condition means</b>. Replicates feed discriminability (gate ③)":
        "모델이 학습하는 대상은 <b>조건 평균</b>입니다. 반복 측정은 판별력(관문 ③)에 쓰입니다",
    "<h3>2. The acquisition — choosing where to measure next</h3>": "<h3>2. 획득함수 — 다음에 잴 곳 고르기</h3>",
    "<pre>EI  = (μ − best)·Φ(z) + σ·φ(z),   z = (μ − best)/σ\n"
    "UCB = μ + b·σ\n"
    "TS  = one posterior draw, take its maximum</pre>":
        "<pre>EI  = (μ − best)·Φ(z) + σ·φ(z),   z = (μ − best)/σ\n"
        "UCB = μ + b·σ\n"
        "TS  = 사후분포에서 뽑은 함수 하나의 최댓값</pre>",
    "<b>best is always the best measured value.</b> Use a true or corrected "
    "value and the choice no longer matches what a researcher would actually do.":
        "<b>best 는 언제나 실제로 측정한 값 중 최선</b>입니다. 참값이나 보정값을 쓰면 "
        "실제 연구자가 할 선택과 달라집니다.",
    "<h3>3. The diagnostics — what only this tool does</h3>": "<h3>3. 진단 — 이 도구만 하는 것</h3>",
    "<pre>σ<sub>w</sub> = √( Σ(n−1)·var(replicates) / Σ(n−1) )    measurement wobble\n"
    "σ<sub>b</sub> = std( condition means , ddof=1 )         between-condition difference\n"
    "D(n) = σ<sub>b</sub> / (σ<sub>w</sub>/√n)                        discriminability\n\n"
    "R² = 1 − SS_res/SS_tot   (per-condition LOOCV, refit per fold)\n"
    "nugget ratio = nugget / sill   (semivariogram)</pre>":
        "<pre>σ<sub>w</sub> = √( Σ(n−1)·var(replicates) / Σ(n−1) )    측정 흔들림\n"
        "σ<sub>b</sub> = std( condition means , ddof=1 )         조건 간 차이\n"
        "D(n) = σ<sub>b</sub> / (σ<sub>w</sub>/√n)                        판별력\n\n"
        "R² = 1 − SS_res/SS_tot   (조건별 LOOCV, 폴드마다 재학습)\n"
        "nugget ratio = nugget / sill   (세미베리오그램)</pre>",
    "Discriminability comes with a 95% interval from a <b>4000-draw "
    "condition bootstrap</b>. When the interval straddles 1.0, the verdict "
    "is \"undecided\".":
        "판별력은 <b>조건 단위 부트스트랩 4000회</b>로 낸 95% 구간과 함께 나옵니다. "
        "구간이 1.0 을 걸치면 판정은 ‘판정불가’입니다.",
    "Has it been validated": "검증은 된 건가요",
    "validation trust tests reproduce evidence measured": "검증 신뢰 테스트 재현 근거 측정",
    "<h3>How far the validation goes</h3>": "<h3>검증이 어디까지 됐나</h3>",
    "part": "부분",
    "status": "상태",
    "evidence": "근거",
    "<b>diagnostic calculations</b><br>discriminability · learnability · nugget":
        "<b>진단 계산</b><br>판별력 · 학습가능성 · 너깃비",
    "<b>validated</b>": "<b>검증됨</b>",
    "the test suite pins the numbers the original validation scripts "
    "produced, to within 1e-3; the public-dataset expectation file "
    "(verify_terrain.json) ships in this repo":
        "테스트가 원래의 검증 스크립트가 낸 값들을 오차 1e-3 이내로 고정합니다. "
        "공개 데이터셋의 기대값 파일(verify_terrain.json)이 이 레포에 함께 있습니다",
    "<b>the gate verdict</b>": "<b>관문 판정</b>",
    "the same yardstick applied to four datasets (one lab, three public) "
    "reproduced the original analysis' split":
        "같은 잣대를 데이터셋 4개(실험 데이터 1개 · 공개 데이터셋 3개)에 적용했더니 "
        "원래 분석과 같은 판정으로 나뉘었습니다",
    "<b>single recommendations (EI · GP)</b>": "<b>단일 추천 (EI · GP)</b>",
    "the global-optimum hit rate within a 40-run budget was actually measured on "
    "8 standard test functions × 10 seeds "
    "(multimodal average {multi}). The result file "
    "ships in the repo, and a test checks the numbers on screen against it":
        "40회 예산 안의 전역 최적 도달률을 표준 시험함수 8개 × 시드 10개에서 실제로 측정했습니다 "
        "(다봉 평균 {multi}). 결과 파일이 레포에 있고, 화면의 숫자가 그 파일과 일치하는지 "
        "테스트가 확인합니다",
    "<b>four global-search alternatives</b>": "<b>전역 탐색 대안 4종</b>",
    "<b>no gain, confirmed</b>": "<b>이득 없음, 확인됨</b>",
    "MES · exploration mixing · GP-UCB · Thompson compared under the same conditions. "
    "None beat EI on the multimodal functions, so none went on screen "
    "(see «Which of the three methods»)":
        "MES · 탐색을 섞은 EI · GP-UCB 일정 · Thompson 을 같은 조건에서 비교했습니다. "
        "다봉 함수에서 EI 를 이긴 것이 하나도 없어 화면에 올리지 않았습니다 "
        "(«고르는 방식 셋 중 뭘 써야 하나요» 참고)",
    "<b>sum constraint · grid candidates</b>": "<b>합 제약 · 격자 후보</b>",
    "tests check that initial designs and recommendations land only on the "
    "constraint plane and on the grid":
        "초기 설계와 추천이 제약 평면 위, 그리고 격자 위에만 놓이는지 테스트로 확인합니다",
    "batch recommendations": "배치 추천",
    "<b>not validated</b>": "<b>검증되지 않음</b>",
    "only checked that distinct points come out. Whether batches beat "
    "sequential picking was never measured":
        "서로 다른 점이 나오는지만 확인했습니다. 배치가 순차 추천보다 나은지는 측정한 적이 없습니다",
    "the random-forest surrogate": "랜덤 포레스트 대리모델",
    "its uncertainty calibration was never checked. Comparison only":
        "불확실성 보정이 맞는지 확인한 적이 없습니다. 비교용으로만 씁니다",
    "<h3>Numbers pinned by the tests (public datasets)</h3>": "<h3>테스트로 고정된 수치 (공개 데이터셋)</h3>",
    "item": "항목",
    "value": "값",
    "external discriminability D": "외부 데이터셋 판별력 D",
    "terrain nugget ratios": "지형 너깃비",
    "The lab dataset the study was run for is <b>not distributed</b> with "
    "this repository; the numbers quoted in this help (R² = −0.272, "
    "D = 1.03 [0.49, 1.80], noise share 95%) are that study's published "
    "aggregates.":
        "이 연구에 쓰인 실험 데이터는 <b>이 저장소에 포함되어 있지 않습니다</b>. "
        "이 도움말에 인용된 수치(R² = −0.272, D = 1.03 [0.49, 1.80], 잡음 비중 95%)는 "
        "그 연구에서 발표한 집계값입니다.",
    "<h3>Held in place by machines</h3>": "<h3>기계로 고정돼 있습니다</h3>",
    "The test suite — <b>{n} tests</b> — re-verifies these values on every "
    "run. Change the calculation and the tests break — that is the tripwire.":
        "테스트 <b>{n}개</b>가 위 값들을 매번 다시 확인합니다. "
        "계산 방식을 바꾸면 테스트가 깨집니다 — 그것이 안전장치입니다.",
    "The Windows executable is only built <b>after the tests pass</b>. "
    "A program that misjudges must never get packaged.":
        "윈도우 실행파일도 <b>테스트를 통과해야만</b> 빌드됩니다. "
        "잘못 판정하는 프로그램이 배포되어서는 안 되기 때문입니다.",
    "<h3>What honestly was not done</h3>": "<h3>솔직히 못 한 것</h3>",
    "Whether batch recommendations beat sequential ones was <b>never measured</b>":
        "배치 추천이 순차 추천보다 나은지 <b>측정한 적이 없습니다</b>",
    "The extrapolation margin of 0.02 was <b>chosen without evidence</b>":
        "외삽 여유 0.02 는 <b>근거 없이 정한 값</b>입니다",
    "Of the four gate thresholds, only <b>R² > 0</b> has a hard basis. "
    "The discriminability 1.0 is borrowed from other fields, so it is "
    "safest in \"A vs B\" comparisons":
        "관문 임계값 4개 중 단단한 근거가 있는 것은 <b>R² > 0 하나</b>뿐입니다. "
        "판별력 1.0 은 다른 분야에서 빌려온 값이라 ‘A 대 B’ 비교에 쓰는 것이 가장 안전합니다",
    "The global-search benchmark uses <b>synthetic test functions</b>, not real device terrain":
        "전역 탐색 벤치마크는 <b>합성 시험함수</b>를 씁니다. 실제 소자 지형이 아닙니다",
    "The stopping-rule history resets when the program restarts":
        "정지 규칙 이력은 프로그램을 다시 시작하면 초기화됩니다",
    "Can I trust these numbers": "이 숫자를 믿어도 되나요",
    "validation trust evidence tests reproduce": "검증 신뢰 근거 테스트 재현",
    "<h3>Three ways to check</h3>": "<h3>세 가지로 확인할 수 있습니다</h3>",
    "<b>Diagnose tab → unfold the calculation</b> — per-condition n, mean, "
    "SD and contribution are all visible, and the σw·σb·D in the box "
    "below come straight from that table":
        "<b>진단 탭 → 계산 과정 펼치기</b> — 조건별 n·평균·SD·기여도가 모두 보이고, "
        "아래 상자의 σw·σb·D 는 그 표에서 바로 나옵니다",
    "<b>Report → calculation log</b> — every number's formula and "
    "intermediate values, saved as text":
        "<b>리포트 → 계산 로그</b> — 모든 수치의 산출식과 중간값을 텍스트로 저장합니다",
    "<b>Report → reproduction script</b> — one file that produces the same "
    "numbers again. Half a year later, \"where did this number come "
    "from\" still has an answer":
        "<b>리포트 → 재현 스크립트</b> — 파일 하나로 같은 숫자를 다시 낼 수 있습니다. "
        "반년 뒤 ‘이 숫자가 어디서 나왔나’ 라는 질문에도 답할 수 있습니다",
    "<h3>Machine-checked</h3>": "<h3>기계 검증</h3>",
    "The computation core is pinned by tests that reproduce the original "
    "validation scripts' values to within 1e-3 (the external datasets' "
    "D values and terrain statistics among them). {n} tests in all.":
        "계산 핵심부는 원래의 검증 스크립트가 낸 값들을 오차 1e-3 이내로 재현하도록 테스트로 "
        "고정되어 있습니다 (그중에는 외부 데이터셋의 D 값과 지형 통계도 포함됩니다). "
        "테스트는 모두 {n}개입니다.",
    "So <b>changing the calculation breaks the tests.</b> That is the tripwire.":
        "그래서 <b>계산 방식을 바꾸면 테스트가 깨집니다.</b> 그것이 안전장치입니다.",
    "The learnability computation is slow": "학습가능성 계산이 오래 걸립니다",
    "slow speed performance LOOCV background": "느림 속도 성능 LOOCV 백그라운드",
    "It is. LOOCV refits the model once per condition — "
    "<b>39 seconds at 178 conditions × 5 variables</b> (measured).":
        "맞습니다. LOOCV 는 조건 수만큼 모델을 다시 학습하므로 <b>조건 178개·변수 5개에서 39초</b>가 "
        "걸립니다(실측).",
    "So the fast parts (surface, σ, EI — 0.2s) and the slow part "
    "(learnability R²) are split, and only the slow part runs in the "
    "background. Table input never freezes.":
        "그래서 빠른 부분(응답면·σ·EI, 0.2초)과 느린 부분(학습가능성 R²)을 나누어 느린 쪽만 "
        "백그라운드에서 돌립니다. 표 입력은 절대 멈추지 않습니다.",
    "<h3>Why not use the fast method</h3>": "<h3>왜 빠른 방법을 안 쓰나</h3>",
    "Closed-form LOO with fixed hyperparameters is <b>200× faster.</b> "
    "But on the validation study's lab data it flipped R² from "
    "<b>−0.272 to +0.228</b> — information used in fitting leaks into "
    "every fold.":
        "하이퍼파라미터를 고정한 폐형식 LOO 를 쓰면 <b>200배 빨라집니다.</b> "
        "그런데 그 검증 연구의 실험 데이터에서는 R² 가 <b>−0.272 에서 +0.228 로 뒤집힙니다</b> — "
        "학습에 쓰인 정보가 모든 폴드로 새어 들어가기 때문입니다.",
    "That speed would buy a <b>gate verdict reversed from FAIL to OK.</b> "
    "It would erase this tool's reason to exist, so it is not used.":
        "그 속도를 얻는 대가로 <b>관문 판정이 FAIL 에서 OK 로 뒤바뀝니다.</b> "
        "이 도구가 존재하는 이유 자체가 사라지므로 쓰지 않습니다.",
    "What this program does not do": "이 프로그램이 못 하는 것",
    "limits out of scope constraints multi-objective": "한계 범위밖 제약 다목적",
    "<b>Explicitly out of scope.</b> Not for lack of ability — half-built "
    "features with no explanation are more dangerous than absent ones.":
        "<b>명시적으로 범위 밖입니다.</b> 못 만들어서가 아닙니다 — 설명 없이 어설프게 들어간 기능이 "
        "아예 없는 기능보다 더 위험하기 때문입니다.",
    "<b>Multi-objective optimization (Pareto)</b> — more than one response":
        "<b>다목적 최적화(파레토)</b> — 출력변수가 2개 이상인 경우",
    "<b>Constraints other than one sum</b> — only <b>a single linear sum constraint</b> "
    "(e.g. composition = 100%) is supported. Inequalities between variables such as "
    "'A &gt; B', nonlinear constraints and two or more constraints are not":
        "<b>합 제약 외의 다른 제약</b> — 조성 = 100% 같은 <b>선형 합 제약 하나</b>만 지원합니다. "
        "‘A &gt; B’ 같은 변수 간 부등식, 비선형 제약, 제약 2개 이상은 지원하지 않습니다",
    "<b>Population methods — genetic algorithms · PSO · CMA-ES</b> — each generation needs "
    "dozens of runs, so a budget of a few dozen runs affords one or two generations "
    "(effectively random search). Global search is done by the space-filling initial "
    "design and the multi-start acquisition maximisation — see «Which of the three "
    "methods» for the results on 8 test functions":
        "<b>유전 알고리즘 · PSO · CMA-ES 같은 개체군 방식</b> — 세대마다 수십 번의 측정이 필요해, "
        "예산이 수십 회뿐이면 한두 세대밖에 돌릴 수 없습니다(사실상 무작위 탐색). 전역 탐색은 공간을 "
        "고루 채우는 초기 설계와 획득함수의 다중 시작 최대화로 대신합니다 — 시험함수 8개에 대한 결과는 "
        "«고르는 방식 셋 중 뭘 써야 하나요»를 보세요",
    "<b>Multi-fidelity</b> — mixing coarse and precise computations":
        "<b>다중 정밀도(multi-fidelity)</b> — 거친 계산과 정밀한 계산을 섞어 쓰는 방식",
    "<b>Instrument control / automated measurement</b> — a person measures and types the value":
        "<b>장비 직접 제어 · 자동 측정</b> — 사람이 측정해서 값을 입력하는 구조입니다",
    "<b>Cloud sync · multiple users</b>": "<b>클라우드 동기화 · 다중 사용자</b>",
    "<h3>Scale limits</h3>": "<h3>규모의 한계</h3>",
    "Around 200 conditions × 5 variables is the comfortable range. Beyond "
    "500 conditions, a single model fit passes 2 seconds. For thousands of "
    "points, a different tool is the right choice.":
        "조건 200개 · 변수 5개 정도가 편안한 범위입니다. 500개를 넘어가면 모델을 한 번 학습하는 데만 "
        "2초를 넘습니다. 수천 개의 점을 다루려면 다른 도구가 맞습니다.",
    "How do saving and backups work": "저장 · 백업은 어떻게 되나요",
    "save backup autosave recovery seqopt file": "저장 백업 자동저장 복구 seqopt 파일",
    "A project is one <b>.seqopt</b> file, with <b>the raw data inside "
    "it, whole</b> — move the original spreadsheet and every number "
    "still traces back":
        "프로젝트는 <b>.seqopt</b> 파일 하나입니다. <b>원본 데이터를 통째로 그 안에</b> 담고 있어서, "
        "원본 스프레드시트를 옮겨도 모든 숫자를 그대로 추적할 수 있습니다",
    "Saves are <b>atomic</b> — the program dying mid-save leaves the previous file intact":
        "저장은 <b>원자적</b>입니다 — 저장 도중 프로그램이 죽어도 이전 파일은 그대로 남습니다",
    "The previous version survives as <b>.seqopt.bak</b>": "이전 버전은 <b>.seqopt.bak</b> 으로 남습니다",
    "Every minute, an <b>.seqopt.autosave</b> is written. A dead PC "
    "still yields the last state":
        "1분마다 <b>.seqopt.autosave</b> 가 기록됩니다. PC 가 꺼져도 마지막 상태를 되찾을 수 있습니다",
    "The Data tab undoes with <b>Ctrl+Z</b> (50 steps)": "데이터 탭은 <b>Ctrl+Z</b> 로 되돌릴 수 있습니다 (50단계)",
    "Adding features": "기능을 추가하려면",
    "development extension code algorithm add module": "개발 확장 코드 알고리즘 추가 모듈",
    "<b>Computation (core/) and screens (ui/) are split.</b> "
    "core never imports the GUI and runs entirely from the CLI.":
        "<b>계산(core/)과 화면(ui/)이 분리되어 있습니다.</b> core 는 GUI 를 임포트하지 않으며 "
        "CLI 만으로도 전부 동작합니다.",
    "<h3>Plugging in a new algorithm</h3>": "<h3>새 알고리즘 붙이기</h3>",
    "Register <b>one class</b> — no existing file changes. It enters the "
    "screen list, the report and the recommendation path automatically.":
        "<b>클래스 하나만 등록</b>하면 됩니다 — 기존 파일은 고치지 않습니다. "
        "화면 목록·리포트·추천 경로에 자동으로 들어갑니다.",
    "<h3>What must not change</h3>": "<h3>바꾸면 안 되는 것</h3>",
    "<b>The GP kernel</b> — exactly one combination reproduces the regression expectations":
        "<b>GP 커널</b> — 회귀 기댓값을 재현하는 조합은 단 하나뿐입니다",
    "<b>LOOCV to closed form</b> — the gate verdict flips": "<b>LOOCV 를 폐형식으로 바꾸기</b> — 관문 판정이 뒤집힙니다",
    "<b>The scikit-learn version</b> — pinned at 1.8.0": "<b>scikit-learn 버전</b> — 1.8.0 으로 고정되어 있습니다",
    "<b>Any path around the gate</b> — the one entrance to a recommendation is <code>recommend()</code>":
        "<b>관문을 우회하는 경로</b> — 추천으로 가는 입구는 <code>recommend()</code> 하나뿐입니다",
}
