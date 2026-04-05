def predict_by_probability(df):
    # 1. 전체 이월수 히스토리 생성 (최신순 -> 과거순)
    iter_history = []
    for i in range(len(df) - 1):
        curr = set(df.iloc[i][['n1', 'n2', 'n3', 'n4', 'n5', 'n6']])
        prev = set(df.iloc[i+1][['n1', 'n2', 'n3', 'n4', 'n5', 'n6']])
        iter_history.append(len(curr & prev))
    
    # 2. 직전 회차(1217회)의 이월수 개수 확인
    last_iter_count = iter_history[0] 
    
    # 3. 과거 데이터에서 '직전 회차와 같은 개수'였던 사례들 찾기
    # 예: 과거에 이월수가 1개였을 때, 그 다음 회차는 어땠는가?
    next_counts = []
    for i in range(1, len(iter_history) - 1):
        if iter_history[i] == last_iter_count:
            next_counts.append(iter_history[i-1]) # '그다음' 결과 저장
            
    if not next_counts:
        return 1, "참조 데이터 부족으로 표준 확률 적용"

    # 4. 빈도수 계산 (0개, 1개, 2개...)
    prob_0 = next_counts.count(0) / len(next_counts) * 100
    prob_1 = next_counts.count(1) / len(next_counts) * 100
    prob_2 = next_counts.count(2) / len(next_counts) * 100
    
    # 5. 가장 확률이 높은 개수 선택
    max_prob = max(prob_0, prob_1, prob_2)
    if max_prob == prob_1:
        predicted = 1
    elif max_prob == prob_2:
        predicted = 2
    else:
        predicted = 0
        
    reason = f"과거 {last_iter_count}개 이월 후 다음 회차에 {predicted}개가 나온 실제 빈도는 {max_prob:.1f}%입니다."
    
    return predicted, reason, {0: prob_0, 1: prob_1, 2: prob_2}

def predict_with_numbers(df, current_nums_info):
    # 1. 개수 예측 (기존 로직 사용)
    predicted_count, reason, prob_dist = predict_by_probability(df)
    
    # 2. 개별 번호의 이월 확률 계산 (v2.3 복합 지표)
    # 기세 가중치 + 반등 지수 + 출현 빈도를 결합하여 점수화
    current_nums_info['이월확률'] = (
        (current_nums_info['반등지수'] * 30) +        # 반등 (30%)
        (current_nums_info['현재연속'] / current_nums_info['최대연속'] * 50) + # 기세 (50%)
        (current_nums_info['에너지지수'] * 10) +      # 에너지 (10%)
        (current_nums_info['탄성점수'] * 0.05) +      # 탄성 (5%)
        (current_nums_info['리듬점수'] * 0.05)        # 리듬 (5%)
    ).clip(0, 95) # 로또에 100%는 없으므로 95% 상한선
    
    # 확률 상위권 번호 추출
    top_targets = current_nums_info.sort_values(by='이월확률', ascending=False)
    
    # 예측 개수(predicted_count)만큼 번호 선정
    recommended_nums = top_targets.head(predicted_count)
    
    return predicted_count, reason, recommended_nums


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
            
