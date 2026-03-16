import pandas as pd

def analyze_specific_number(df, target_num):
    """
    특정 번호의 출현 빈도, 연속성, 미출현 기간을 분석합니다.
    """
    if df.empty:
        return None

    # 회차순 정렬 (과거 -> 현재)
    df_sorted = df.sort_values(by='round', ascending=True)
    
    # 1. 당첨 회차 리스트 추출
    appearance_rounds = []
    for row in df_sorted.itertuples():
        win_nums = [row.n1, row.n2, row.n3, row.n4, row.n5, row.n6]
        if target_num in win_nums:
            appearance_rounds.append(int(row.round))
    
    total_count = len(appearance_rounds)
    last_appearance = appearance_rounds[-1] if appearance_rounds else 0
    
    # 2. 연속성 분석을 위한 불리언 리스트
    appearances_bool = []
    for row in df_sorted.itertuples():
        win_nums = [row.n1, row.n2, row.n3, row.n4, row.n5, row.n6]
        appearances_bool.append(target_num in win_nums)
    
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
    
    # 3. 미출현 기간
    latest_round = int(df_sorted['round'].max())
    missing_period = latest_round - last_appearance if last_appearance > 0 else latest_round

    return {
        "총출현횟수": total_count,
        "최근출현회차": last_appearance,
        "현재연속출현": curr_streak,
        "최대연속출현": max_streak,
        "현재미출현기간": missing_period,
        "출현기록": appearance_rounds[::-1]
    }
