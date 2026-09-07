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
}
