
def predict_iteration_count(recent_data, current_winning_nums):
    """
    recent_data: 최근 10~20회차 당첨 번호 목록
    current_winning_nums: 직전 회차(1217회) 당첨 번호와 각 번호의 max_streak 정보
    """
    # 1. 최근 이월수 출현 흐름 분석 (Moving Average)
    # 최근 5회차 동안 이월수가 평균 몇 개 나왔는지 계산
    recent_iter_counts = [calc_iter(r) for r in recent_data[:5]]
    avg_iter = sum(recent_iter_counts) / len(recent_iter_counts)
    
    # 2. 직전 번호들의 '재출현 에너지' 합산
    # 각 번호의 (max_streak - curr_streak)이 클수록 이월 가능성 상승
    total_reappearance_energy = sum([n.max_streak - n.curr_streak for n in current_winning_nums])
    
    # 3. 예측 로직 (Heuristic)
    if avg_iter >= 2.0: # 최근에 너무 많이 이월됨 -> 회귀 본능
        predicted_count = 1 
        reason = "최근 5회차 이월 과다 출현으로 인한 통계적 회귀(평균 1개로 수렴) 예상"
    elif total_reappearance_energy >= 5: # 기세가 남은 번호가 많음
        predicted_count = 2
        reason = "직전 당첨번호 중 최대연속 기록에 미치지 못한 '기세 잔여 번호' 다수 포착"
    else:
        predicted_count = 1
        reason = "표준 확률(43%) 및 최근 안정적 흐름에 따른 정석적 1개 예상"
        
    return predicted_count, reason
