# seqopt — 실험실 측정을 위한 순차 최적화

*[English](README.md)* · 프로그램 자체도 한국어/영어를 지원합니다 — 시작 화면과 **Language** 메뉴에서 바꿀 수 있고, 첫 실행 때는 OS 언어를 따릅니다.

**측정값을 넣으면 다음에 어떤 조건을 측정할지 알려주고 —
그 조언을 믿어도 되는지부터 판정합니다.**

▶ **[순차 최적화란? — 인터랙티브 설명](https://euichanlee0608-svg.github.io/seqopt/)**
 · 5분, 설치 없음, 한국어·영어. 가우시안 프로세스가 브라우저 안에서 돌고,
그림은 이 저장소의 진단 코드가 그린 것과 같습니다.

핵심은 뒷부분입니다. 다음 실험을 제안하는 도구는 이미 많습니다. 어느 것도
알려주지 않던 것은 그 제안이 의미가 있는지였습니다 — 그래서 이 프로그램은
**자기 조언의 신뢰도를 먼저 검사하고, 데이터가 받쳐주지 못하면 조언을 거부합니다.**

### 고를 것이 없다

| 도구 | 사용자가 골라야 하는 것 |
|---|---|
| AutoOED | 대리모델 · 획득함수 · 다목적 솔버 · 선택 전략 — 드롭다운 4개 |
| MADGUI | ElasticNet / RandomForest / XGBoost · 교차검증 방식 |
| OPTIMEO | DoE 종류 · 모델 · 획득함수 |
| **seqopt** | **없음** — 커널 고정 · EI 고정 · 모델 고정 |

고정할 수 있는 이유가 관문입니다. 데이터가 나쁠 때 다른 도구는 모델 메뉴를
내밀어 헤매게 하지만, 이 프로그램은 **"모델을 바꿔도 소용없다"**고 판정하고
추천을 잠급니다. 앞에서 치운 것들은 각 화면의 *고급 ▸* 접힘 안에 그대로
있습니다 — 미룬 것이지 없앤 것이 아닙니다.

### 관문 4개 — 하나라도 실패하면 추천이 잠긴다

| | 관문 | 무엇을 보나 | 실패하면 |
|---|---|---|---|
| ① | 후보 수 | 선언한 설계 공간(범위 × 격자 간격)의 후보가 예산보다 많은가? | 전부 측정하는 편이 낫다 |
| ② | 응답면 학습가능성 | 모델이 배우고 있는가(LOOCV R² > 0)? | 모델을 바꿔도 소용없다 |
| ③ | 판별력 | 조건 간 차이가 측정 흔들림보다 큰가? | 반복 측정을 늘려라 |
| ④ | 반복 측정 | 같은 조건을 다시 잰 적이 있는가? | 흔들림 자체를 알 수 없다 |

잠금은 UI 규율이 아니라 **반환 타입**으로 강제됩니다: `recommend()`는
`Recommendation | Locked`를 돌려주고, `Locked`에는 **제안 필드가 아예 없어서**
화면이 잘못 쓸 것이 없습니다.

---

## Windows — 그냥 실행 (파이썬 불필요)

1. 이 저장소의 **Actions** 탭을 엽니다
2. 왼쪽에서 **windows-build**를 고르고 가장 최근의 초록 ✅ 실행을 클릭합니다
3. 맨 아래 *Artifacts*에서 **`seqopt-windows`**를 내려받습니다
4. **zip 을 먼저 풉니다** (zip 뷰어 안에서 exe 를 실행하면 실패합니다)
5. 풀린 `seqopt` 폴더 안의 **`seqopt.exe`**를 더블클릭합니다

> 가장 흔한 실수 두 가지:
> - **zip 안에서 실행** — 탐색기는 zip 을 폴더처럼 보여주지만, 거기서
>   더블클릭하면 exe 만 풀리고 옆에 있어야 할 파일들은 안 풀립니다.
> - **exe 만 옮기기** — 자기 폴더가 필요합니다. 폴더째 옮기세요.
>   (그 폴더 구조 덕에 약 4초 만에 열립니다.)
>
> 파란 *SmartScreen* 창이 뜨면 **추가 정보 → 실행**을 누르세요 — 서명되지
> 않은 바이너리라서 뜨는 것입니다.

그래도 안 되면 명령 프롬프트에서 `seqopt.exe --selftest`를 실행하세요:
무엇이 빠졌는지 말해주고 exe 옆에 `selftest.txt`를 남깁니다. 시작 과정은
단계별로 `%USERPROFILE%\.seqopt\seqopt.log`에 기록되고(무거운 라이브러리를
읽는 동안 스플래시 카드가 같은 단계를 보여줍니다), 충돌은
`%USERPROFILE%\.seqopt\error.log`에 상세히 남습니다.

내려받기 전에 화면을 보고 싶다면 — 같은 CI 실행이
**`seqopt-windows-shots`**도 올립니다. 빌드 직후 러너의 실제 Windows 화면에서
찍은, 번들 예제 전부의 전 탭 캡처입니다(`en/`·`ko/` 두 언어).

### Windows 에서 직접 빌드

1. [Python 3.11](https://www.python.org/downloads/release/python-3119/) 설치
   (**"Add python.exe to PATH"** 체크)
2. 이 페이지에서 *Code → Download ZIP*, 압축 해제
3. **`packaging\build_windows.bat`** 더블클릭
4. 결과물은 **`dist\seqopt\seqopt.exe`**

배치 파일은 venv 를 만들고 의존성을 설치한 뒤 **회귀 테스트를 돌리고**,
통과했을 때만 빌드합니다 — 판정이 틀린 프로그램은 포장되면 안 됩니다.

## macOS / 소스에서

```bash
git clone https://github.com/euichanlee0608-svg/seqopt && cd seqopt
uv venv --python 3.11 .venv          # 또는: python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt PySide6 matplotlib reportlab
.venv/bin/python app.py
```

번들 앱은 `packaging/build_macos.sh` → `dist/seqopt.app`

---

## 첫 실행

예제 두 개가 함께 들어 있습니다:

- **모의 열처리 (결정화도)** — 시뮬레이션 데이터, 온도 × 시간 격자에서 42회
  측정(후보 조건 252개, 예산 60). 관문 4개를 모두 통과하므로 추천이 어떤
  모습이고 왜 그런지 볼 수 있습니다. 참 최적점은 290 °C / 40 min 이고, 실제로
  그것이 나옵니다.
- **P3HT:CNT 전도도** — 공개된 박막 실측 데이터 48조건(*Adv. Funct. Mater.*
  2021, 공개 데이터셋). 데이터 탭에서 행이나 반복 측정을 지워 보면 관문이
  잠기는 것을 볼 수 있습니다.

| 탭 | 하는 일 |
|---|---|
| 1 설정 | 장비가 실제로 맞출 수 있는 격자 간격으로 조절 변수(입력)를 정의하고, 필요하면 합 제약(예: 분율 합 100 %), 목표, 예산을 정합니다 |
| 2 데이터 | Excel/CSV 가져오기, 붙여넣기, 직접 입력; Ctrl+Z 되돌리기 |
| 3 **진단** | **이 도구의 심장** — 관문 4개의 판정, 모든 계산을 펼쳐서 보여줍니다 |
| 4 모델 | 응답면 · 불확실성 · EI · 민감도 |
| 5 추천 | 선언한 격자 위, 제약 안의 다음 조건 — 관문을 통과할 때까지 잠김 |
| 6 리포트 | PDF · 계산 기록 · 모든 숫자를 재현하는 스크립트 |
| ? 도움말 | 검색되는 답변, 항목마다 코드 참조가 붙어 있습니다 |

모든 숫자는 근거로 거슬러 올라갑니다: 진단 탭은 σw/σb/D 뒤의 조건별 표를
펼쳐 보여주고, 리포트에는 전체 계산 기록이 실리며, 내보낸 파이썬 스크립트는
원본 데이터만으로 같은 숫자를 다시 냅니다.

---

## 개발자용

**구조** — `core/`(계산, GUI 를 절대 import 하지 않음) ↔ `ui/`(화면, 판단하지
않음). `core/`의 모든 것은 CLI 에서 돕니다.

대리모델과 획득함수는 레지스트리 플러그인입니다 — 클래스 하나면 되고 다른
변경은 없습니다:

```python
@ACQUISITIONS.register("PI")
class ProbabilityOfImprovement:
    label = "PI — probability of improvement"
    supports_continuous = True
    def score(self, model, X, best, rng=None): ...
    def describe(self): return "PI"
```

**관문은 플러그인이 아닙니다.** 받쳐주지 못하는 데이터로 최적화하기를 거부하는
것이 이 도구의 존재 이유입니다(`docs/ARCHITECTURE.md`).

**화면에 EI · UCB · Thompson 만 있는 이유.** 전역 탐색 대안 4종(max-value
entropy search, 탐색을 섞은 EI, GP-UCB 스케줄, Thompson 변형)을 시험함수 8종 ×
씨앗 10개로, 재기 전에 정한 규칙 아래 비교했습니다 — 다봉 함수에서 EI 를
이기면서 단봉 함수에서 지지 않을 때만 싣는다. 아무것도 넘지 못했습니다.
수치는 `docs/bench_global.json`, 정리는 `docs/GLOBAL_SEARCH.md`, 후보 코드는
`packaging/bench_global.py`에 있고, 어느 날 후보가 EI 를 이기면
`tests/test_global.py`가 실패합니다 — 그것이 승격 신호입니다.

**두 언어.** 사용자에게 보이는 문자열은 전부 `tr()`을 거치고, 한국어는
`core/lang/ko_*.py`에 있습니다. 새 문자열을 추가하는 법과 그것을 강제하는
테스트(`tests/test_i18n.py` — 맨 문자열 0, 한국어 누락 0;
`tests/test_layout.py` — 두 언어 × 두 창 크기에서 잘린 글자 0)는
`docs/ARCHITECTURE.md`의 i18n 절에 있습니다.

```bash
.venv/bin/python -m pytest tests -q
```

테스트는 두 종류의 기대값에 앵커돼 있습니다: **합성 실험실 스프레드시트**
(`tests/data/make_synthetic.py` — 독립된 numpy 식으로 생성, 씨앗 고정, 이
도구가 잡으려는 바로 그 상황에 놓이도록 설계)와 공개 데이터셋 3종
(P3HT-CNT · AgNP · Perovskite,
[PV-Lab/Benchmarking](https://github.com/PV-Lab/Benchmarking))에 대한
**원 검증 연구의 수치**입니다.

바꾸지 말아야 할 세 가지(상세는 `docs/ARCHITECTURE.md`):

1. **GP 커널** — 회귀 기대값을 재현하는 조합은 정확히 하나뿐입니다
2. **LOOCV 폐형식화** — 200배 빨라지지만 관문 판정이 뒤집힙니다. 느린 것이 맞습니다
3. **`scikit-learn==1.8.0` 핀** — 회귀 기대값이 그 버전에서 만들어졌습니다

## 유래

이 도구는 한 소자 연구실의 의사결정 연구에서 나왔습니다 — 순차 베이지안
최적화를 도입할 것인가. 공개 데이터셋 3종에서는 이 방법이 실제 측정을
아꼈지만, 연구실 자체 데이터에서는 모든 데이터셋이 관문에 걸렸습니다 —
그래서 결론은 *아직 아니다*였고, 그 관문이 이 프로그램이 됐습니다. 연구실의
원본 데이터는 이 저장소에 **없습니다**. 공개 데이터셋과 같은 구조의 합성
대체 데이터만 있습니다.

## 라이선스

MIT — [LICENSE](LICENSE).
