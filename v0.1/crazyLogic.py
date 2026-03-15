import pandas as pd

def get_crazy_analysis(df):
    if df.empty:
        return pd.DataFrame()

    df_sorted = df.sort_values(by='round', ascending=True)
    results = []

    for num in range(1, 45 + 1):
        appearances = []
        for _, row in df_sorted.iterrows():
            win_nums = [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]
            appearances.append(num in win_nums)

        # 1. 현재 연속출현 횟수 계산
        curr_streak = 0
        for appeared in reversed(appearances):
            if appeared:
                curr_streak += 1
            else:
                break
        
        # [조건 추가] 현재 연속출현횟수가 0인 경우 아예 리스트에 추가하지 않음 (순위 제외)
        if curr_streak == 0:
            continue

        # 2. 모든 연속 기록 추출 (과거 최대 계산용)
        streaks = []
        temp_streak = 0
        for appeared in appearances:
            if appeared:
                temp_streak += 1
            else:
                if temp_streak > 0:
                    streaks.append(temp_streak)
                temp_streak = 0
        if temp_streak > 0:
            streaks.append(temp_streak)

        # 3. 과거 최대 연속출현 (현재 기록 제외)
        if len(streaks) > 1:
            past_streaks = streaks[:-1]
        else:
            past_streaks = []
            
        max_past = max(past_streaks) if past_streaks else curr_streak
        
        # 4. 새로운 공식 적용: (과거최대 - 현재) / 과거최대 * 100
        # 현재가 과거최대를 넘어서면 확률은 0 이하가 될 수 있으므로 최소값 0 처리
        if max_past > 0:
            prob = ((max_past - curr_streak) / max_past) * 100
            if prob < 0: prob = 0.0 # 현재가 기록 경신 중인 경우
        else:
            prob = 0.0
        
        results.append({
            "번호": num,
            "현재연속": curr_streak,
            "과거최대": max_past,
            "확률": round(prob, 1)
        })

    return pd.DataFrame(results)
