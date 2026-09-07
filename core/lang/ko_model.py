# -*- coding: utf-8 -*-
"""Korean for ui/tab_recommend.py · ui/tab_model.py · core/recommend.py · core/acquisition.py · core/surface.py · core/surrogate.py. Keys are the English strings as written in the code (core/i18n.py)."""

KO: dict[str, str] = {
    'Default — expected improvement (EI)':
        '기본 — 기대 개선량 (EI)',
    'Use this in most cases. It scores each candidate by how much it is expected to beat the best so far.':
        '대부분 이걸 쓰면 됩니다. 지금까지 최선보다 얼마나 나아질지를 기댓값으로 잽니다.',
    'Explore wider — upper confidence bound (UCB)':
        '넓게 탐색 — 신뢰상한 (UCB)',
    'When the terrain is still unknown. Looks harder at uncertain regions. Pushing too far backfires — raising b from 1 to 4 dropped the global-optimum hit rate from 90% to 61% in the validation study.':
        '아직 지형을 모를 때. 불확실한 곳을 더 봅니다. 다만 너무 밀면 오히려 나빠집니다 — 검증에서 b 를 1→4 로 키우자 전역최적 도달률이 90%→61% 로 떨어졌습니다.',
    'Diversify — Thompson sampling':
        '다양하게 — 톰슨 표본추출',
    'When you receive several suggestions at once. Each draw picks a different place, so candidates do not pile up in one spot. Running alone, the default (EI) is better.':
        '한 번에 여러 개를 받을 때. 매번 다른 곳을 고르므로 후보가 한곳에 몰리지 않습니다. 혼자 쓸 때는 기본(EI)이 낫습니다.',
    'EI (expected improvement)':
        'EI (기대 개선량)',
    'UCB (b = {b})':
        'UCB (b = {b})',
    'Thompson sampling':
        'Thompson 표본추출',
    'The requirements were not met, so no recommendation is given.':
        '요건을 통과하지 못해 추천을 내지 않습니다.',
    'A suggestion lies outside the measured range — the model has never learned what is out there.':
        '실측 범위 밖을 제안했습니다 — 모델이 그 바깥을 배운 적은 없습니다.',
    'No unmeasured candidates remain. Widen the design range or close out the budget.':
        '아직 재지 않은 후보가 없습니다. 설계 범위를 넓히거나 예산을 끝내세요.',
    'The maximum acquisition value has stayed below 1% of the response range 3 times in a row — there is almost nothing left to gain by measuring more.':
        '최대 획득값이 응답 범위의 1% 미만으로 3회 연속입니다 — 더 재도 나아질 여지가 거의 없습니다.',
    'Gaussian process (Matern · ARD)':
        '가우시안 프로세스 (Matern · ARD)',
    'Random forest (for comparison)':
        '랜덤 포레스트 (비교용)',
    'Recommend — the next condition to measure':
        '추천 — 다음에 잴 조건',
    'Opens only after the diagnostic requirements pass. A recommendation comes as condition values, a suggested replicate count, and its evidence.':
        '진단 요건을 통과했을 때만 엽니다. 추천은 조건값과 권장 반복 횟수, 그 근거로 나옵니다.',
    'It is locked — can I not just use it anyway?':
        '잠겼는데 그냥 쓰면 안 되나요?',
    'Picking method':
        '고르는 방법',
    'Recommend next candidates':
        '다음 후보 추천',
    'Force a recommendation despite unmet requirements':
        '요건 미달이어도 강제로 추천받기',
    'Only after reading the warnings.\nReports built in this state carry a "generated with requirements unmet" stamp.':
        '경고를 읽고도 진행할 때만 쓰세요.\n이 상태에서 만든 리포트에는 ‘요건 미달 상태에서 생성됨’ 이 박힙니다.',
    '1 suggestion at a time':
        '한 번에 1개씩 추천',
    '{n} suggestions at a time':
        '한 번에 {n}개씩 추천',
    'At a time':
        '한 번에',
    'Receive several at once. Each picked point assumes its predicted\nmean as if observed, then the next is chosen (kriging believer).\nWhether batches beat sequential picking has not been validated.':
        '여러 개를 한꺼번에 받습니다. 이미 뽑은 점은 예측 평균을\n관측값처럼 두고 다음 점을 고릅니다 (kriging believer).\n배치가 순차보다 나은지는 아직 검증하지 않았습니다.',
    'Exploration strength b':
        '탐색 세기 b',
    'Larger pushes further into uncertainty. Do not casually raise the default 2.0.':
        '크게 하면 불확실한 쪽으로 더 나갑니다. 기본 2.0 을 함부로 올리지 마세요.',
    'Measure this next':
        '다음 측정 조건',
    'Other candidates':
        '다른 후보',
    'Insert into the data table':
        '측정표에 넣기',
    'Pre-fills the suggested conditions as gray rows on the Data tab.\nThey become real once you enter the measured values.':
        '제안 조건을 데이터 탭에 회색 행으로 미리 넣습니다.\n측정한 값을 채우면 확정됩니다.',
    'Export instruction sheet (CSV)':
        '지시서 CSV 내보내기',
    'Saves condition values + suggested replicates + the evidence, as a table.':
        '조건값 + 권장 반복 횟수 + 제안 근거를 표로 저장합니다.',
    '<b style=\'color:{c}\'>{headline}</b><ul style=\'margin:6px 0\'>{reasons}</ul>Follow the prescription on the Diagnose tab first. If you must proceed anyway, turn on "Force a recommendation" above — the result will carry the mark.':
        "<b style='color:{c}'>{headline}</b><ul style='margin:6px 0'>{reasons}</ul>진단 탭의 처방을 먼저 따르세요. 그래도 진행해야 한다면 위의 ‘요건 미달이어도 강제로 추천받기’ 를 켜면 되지만, 그 결과에는 표시가 남습니다.",
    'predicted {pred} · acquisition {acq} · suggested reps ×{n}':
        '예측 {pred} · 획득값 {acq} · 권장 반복 ×{n}',
    '<b>1 condition suggested.</b>':
        '<b>조건 1개를 제안합니다.</b>',
    '<b>{n} conditions suggested.</b>':
        '<b>조건 {n}개를 제안합니다.</b>',
    'best measured so far {best}':
        '지금 최선 측정값 {best}',
    "<b style='color:{c}'>This recommendation was forced with requirements unmet.</b> The report will say so.":
        "<b style='color:{c}'>요건 미달 상태에서 강제로 만든 추천입니다.</b> 리포트에 그 사실이 박힙니다.",
    "<b style='color:{c}'>Stopping advised</b> — {why}":
        "<b style='color:{c}'>종료 권고</b> — {why}",
    '"Insert into the data table" pre-fills these as gray rows on the Data tab. Enter the measured values to make them real.':
        '‘측정표에 넣기’ 를 누르면 데이터 탭에 회색 행으로 들어갑니다. 값을 채우면 확정됩니다.',
    'Press "Recommend next candidates" to pick what to measure next from the current data.':
        '‘다음 후보 추천’ 을 누르면 지금 데이터로 다음에 잴 조건을 고릅니다.',
    'Requirements are unmet':
        '요건 미달 상태입니다',
    'There is no evidence this data can support a recommendation.\n\nProceed anyway and the results and the report will be marked "generated with requirements unmet".':
        '이 데이터로는 추천을 믿을 근거가 없습니다.\n\n그래도 진행하면 결과와 리포트에 ‘요건 미달 상태에서 생성됨’ 이 표시됩니다.',
    'suggested · {acq} · predicted {pred}':
        '추천 · {acq} · 예측 {pred}',
    'Export instruction sheet':
        '지시서 내보내기',
    'Exported':
        '내보냈습니다',
    '{path}\n\nFill in the values after measuring.':
        '{path}\n\n측정한 뒤 값을 채워 넣으세요.',
    'outside measured range':
        '실측 범위 밖',
    '≈ {value} (log10 {mean} ± {sd})':
        '≈ {value} (log10 값 {mean} ± {sd})',
    'predicted':
        '예측',
    'predicted mean':
        '예측 평균',
    'predicted mean (log10)':
        '예측 평균 (log10)',
    'uncertainty σ':
        '불확실성 σ',
    'uncertainty σ (log10)':
        '불확실성 σ (log10)',
    'σ (log10)':
        'σ (log10)',
    'acq.':
        '획득값',
    'acq. value':
        '획득값',
    'suggested reps':
        '권장 반복',
    'note':
        '메모',
    'evidence':
        '근거',
    'caution':
        '주의',
    'generated with requirements unmet':
        '요건 미달 상태에서 생성됨',
    'Model — the surface drawn from the current data':
        '모델 — 지금 데이터로 그린 응답면',
    'The terrain as the model sees it, plus the validation figures that say how far to trust it.':
        '모델이 본 지형과, 그 모델을 얼마나 믿을 수 있는지 보여 주는 검증 그림입니다.',
    'Slice':
        '절단면',
    'Sensitivity — which knob matters':
        '민감도 — 어느 손잡이가 세게 듣는가',
    'Surface':
        '응답면',
    'Validation':
        '검증 그림',
    'Top left the trajectory, top right learnability (LOOCV), bottom left the replicate scatter — how far repeats of the same condition wobble — and bottom right the terrain roughness.':
        '왼쪽 위는 궤적, 오른쪽 위는 학습가능성(LOOCV), 왼쪽 아래는 반복 산포 — 같은 조건을 다시 재면 얼마나 흔들리는지 — 오른쪽 아래는 지형 거칠기입니다.',
    'Next-candidate method: {method}  (change it on the Recommend tab)':
        '다음 후보 고르는 방식 : {method}  (추천 탭에서 바꿉니다)',
    "⚠ This surface is <b>unlearned</b> (LOOCV R² = {r2} ≤ 0). Its shape comes from the kernel's default assumptions more than from the data. <b>Do not draw conclusions from the shape.</b>":
        '⚠ 이 응답면은 <b>학습되지 않았습니다</b> (LOOCV R² = {r2} ≤ 0). 모양은 데이터가 아니라 커널의 기본 가정에서 나온 것에 가깝습니다. <b>모양을 근거로 결론을 내지 마세요.</b>',
    'The surface is drawn once there are at least 3 conditions.':
        '조건이 3개 이상이어야 응답면을 그립니다.',
    'UNLEARNED  R² < 0':
        '학습되지 않음  R² < 0',
    'predicted mean μ':
        '예측 평균 μ',
    'Response surface — measured points and the uncertainty around them':
        '응답면 — 실측점과 그 둘레의 불확실성',
    '{kind} — where the next measurement teaches the most':
        '{kind} — 다음에 재면 가장 많이 배우는 곳',
    'μ predicted mean · σ uncertainty, darker is less known · {kind} where to measure next':
        'μ 예측 평균 · σ 불확실성, 짙을수록 모릅니다 · {kind} 다음에 잴 곳',
    'Top left: the 3D surface with residual drop lines.':
        '왼쪽 위 : 잔차 수선을 세운 3D 곡면.',
    'pinned at: {where}<br>{n} measured points near this slice · closest measured condition: {nearest}':
        '고정 : {where}<br>이 면 근처의 실측점 {n}개 · 가장 가까운 실측 조건 {nearest}',
    "<span style='color:{c}'>{kind} max: {where} · value {value} = {pct}% of the response range — there is almost nothing left to learn anywhere</span>":
        "<span style='color:{c}'>{kind} 최대 : {where} · 값 {value} = 응답 범위의 {pct}% — 어디를 재도 배울 것이 거의 없습니다</span>",
    '{kind} max: {where} · value {value}':
        '{kind} 최대 : {where} · 값 {value}',
    'This surrogate has no length scales, so sensitivity cannot be computed.':
        '이 대리모델은 길이척도가 없어 민감도를 낼 수 없습니다.',
    'influence [%]':
        '영향 [%]',
    'A <b>longer bar is more sensitive</b> (1 / length scale).':
        '막대가 <b>클수록 민감</b>합니다 (1/길이척도).',
    "No influence was detected for '{names}'.":
        '‘{names}’ 은 영향이 잡히지 않았습니다.',
    'measurements (cumulative)':
        '측정 횟수 (누적)',
    'Trajectory — best measured value so far':
        '궤적 — 지금까지의 최선 측정값',
    'Computing learnability…':
        '학습가능성 계산 중…',
    'perfect prediction':
        '완벽한 예측',
    'always answer the mean':
        '전체 평균만 답하기',
    'measured (condition mean)':
        '실측 (조건 평균)',
    'LOOCV prediction':
        'LOOCV 예측',
    'Learnability R² = {r2}':
        '학습가능성 R² = {r2}',
    'condition mean':
        '조건 평균',
    'condition (sorted by mean)':
        '조건 (평균 오름차순)',
    'Replicate scatter':
        '반복 산포',
    'sill {v}':
        '문턱값 {v}',
    'nugget {v}':
        '너깃 {v}',
    'distance between conditions (normalized)':
        '조건 사이 거리 (정규화)',
    'semivariance γ':
        '반변이도 γ',
    'Terrain roughness — nugget ratio {ratio}':
        '지형 거칠기 — 너깃비 {ratio}',
}
