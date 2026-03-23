import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

def save_to_google_sheets(df):
    try:
        # 구글 시트 연결 생성
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 기존 데이터 읽기
        existing_data = conn.read(worksheet="Sheet1")
        
        # 새로운 데이터 아래에 붙이기 (현재 분석 결과)
        # 분석 일시와 회차 정보를 추가하면 더 좋겠지?
        updated_df = pd.concat([existing_data, df], ignore_index=True)
        
        # 시트에 업데이트
        conn.update(worksheet="Sheet1", data=updated_df)
        return True, "구글 시트 업데이트 완료!"
    except Exception as e:
        return False, str(e)

def render_gsheet_button(df):
    if st.button("☁️ 구글 스프레드시트로 즉시 전송", use_container_width=True):
        if df.empty:
            st.warning("전송할 데이터가 없습니다.")
            return
            
        success, msg = save_to_google_sheets(df)
        if success:
            st.success(msg)
            st.balloons()
        else:
            st.error(f"전송 실패: {msg}")
