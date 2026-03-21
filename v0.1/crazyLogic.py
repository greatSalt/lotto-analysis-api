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
        
        # --- [A] 스킵 및 연속 출현 데이터 추출 ---
        skips = []
        streaks = []
        temp_skip = 0
        temp_streak = 0
        
        for app in appearances_bool:
            if app:
                # 스킵 기록 저장
                if temp_skip > 0: 
                    skips.append(temp_skip)
                temp_skip = 0
                # 연속 출현 기록 시작
                temp_streak += 1
            else:
                # 연속 출현 기록 저장
                if temp_streak > 0:
                    streaks.append(temp_streak)
                temp_streak = 0
                # 스킵 기록 시작
                temp_skip += 1
        
        # 마지막 기록 처리
        if temp_streak > 0: streaks.append(temp_streak)
        
        # --- [B] 핵심 지표 계산 ---
        current_skip = temp_skip  # 현재 진행 중인 미출현 기간
        avg_skip = sum(skips) / len(skips) if skips else 1.0
        last_skip = skips[-1] if skips else 0
        max_streak = max(streaks) if streaks else 1
        
        # 현재 연속 출현 계산 (뒤에서부터)
        curr_streak = 0
        for app in reversed(appearances_bool):
            if app: curr_streak += 1
            else: break

        # --- [C] 에너지 지수 및 임계점 (사용자 요청 핵심 로직) ---
        # 공식: 현재 얼마나 안 나왔는가 / 평소에 얼마나 안 나오는가
        energy_index = current_skip / avg_skip if avg_skip > 0 else 0
        is_critical = energy_index >= 1.0

        # --- [D] 점수 산출 로직 (기존 유지) ---
        streak_score = ((max_streak - curr_streak) / max_streak) * 100
        streak_score = max(0, min(100, streak_score))

        # 징검다리 점수
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
        total_score = (streak_score * 0.6) + (bridge_score * 0.4)

        # --- [E] 결과 수집 ---
        results.append({
            "번호": num,
            "현재연속": curr_streak,
            "최대연속": max_streak,
            "연속점수": round(streak_score, 1),
            "징검다리점수": round(bridge_score, 1),
            "평균스킵": round(avg_skip, 1),
            "직전스킵": last_skip,
            "현재스킵": current_skip,
            "에너지지수": round(energy_index, 2),
            "임계점": "🔥도달" if is_critical else "⏳충전",
            "통합크레이지점수": round(total_score, 1)
        })

    return pd.DataFrame(results)
