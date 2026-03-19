import streamlit as st
import pandas as pd

def init_saved_picks(conn, sheet_url):
    """앱 시작 시 구글 시트에서 저장된 번호를 불러오기"""
    if 'my_saved_picks' not in st.session_state:
        try:
            df = conn.read(spreadsheet=sheet_url, worksheet="SavedPicks", ttl=0)
            if not df.empty:
                st.session_state.my_saved_picks = df['번호'].tolist()
            else:
                st.session_state.my_saved_picks = []
        except Exception:
            st.session_state.my_saved_picks = []

def save_picks_to_sheets(conn, sheet_url, new_picks):
    """구글 시트에 번호 영구 저장"""
    df = pd.DataFrame({"번호": new_picks})
    try:
        conn.update(spreadsheet=sheet_url, worksheet="SavedPicks", data=df)
        st.session_state.my_saved_picks = new_picks
        st.toast("✅ 구글 시트에 안전하게 저장되었습니다!")
    except Exception as e:
        st.error(f"저장 실패: {e}")

def display_sidebar_picks(conn, sheet_url):
    """사이드바 표시 및 관리"""
    with st.sidebar:
        st.divider()
        st.markdown("### 🎯 My Lucky Picks")
        
        if st.session_state.my_saved_picks:
            picks = sorted(st.session_state.my_saved_picks)
            cols = st.columns(3)
            for i, num in enumerate(picks):
                cols[i % 3].info(f"**{num}**")
            
            # 리셋 시에도 시트와 동기화되도록 sheet_url 전달
            if st.button("🔄 Reset & Sync", use_container_width=True):
                save_picks_to_sheets(conn, sheet_url, []) 
                st.rerun()
        else:
            st.caption("저장된 번호가 없습니다.")
        st.divider()

def get_highlight_style(row):
    """표의 스타일 결정 (색상 및 굵은 글씨)"""
    base_style = ''
    
    # 1. 스킵 주기 분석 (노란색: 임계점 / 빨간색: 응축 / 파란색: 미출현)
    try:
        # 데이터에 컬럼이 있는지 확인 후 계산
        if '직전스킵' in row and '평균스킵' in row:
            skip_diff = abs(row['직전스킵'] - row['평균스킵'])
            if skip_diff <= 1:
                base_style = 'background-color: #F1C40F; color: black;' # 진한 노랑
            elif row['직전스킵'] > row['평균스킵']:
                base_style = 'background-color: #E74C3C; color: white;' # 진한 빨강
        
        if '현재연속' in row and row['현재연속'] == 0:
            base_style = 'background-color: #3498DB; color: white;' # 진한 파랑
    except:
        pass

    # 2. [핵심] 내가 저장한 번호는 아주 굵게 표시 (사이드바 번호와 동기화)
    if 'my_saved_picks' in st.session_state:
        if row['번호'] in st.session_state.my_saved_picks:
            base_style += ' font-weight: 900; font-size: 1.1em; border: 2px solid #2C3E50;'
    
    return [base_style] * len(row)
