
def get_confirmed_empty_zone(df, analyze_range=100):
    zones = {
        '단번대': (1, 10), '10번대': (11, 20), '20번대': (21, 30), 
        '30번대': (31, 40), '40번대': (41, 45)
    }
    
    # 1. 현재 상태(직전 회차) 파악
    last_draw = [df.iloc[0][f'n{i}'] for i in range(1, 7)]
    zone_counts = {name: len([n for n in last_draw if s <= n <= e]) for name, (s, e) in zones.items()}
    
    final_decision = {}

    for name, (start, end) in zones.items():
        curr_count = zone_counts[name]
        
        # 2. 역사적 확률 계산 (analyze_range 내)
        history_match = 0
        history_empty_next = 0
        
        for i in range(1, min(len(df)-1, analyze_range)):
            # 과거에 현재와 같은 개수(curr_count)가 나왔던 지점 찾기
            prev_draw = [df.iloc[i][f'n{j}'] for j in range(1, 7)]
            prev_count = len([n for n in prev_draw if start <= n <= end])
            
            if prev_count == curr_count:
                history_match += 1
                # 그 다음 회차(i-1)가 멸(0개)이었는지 확인
                next_draw = [df.iloc[i-1][f'n{j}'] for j in range(1, 7)]
                if not any(start <= n <= end for n in next_draw):
                    history_empty_next += 1
        
        prob = (history_empty_next / history_match * 100) if history_match > 0 else 0
        
        # 3. 최근 쏠림도 계산 (최근 10회차 평균 대비)
        recent_10_avg = sum([len([n for n in [df.iloc[k][f'n{j}'] for j in range(1, 7)] if start <= n <= end]) for k in range(10)]) / 10
        bias_index = curr_count / recent_10_avg if recent_10_avg > 0 else 1
        
        # 4. 명확한 이유 근거 생성
        is_empty = prob > 55 and bias_index > 1.1 # 확률 55% 이상 & 최근 쏠림 1.1배 이상 시 멸 확정
        final_decision[name] = {
            'is_empty': is_empty,
            'prob': prob,
            'bias': bias_index,
            'reason': f"과거 동일패턴 시 멸 확률 {prob:.1f}% & 최근 평균 대비 {bias_index:.1f}배 과밀"
        }
        
    return final_decision
