import pandas as pd

def get_crazy_analysis(df):
    if df.empty:
        return pd.DataFrame()

    df_sorted = df.sort_values(by='round', ascending=True)
    latest_round = df_sorted['round'].max()
    results = []

    for num in range(1, 46):
        # 1. 출현 여부 리스트 생성
        appearances_bool = []
        for row in df_sorted.itertuples():
            win_nums = [row.n1, row.n2, row.n3, row.n4, row.n5, row.n6]
            appearances_bool.append(num in win_nums)
        
        # --- [A] 연속 지수 계산 (Streak Score) ---
        curr_streak = 0
        for app in reversed(appearances_bool):
            if app: curr_streak += 1
            else: break
        
        # 현재 안 나오고 있는 번호는 크레이지 분석에서 제외 (0점 처리 가능)
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
        
        # 연속 점수 (0~100)
        streak_score = ((max_streak - curr_streak + 1) / max_streak) * 100
        streak_score = max(0, min(100, streak_score))

        # --- [B] 징검다리 지수 계산 (Bridge Score) ---
        # 최근 10회차를 기준으로 분석
        recent_10 = appearances_bool[-10:]
        appearance_count = sum(recent_10) # 10회 중 몇 번 나왔나
        
        # 조밀도 점수: 10회 중 5회 나오면 만점(100점) 기준 설계
        bridge_score = (appearance_count / 5) * 100
        bridge_score = min(100, bridge_score) 

        # --- [C] 통합 점수 합산 (Total) ---
        total_score = (streak_score * 0.6) + (bridge_score * 0.4)

        results.append({
            "번호": num,
            "현재연속": curr_streak,
            "최근조밀도": f"{appearance_count}/10",
            "연속점수": round(streak_score, 1),
            "징검다리점수": round(bridge_score, 1),
            "통합크레이지점수": round(total_score, 1)
        })

    return pd.DataFrame(results)
