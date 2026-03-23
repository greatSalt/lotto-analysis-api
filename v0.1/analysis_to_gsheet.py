import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

def save_to_google_sheets(df):
    """
    SavedPick.py에서 성공했던 방식 그대로 URL을 명시하여 RowData 시트에 저장합니다.
    """
    try:
        # 1. 연결 생성
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 2. secrets에서 URL 가져오기 (가장 확실한 방법)
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # 3. 기존 데이터 읽기 (시트 이름: RowData)
        try:
            # SavedPick.py와 동일하게 spreadsheet 주소를 직접 전달
            existing_data = conn.read(spreadsheet=sheet_url, worksheet="RowData", ttl=0)
        except Exception:
            # 시트가 비어있거나 처음 만들 때를 대비
            existing_data = pd.DataFrame()
        
        # 4. 새 데이터 준비 (타임스탬프 추가)
        df_to_save = df.copy()
        df_to_save['저장일시'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 5. 데이터 합치기 (기존 데이터 아래에 추가)
        if not existing_data.empty:
            updated_df = pd.concat([existing_data, df_to_save], ignore_index=True)
        else:
            updated_df = df_to_save
        
        # 6. 구글 시트에 업데이트 (URL 명시)
        conn.update(spreadsheet=sheet_url, worksheet="RowData", data=updated_df)
        return True, "✅ 구글 시트(RowData) 업데이트 완료!"
        
    except Exception as e:
        return False, f"❌ 저장 실패: {str(e)}"

def render_gsheet_button(df):
    """
    분석 결과 전송 버튼 렌더링
    """
    if st.button("☁️ 분석 결과 구글 시트로 즉시 전송", use_container_width=True):
        if df is None or df.empty:
            st.warning("⚠️ 전송할 데이터가 없습니다.")
            return
            
        with st.spinner("구글 시트(RowData)로 전송 중..."):
            success, msg = save_to_google_sheets(df)
            
        if success:
            st.success(msg)
            st.balloons()
        else:
            st.error(msg)
