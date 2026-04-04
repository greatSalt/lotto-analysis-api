def predict_iteration_count(df, current_nums_info):
    # 1. 최근 5회차간의 실제 이월수 개수 리스트 생성
    # (n1~n6 컬럼을 집합으로 변환하여 윗행과 교집합 개수 산출)
    iter_history = []
    for i in range(len(df) - 1):
        curr = set(df.iloc[i][['n1', 'n2', 'n3', 'n4', 'n5', 'n6']])
        prev = set(df.iloc[i+1][['n1', 'n2', 'n3', 'n4', 'n5', 'n6']])
        iter_history.append(len(curr & prev))
    
    recent_iters = iter_history[:5] # 최근 5회차 이월수 기록
    avg_iter = sum(recent_iters) / len(recent_iters) if recent_iters else 0

    # 2. 직전 번호들의 '기세 잔여' 에너지 (10번, 31번 등)
    # (최대연속 > 현재연속) 인 번호들의 개수
    potential_energy = len(current_nums_info[current_nums_info['현재연속'] < current_nums_info['최대연속']])

    # 3. 최종 예측 로직
    if avg_iter <= 0.8 and potential_energy >= 2:
        count = 2
        reason = f"최근 이월 흐름이 저조({avg_iter:.1f}개)하고, 기세가 남은 번호가 {potential_energy}개 포착되어 2개 이월 가능성 높음"
    elif avg_iter >= 1.6:
        count = 1
        reason = f"최근 이월 과다 출현({avg_iter:.1f}개)에 따른 통계적 회귀로 1개 예상"
    else:
        count = 1
        reason = "표준 출현 확률(43%) 및 안정적 흐름에 근거하여 1개 예상"

    return count, reason
