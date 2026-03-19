import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

def init_saved_picks(conn, sheet_url):
    """앱 시작 시 구글 시트에서 저장된 번호를 불러오기"""
    if 'my_saved_picks' not in st.session_state:
        try:
            # 'SavedPicks' 시트에서 데이터 읽기
            df = conn.read(spreadsheet=sheet_url, worksheet="SavedPicks", ttl=0)
            if not df.empty:
                st.session_state.my_saved_picks = df['번호'].tolist()
            else:
                st.session_state.my_saved_picks = []
        except Exception:
            # 시트가 없거나 오류 시 빈 리스트로 초기화
            st.session_state.my_saved_picks = []

def save_picks_to_sheets(conn, sheet_url, new_picks):
    """구글 시트에 번호 영구 저장"""
    df = pd.DataFrame({"번호": new_picks})
    try:
        # 'SavedPicks' 시트에 덮어쓰기
        conn.update(spreadsheet=sheet_url, worksheet="SavedPicks", data=df)
        st.session_state.my_saved_picks = new_picks
        st.toast("✅ 구글 시트에 안전하게 저장되었습니다!")
    except Exception as e:
        st.error(f"저장 실패: {e}")

def display_sidebar_picks(conn):
    """사이드바 표시 및 관리"""
    with st.sidebar:
        st.divider()
        st.markdown("### 🎯 My Lucky Picks (Synced)")
        
        if st.session_state.my_saved_picks:
            picks = sorted(st.session_state.my_saved_picks)
            cols = st.columns(3)
            for i, num in enumerate(picks):
                cols[i % 3].info(f"**{num}**")
            
            if st.button("🔄 Reset & Sync", use_container_width=True):
                save_picks_to_sheets(conn, []) # 시트 비우기
                st.rerun()
        else:
            st.caption("저장된 번호가 없습니다.")
        st.divider()
