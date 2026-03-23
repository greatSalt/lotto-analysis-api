import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

def save_to_google_sheets(df, sheet_url):
    """
    main.py에서 넘겨받은 sheet_url을 사용하여 RowData 시트에 저장합니다.
    """
    try:
        # 1. 연결 생성
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 2. 데이터 읽기 (SavedPick.py 성공 방식 적용)
        try:
            # 넘겨받은 sheet_url을 직접 사용함 (에러 원천 차단)
            existing_data = conn.read(spreadsheet=sheet_url, worksheet="RowData", ttl=0)
        except Exception:
            existing_data = pd.DataFrame()
        
        # 3. 새 데이터 준비 (타임스탬프 추가)
        df_to_save = df.copy()
        df_to_save['저장일시'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 4. 데이터 합치기
        if not existing_data.empty:
            updated_df = pd.concat([existing_data, df_to_save], ignore_index=True)
        else:
            updated_df = df_to_save
        
        # 5. 시트 업데이트 (여기서도 URL 직접 사용)
        conn.update(spreadsheet=sheet_url, worksheet="RowData", data=updated_df)
        return True, "✅ 구글 시트(RowData) 저장 성공!"
        
    except Exception as e:
        return False, f"❌ 저장 실패: {str(e)}"

def render_gsheet_button(df, sheet_url):
    """
    버튼 클릭 시 main.py의 SHEET_URL을 함수로 전달합니다.
    """
    if st.button("☁️ 분석 결과 구글 시트로 즉시 전송", use_container_width=True):
        if df is None or df.empty:
            st.warning("⚠️ 전송할 데이터가 없습니다.")
            return
            
        with st.spinner("구글 시트(RowData)로 전송 중..."):
            # main.py에서 정의된 그 URL을 그대로 사용
            success, msg = save_to_google_sheets(df, sheet_url)
            
        if success:
            st.success(msg)
            st.balloons()
        else:
            st.error(msg)
