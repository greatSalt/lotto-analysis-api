import pandas as pd

def analyze_specific_number(df, target_num):
    if df.empty or not (1 <= target_num <= 45):
        return None

    # 회차순 정렬 (과거 -> 현재)
    df_sorted = df.sort_values(by='round', ascending=True)
    
    # 1. 특정 번호가 포함된 당첨 회차 리스트 (범위 내)
    appearance_rounds = []
    for row in df_sorted.itertuples():
        win_nums = [row.n1, row.n2, row.n3, row.n4, row.n5, row.n6]
        if target_num in win_nums:
            appearance_rounds.append(int(row.round))
    
    total_count = len(appearance_rounds)
    last_appearance = appearance_rounds[-1] if appearance_rounds else 0
    
    # 2. 연속성 분석을 위한 불리언 리스트
    appearances_bool = [target_num in [r.n1, r.n2, r.n3, r.n4, r.n5, r.n6] for r in df_sorted.itertuples()]
    
    # 현재 연속 출연
    curr_streak = 0
    for app in reversed(appearances_bool):
        if app: curr_streak += 1
        else: break
        
    # 최대 연속 출연
    streaks = []
    temp = 0
    for app in appearances_bool:
        if app: temp += 1
        else:
            if temp > 0: streaks.append(temp)
            temp = 0
    if temp > 0: streaks.append(temp)
    max_streak = max(streaks) if streaks else 0
    
    # 3. 미출현 기간 (범위 내 최신 회차 기준)
    latest_round = int(df_sorted['round'].max())
    missing_period = latest_round - last_appearance if last_appearance > 0 else len(df_sorted)

    return {
        "총출현횟수": total_count,
        "최근출현회차": last_appearance,
        "현재연속출현": curr_streak,
        "최대연속출현": max_streak,
        "현재미출현기간": missing_period,
        "출현기록": appearance_rounds[::-1],
        "분석범위": len(df_sorted)
    }
