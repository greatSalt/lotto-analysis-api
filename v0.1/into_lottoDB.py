import pandas as pd
import streamlit as st
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
        
def analyze_combination(nums, prev_nums, cold_nums):
    """입력된 번호 조합의 상세 지표 분석"""
    nums = sorted(nums)
    
    # 1. 개별 번호 분석 (이월수, 콜드수 여부)
    analysis_list = []
    for n in nums:
        is_carryover = "✅" if n in prev_nums else "X"
        is_cold = "❄️" if n in cold_nums else "X"
        analysis_list.append({
            "번호": n,
            "이월수여부": is_carryover,
            "콜드수여부": is_cold
        })
    
    # 2. 조합 전체 지표 계산
    total_sum = sum(nums)
    odd_count = len([n for n in nums if n % 2 != 0])
    even_count = 6 - odd_count
    high_count = len([n for n in nums if n >= 23])
    low_count = 6 - high_count
    
    # AC 계산
    diffs = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    ac_value = len(diffs) - (6 - 1)
    
    # 연번 계산
    consecutive = 0
    for i in range(len(nums)-1):
        if nums[i+1] - nums[i] == 1:
            consecutive += 1
            
    metrics = {
        "홀짝": f"{odd_count}:{even_count}",
        "총합": total_sum,
        "AC": ac_value,
        "고저": f"{low_count}:{high_count}",
        "연번": consecutive
    }
    
    return pd.DataFrame(analysis_list), metrics
