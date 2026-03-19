import pandas as pd

def get_crazy_analysis(df):
    if df.empty:
        return pd.DataFrame()

    df_sorted = df.sort_values(by='round', ascending=True)
    results = []

    for num in range(1, 46):
        appearances_bool = []
        for row in df_sorted.itertuples():
            win_nums = [row.n1, row.n2, row.n3, row.n4, row.n5, row.n6]
            appearances_bool.append(num in win_nums)
        
        # --- [A] 현재 연속 출현(Curr) 및 스킵 이력 계산 ---
        curr_streak = 0
        skips = []
        temp_skip = 0
        
        for app in appearances_bool:
            if app:
                if temp_skip > 0: 
                    skips.append(temp_skip) # 당첨 전까지 쉰 기간 기록
                temp_skip = 0
            else:
                temp_skip += 1
        
        # 현재 연속 계산 (뒤에서부터)
        for app in reversed(appearances_bool):
            if app: curr_streak += 1
            else: break
        
        # [사용자 설정 유지] 현재 미출현 번호도 분석에 포함
        # if curr_streak == 0: continue 

        # --- [B] 역대 최대 연속 출현(Max) 및 스킵 주기 지표 ---
        avg_skip = sum(skips) / len(skips) if skips else 0 # 평균적으로 쉬는 기간
        last_skip = skips[-1] if skips else 0             # 이번에 나오기 전 쉰 기간
        
        streaks = []
        temp_s = 0
        for app in appearances_bool:
            if app: temp_s += 1
            else:
                if temp_s > 0: streaks.append(temp_s)
                temp_s = 0
        if temp_s > 0: streaks.append(temp_s)
        max_streak = max(streaks) if streaks else 1
        
        # [원본 유지] 최대 연속 출현이 1인 번호는 제외
        if max_streak <= 1: continue

        # --- [C] 기존 공식 유지: (Max - Curr) / Max * 100 ---
        streak_score = ((max_streak - curr_streak) / max_streak) * 100
        streak_score = max(0, min(100, streak_score))

        # --- [D] 징검다리 탄성 지수 (Bridge Score) - 원본 로직 보존 ---
        recent_10 = appearances_bool[-10:]
        indices = [i for i, val in enumerate(recent_10) if val]
        
        if len(indices) >= 2:
            gaps = [indices[i] - indices[i-1] - 1 for i in range(1, len(indices))]
            avg_gap = sum(gaps) / len(gaps)
            elasticity = max(0, 100 - (abs(1.0 - avg_gap) * 40))
            recency_bonus = (indices[-1] + 1) * 10 
            bridge_score = (elasticity * 0.7) + (recency_bonus * 0.3)
        else:
            bridge_score = sum(recent_10) * 20 

        bridge_score = min(100, max(0, bridge_score))

        # --- [E] 통합 점수 (6:4 비중) ---
        total_score = (streak_score * 0.6) + (bridge_score * 0.4)

        results.append({
            "번호": num,
            "현재연속": curr_streak,
            "최대연속": max_streak,
            "평균스킵": round(avg_skip, 1),      # 추가: 독립성 판단 지표 1
            "직전스킵": last_skip,               # 추가: 독립성 판단 지표 2
            "연속점수": round(streak_score, 1),
            "징검다리점수": round(bridge_score, 1),
            "통합크레이지점수": round(total_score, 1)
        })

    return pd.DataFrame(results)
