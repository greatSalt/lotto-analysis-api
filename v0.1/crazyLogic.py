import pandas as pd

def get_crazy_analysis(df):
    if df.empty:
        return pd.DataFrame()

    df_sorted = df.sort_values(by='round', ascending=True)
    results = []

    for num in range(1, 46):
        appearances_bool = []
        for row in df_sorted.itertuples():
            # 보너스 번호를 제외한 당첨 번호 내 존재 여부 확인
            win_nums = [row.n1, row.n2, row.n3, row.n4, row.n5, row.n6]
            appearances_bool.append(num in win_nums)
        
        # --- [A] 현재 연속 출현(Curr) 계산 ---
        curr_streak = 0
        for app in reversed(appearances_bool):
            if app: curr_streak += 1
            else: break
        
        # 현재 안 나오고 있는 번호는 분석 대상에서 제외
        if curr_streak == 0: continue 

        # --- [B] 역대 최대 연속 출현(Max) 계산 ---
        streaks = []
        temp = 0
        for app in appearances_bool:
            if app: temp += 1
            else:
                if temp > 0: streaks.append(temp)
                temp = 0
        if temp > 0: streaks.append(temp)
        max_streak = max(streaks) if streaks else 1
        
        # [수정] 원래 공식 복구: (Max - Curr) / Max * 100
        # 분석 의미: 과거 기록 대비 현재 얼마나 더 갈 수 있는가(남은 여력)
        streak_score = ((max_streak - curr_streak) / max_streak) * 100
        streak_score = max(0, min(100, streak_score))

        # --- [C] 징검다리 탄성 지수 (Bridge Score) ---
        recent_10 = appearances_bool[-10:]
        indices = [i for i, val in enumerate(recent_10) if val]
        
        if len(indices) >= 2:
            gaps = [indices[i] - indices[i-1] - 1 for i in range(1, len(indices))]
            avg_gap = sum(gaps) / len(gaps)
            
            # 탄성 공식: 평균 간격 1회(퐁당퐁당)일 때 최적화
            elasticity = max(0, 100 - (abs(1.0 - avg_gap) * 40))
            
            # 최근성 가중치: 마지막 출현 위치 보너스
            recency_bonus = (indices[-1] + 1) * 10 
            bridge_score = (elasticity * 0.7) + (recency_bonus * 0.3)
        else:
            bridge_score = sum(recent_10) * 20 

        bridge_score = min(100, max(0, bridge_score))

        # --- [D] 통합 점수 (6:4 비중) ---
        total_score = (streak_score * 0.6) + (bridge_score * 0.4)

        results.append({
            "번호": num,
            "현재연속": curr_streak,
            "최대연속": max_streak, # 표에 표시될 필수 변수
            "연속점수": round(streak_score, 1),
            "징검다리점수": round(bridge_score, 1),
            "통합크레이지점수": round(total_score, 1)
        })

    return pd.DataFrame(results)
