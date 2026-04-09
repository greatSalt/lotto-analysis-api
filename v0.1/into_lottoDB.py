import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from crazyLogic import get_crazy_analysis
from coldNum import get_cold_analysis

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
    
@st.cache_data # 이 함수는 500개의 데이터를 한 번 가져오면 메모리에 저장해둡니다. 슬라이더를 움직여도 구글 시트에 다시 접속하지 않고 메모리에서 꺼내옵니다.
def get_recent_data(_conn, sheet_url, count=0): # conn -> _conn 으로 변경
    """
    인자 앞에 '_'를 붙이면 Streamlit은 이 인자의 변화를 
    캐시 체크용 해시 계산에서 제외합니다.
    """
    # 함수 내부 로직...
    # (내부에서도 conn 대신 _conn을 사용하세요)
    # 예: sheet = _conn.open_by_url(url)
    try:
        # 1. 데이터 읽기
        df = _conn.read(spreadsheet=sheet_url, ttl=0)
        
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
        
def analyze_combination(input_nums, df, analyze_range):
    """
    Crazy 엔진의 기술 지표와 Cold 엔진의 미출현 지표를 통합 분석
    """
    input_nums = sorted(input_nums)
    df_target = df.head(analyze_range).copy()
    
    # 1. 각 엔진 실행
    df_crazy = get_crazy_analysis(df_target) # 기술 지표용
    df_cold = get_cold_analysis(df_target)   # 콜드 지수용
    
    # 2. 데이터 병합 (번호 기준)
    df_total = pd.merge(df_crazy, df_cold, on="번호")
    
    # 3. 입력된 6개 번호만 추출
    analysis_df = df_total[df_total['번호'].isin(input_nums)].copy()
    
    # 4. 이월수 여부 체크
    prev_nums = [df.iloc[0][f'n{i}'] for i in range(1, 7)]
    analysis_df['이월수'] = analysis_df['번호'].apply(lambda x: "✅" if x in prev_nums else "X")
    
    # 5. 요청된 컬럼 구성 (불필요 지표 제거 및 콜드지수 추가)
    display_cols = [
        '번호', '이월수', '반등지수', '에너지지수', '콜드지수',
        '평균스킵', '직전스킵', '현재스킵', '최대스킵', 
        '현재연속', '최대연속', '연속점수'
    ]
    analysis_df = analysis_df[display_cols]

    # 6. 조합 전체 필터 지표 (홀짝, 총합, AC, 고저, 연번)
    total_sum = sum(input_nums)
    odd_cnt = len([n for n in input_nums if n % 2 != 0])
    high_cnt = len([n for n in input_nums if n >= 23])
    
    diffs = set()
    for i in range(len(input_nums)):
        for j in range(i + 1, len(input_nums)):
            diffs.add(abs(input_nums[i] - input_nums[j]))
    ac_value = len(diffs) - 5
    
    consecutive = 0
    for i in range(5):
        if input_nums[i+1] - input_nums[i] == 1:
            consecutive += 1
            
    metrics = {
        "홀짝": f"{odd_cnt}:{6-odd_cnt}",
        "총합": total_sum,
        "AC": ac_value,
        "고저": f"{6-high_cnt}:{high_cnt}", # 저:고
        "연번": consecutive
    }
    
    return analysis_df, metrics
