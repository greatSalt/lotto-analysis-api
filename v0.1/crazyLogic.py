import pandas as pd

def get_crazy_analysis(df):
    if df.empty:
        return pd.DataFrame()

    # 데이터를 회차 오름차순으로 정렬 (과거 -> 현재)
    df_sorted = df.sort_values(by='round', ascending=True)
    results = []

    for num in range(1, 46):
        # 1. 특정 번호의 모든 출연 여부 리스트 생성 (True/False)
        appearances = []
        for _, row in df_sorted.iterrows():
            win_nums = [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]
            appearances.append(num in win_nums)

        # 2. 모든 연속 출연 기록(Streaks) 추출
        streaks = []
        temp_streak = 0
        for appeared in appearances:
            if appeared:
                temp_streak += 1
            else:
                if temp_streak > 0:
                    streaks.append(temp_streak)
                temp_streak = 0
        # 마지막 회차까지 진행 중인 경우도 추가
        if temp_streak > 0:
            streaks.append(temp_streak)

        # 3. 현재 연속 출연 횟수 (맨 마지막 회차부터 역순 계산)
        curr_streak = 0
        for appeared in reversed(appearances):
            if appeared:
                curr_streak += 1
            else:
                break
        
        # 4. 과거 최대 연속 출연 (현재 진행 중인 기록 제외)
        # 만약 현재 3회 연속 중이라면, 그 이전 기록들 중 최대값
        if curr_streak > 0:
            # 현재 연속 기록을 제외한 나머지 기록들
            past_streaks = streaks[:-1] if len(streaks) > 1 else []
        else:
            past_streaks = streaks
            
        max_past = max(past_streaks) if past_streaks else 0
        
        # 5. 출현 확률 계산 (%)
        prob = (curr_streak / max_past * 100) if max_past > 0 else 0
        
        results.append({
            "번호": num,
            "현재연속": curr_streak,
            "과거최대": max_past,
            "출현확률(%)": round(prob, 1)
        })

    return pd.DataFrame(results)