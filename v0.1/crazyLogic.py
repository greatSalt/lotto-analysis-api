import pandas as pd

def get_crazy_analysis(df):
    if df.empty:
        return pd.DataFrame()

    df_sorted = df.sort_values(by='round', ascending=True)
    latest_round = int(df_sorted['round'].max())
    results = []

    for num in range(1, 46):
        # 1. 전체 출현 여부 리스트
        appearances_bool = []
        for row in df_sorted.itertuples():
            win_nums = [row.n1, row.n2, row.n3, row.n4, row.n5, row.n6]
            appearances_bool.append(num in win_nums)
        
        # --- [A] 연속 지수 (Streak Score) : 기존 코드 유지 ---
        curr_streak = 0
        for app in reversed(appearances_bool):
            if app: curr_streak += 1
            else: break
        
        # 현재 안 나오고 있는 번호는 분석 제외
        if curr_streak == 0: continue 

        streaks = []
        temp = 0
        for app in appearances_bool:
            if app: temp += 1
            else:
                if temp > 0: streaks.append(temp)
                temp = 0
        if temp > 0: streaks.append(temp)
        max_streak = max(streaks) if streaks else 1
        
        # 기존 공식 유지
        streak_score = ((max_streak - curr_streak + 1) / max_streak) * 100
        streak_score = max(0, min(100, streak_score))

        # --- [B] 징검다리 탄성 지수 (정교화된 Bridge Score) ---
        recent_10 = appearances_bool[-10:]
        indices = [i for i, val in enumerate(recent_10) if val]
        
        if len(indices) >= 2:
            # 간격(Gap) 계산: 당첨 사이의 회차 수
            gaps = [indices[i] - indices[i-1] - 1 for i in range(1, len(indices))]
            avg_gap = sum(gaps) / len(gaps)
            
            # 탄성 공식: 평균 간격이 1(한 번 걸러 한 번)일 때 최적
            # 간격이 너무 넓거나(느슨함) 너무 좁으면(단순 연속) 점수가 조정됨
            elasticity = max(0, 100 - (abs(1.0 - avg_gap) * 40))
            
            # 최근성 가중치: 마지막 출현이 멀어질수록 탄성 감소
            recency_bonus = (indices[-1] + 1) * 10 # 최근에 나올수록 높은 점수
            bridge_score = (elasticity * 0.7) + (recency_bonus * 0.3)
        else:
            # 최근 10회 중 1번 이하로 나왔으면 탄성이 없다고 판단
            bridge_score = sum(recent_10) * 20 

        bridge_score = min(100, max(0, bridge_score))

        # --- [C] 통합 점수 합산 (6:4 비중 유지) ---
        total_score = (streak_score * 0.6) + (bridge_score * 0.4)

        results.append({
            "번호": num,
            "현재연속": curr_streak,
            "최근조밀도": f"{sum(recent_10)}/10",
            "연속점수": round(streak_score, 1),
            "징검다리점수": round(bridge_score, 1),
            "통합크레이지점수": round(total_score, 1)
        })

    return pd.DataFrame(results)
