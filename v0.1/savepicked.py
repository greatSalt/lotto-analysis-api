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
    """표의 스타일 결정 (노란색 임계점 우선 적용)"""
    base_style = ''
    
    try:
        # 1. 우선순위 1: 노란색 (임계점 도달) - 가장 중요함
        if '직전스킵' in row and '평균스킵' in row:
            skip_diff = abs(row['직전스킵'] - row['평균스킵'])
            if skip_diff <= 1:
                base_style = 'background-color: #FFD700; color: #000000;' # 노랑
            
            # 2. 우선순위 2: 빨간색 (에너지 응축) - 노란색이 아닐 때만 적용
            elif row['직전스킵'] > row['평균스킵']:
                base_style = 'background-color: #FF4B4B; color: #FFFFFF;' # 빨강

        # 3. 우선순위 3: 파란색 (방금 출현) - 노랑/빨강이 모두 아닐 때만 적용
        # 이렇게 else/elif 구조를 타야 노란색이 파란색에 먹히지 않습니다.
        if base_style == '' and '현재연속' in row and row['현재연속'] == 0:
            base_style = 'background-color: #1E90FF; color: #FFFFFF;' # 파랑
            
    except Exception:
        pass

    # 4. [핵심] 내 번호 강조 (어떤 배경색 위에서도 굵게 표시)
    if 'my_saved_picks' in st.session_state:
        if row['번호'] in st.session_state.my_saved_picks:
            # !important를 추가하여 테두리가 다른 스타일에 밀리지 않게 강조
            base_style += ' font-weight: 900; font-size: 1.15em; border: 2.5px solid #000000 !important;'
    
    return [base_style] * len(row)
