import streamlit as st

def init_saved_picks():
    """세션 상태 초기화"""
    if 'my_saved_picks' not in st.session_state:
        st.session_state.my_saved_picks = []

def display_sidebar_picks():
    """사이드바에 저장된 번호를 항상 표시"""
    with st.sidebar:
        st.divider()
        st.markdown("### 🎯 My Lucky Picks")
        
        if st.session_state.my_saved_picks:
            # 번호를 보기 좋게 나열 (배지 스타일 느낌으로)
            picks = sorted(st.session_state.my_saved_picks)
            cols = st.columns(3) # 3열로 배치해서 깔끔하게 표시
            for i, num in enumerate(picks):
                cols[i % 3].info(f"**{num}**")
            
            if st.button("🔄 Reset Picks", use_container_width=True):
                st.session_state.my_saved_picks = []
                st.rerun()
        else:
            st.caption("No numbers selected yet.")
        st.divider()

def get_highlight_style(row):
    """표의 스타일 결정 (동일 유지)"""
    base_style = ''
    skip_diff = abs(row['직전스킵'] - row['평균스킵'])
    
    if skip_diff <= 1:
        base_style = 'background-color: #F1C40F; color: black;'
    elif row['직전스킵'] > row['평균스킵']:
        base_style = 'background-color: #E74C3C; color: white;'
    elif row['현재연속'] == 0:
        base_style = 'background-color: #3498DB; color: white;'

    if row['번호'] in st.session_state.my_saved_picks:
        base_style += ' font-weight: 900; font-size: 1.1em; border: 2.5px solid #2C3E50;'
    
    return [base_style] * len(row)
