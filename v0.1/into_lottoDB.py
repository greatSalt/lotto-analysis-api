import pandas as pd
from streamlit_gsheets import GSheetsConnection

def save_to_gsheet(conn, sheet_url, new_data):
    """
    new_data: {'drwNo': 1110, 'num1': 3, ...} 형태의 딕셔너리
    """
    try:
        # 1. 기존 데이터 불러오기
        df = conn.read(spreadsheet=sheet_url, ttl=0)
    except Exception as e:
        st.warning(f"기존 데이터를 읽지 못했습니다: {e}")
        # 시트가 비어있을 경우 대비
        df = pd.DataFrame()

    # 2. 새로운 데이터를 데이터프레임으로 변환
    new_df = pd.DataFrame([new_data])

    # 3. 기존 데이터와 합치기 (중복 회차 제거 포함)
    if not df.empty:
        df = pd.concat([df, new_df], ignore_index=True)
        # 회차(drwNo)가 중복되면 마지막에 입력한 것으로 유지
        df = df.drop_duplicates(['round'], keep='last')
    else:
        df = new_df

    # 4. 회차(drwNo) 기준 내림차순 정렬 (최신순)
    df = df.sort_values(by='round', ascending=False)

    # 5. 구글 시트 업데이트
    conn.update(spreadsheet=sheet_url, data=df)
    
    return df
 
def get_recent_data(conn, sheet_url, count=0):
    try:
        # 1. 데이터 읽기 (캐시 무시)
        df = conn.read(spreadsheet=sheet_url, ttl=0)
        
        if df.empty:
            return pd.DataFrame()

        # 2. 회차순으로 정렬 (최신이 위로 오게)
        if 'round' in df.columns:
            df = df.sort_values(by='round', ascending=False)
        
        # 3. 인자(count)에 따라 데이터 자르기
        if count > 0:
            df = df.head(count) # 최근 count개만 가져옴
            
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()
        
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