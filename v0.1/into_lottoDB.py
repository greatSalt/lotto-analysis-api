import pandas as pd
from streamlit_gsheets import GSheetsConnection

def save_to_gsheet(conn, sheet_url, new_data):
    """
    new_data: {'drwNo': 1110, 'num1': 3, ...} 형태의 딕셔너리
    """
    try:
        # 1. 기존 데이터 불러오기
        df = conn.read(spreadsheet=sheet_url)
    except:
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
