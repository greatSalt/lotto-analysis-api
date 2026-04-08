
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
        
        # 수정 후 (분석 범위와 실제 데이터 개수 중 작은 값을 사용)
        #actual_range = min(len(df), 10) # 최대 10회차까지만 보되, 데이터가 적으면 그만큼만 계산
        # 또는 사용자가 설정한 analyze_range를 직접 사용하려면:
        actual_range = min(len(df), analyze_range)
        
        # 3. 최근 쏠림도 계산 (최근 {analyze_range}회차 평균 대비)
        recent_avg = sum([
            len([n for n in [df.iloc[k][f'n{j}'] for j in range(1, 7)] if start <= n <= end]) 
            for k in range(actual_range)
        ]) / actual_range

        bias_index = curr_count / recent_avg if recent_avg > 0 else 1
        
        # 4. 명확한 이유 근거 생성
        is_empty = prob > 55 and bias_index > 1.1 # 확률 55% 이상 & 최근 쏠림 1.1배 이상 시 멸 확정
        final_decision[name] = {
            'is_empty': is_empty,
            'prob': prob,
            'bias': bias_index,
            'reason': f"과거 동일패턴 시 멸 확률 {prob:.1f}% & 최근 평균 대비 {bias_index:.1f}배 과밀"
        }
        
    return final_decision

def color_rows(row, decision):
    """
    구간별 상태(멸/주의)에 따라 테이블 행의 색상을 결정하는 함수
    """
    num = row['번호']
    # 구간 판별
    zone = ""
    if 1 <= num <= 10: zone = '단번대'
    elif 11 <= num <= 20: zone = '10번대'
    elif 21 <= num <= 30: zone = '20번대'
    elif 31 <= num <= 40: zone = '30번대'
    else: zone = '40번대'
    
    # 스타일 결정
    if decision[zone]['is_empty']: # 확정 멸구간 (이미 필터링되었겠지만 안전장치)
        return ['background-color: #ffcccc'] * len(row)
    elif decision[zone]['prob'] > 40: # 주의 구간 (멸 확률 40% 초과)
        return ['background-color: #ffffcc'] * len(row) # 노란색 하이라이트
    return [''] * len(row)
    
#데이터프레임 스타일링 함수
def apply_strategy_style(df, decision):
    def row_style(row):
        num = row['번호']
        # 구간 확인용 헬퍼 로직
        zone = '단번대'
        if 11 <= num <= 20: zone = '10번대'
        elif 21 <= num <= 30: zone = '20번대'
        elif 31 <= num <= 40: zone = '30번대'
        elif 41 <= num <= 45: zone = '40번대'
        
        status = decision.get(zone, {'is_empty': False, 'prob': 0})
        # A. 확정 멸구간 (is_empty) -> 파란색 배경 / 흰색 글자
        if status['is_empty']:
            return ['background-color: #0000FF; color: #FFFFFF; font-weight: bold'] * len(row)
        # B. 주의 구간 (멸 확률 > 40%) -> 노란색 배경 / 검정 글자    
        elif status['prob'] > 40:
            return ['background-color: #ffff00; color: #000000; font-weight: bold'] * len(row)
        return [''] * len(row)
            
    return df.style.format(precision=1).apply(row_style, axis=1)
    