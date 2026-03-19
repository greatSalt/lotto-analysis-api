import streamlit as st

def init_saved_picks():
    """세션 상태 초기화 (main.py 상단에서 호출)"""
    if 'my_saved_picks' not in st.session_state:
        st.session_state.my_saved_picks = []

def display_top_picks():
    """상단에 저장된 번호를 예쁘게 표시"""
    if st.session_state.my_saved_picks:
        picks_str = "  |  ".join([f"**{n}**" for n in sorted(st.session_state.my_saved_picks)])
        st.success(f"📍 **추적 중인 주요 번호:** {picks_str}")
        if st.button("🔄 저장 목록 초기화"):
            st.session_state.my_saved_picks = []
            st.rerun()
    else:
        st.warning("🧐 아래 표에서 주요 번호를 체크하고 저장해 주세요.")

def get_highlight_style(row):
    """표의 행(Row) 스타일 결정 (굵은 글씨 및 색상)"""
    base_style = ''
    skip_diff = abs(row['직전스킵'] - row['평균스킵'])
    
    # 1. 상태별 배경색 설정
    if skip_diff <= 1:
        base_style = 'background-color: #F1C40F; color: black;' # 노랑(임계점)
    elif row['직전스킵'] > row['평균스킵']:
        base_style = 'background-color: #E74C3C; color: white;' # 빨강(응축)
    elif row['현재연속'] == 0:
        base_style = 'background-color: #3498DB; color: white;' # 파랑(미출현)

    # 2. [핵심] 저장된 번호면 무조건 굵게 + 테두리
    if row['번호'] in st.session_state.my_saved_picks:
        base_style += ' font-weight: 900; font-size: 1.1em; border: 2.5px solid #2C3E50;'
    
    return [base_style] * len(row)
