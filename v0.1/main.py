import streamlit as st
import pandas as pd
import coldNum
from specialNum import analyze_specific_number
from streamlit_gsheets import GSheetsConnection
from into_lottoDB import save_to_gsheet, get_recent_data
from crazyLogic import get_crazy_analysis

st.set_page_config(page_title="로또 분석 프로 v0.1", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1q8P3SClxNSYsAXwBgk3__y44XxZwI_FTj-eE9uQeVHE/edit?gid=0#gid=0"

st.sidebar.title("🎮 메뉴 선택")
menu = st.sidebar.radio("기능 선택", ["데이터 입력", "크레이지 번호 추출", "콜드 번호 추출", "특정 번호 분석"])

if menu == "데이터 입력":
    st.title("🎰 로또 데이터 입력")
    with st.form("lotto_input_form", clear_on_submit=True):
        col_drw = st.number_input("회차", min_value=1, step=1)
        c = st.columns(6)
        n1, n2, n3, n4, n5, n6 = [c[i].number_input(f"No{i+1}", 1, 45) for i in range(6)]
        bonus = st.number_input("Bonus", 1, 45)
        if st.form_submit_button("DB 저장하기"):
            data_to_save = {"round": int(col_drw), "n1": n1, "n2": n2, "n3": n3, "n4": n4, "n5": n5, "n6": n6, "bonus": bonus}
            save_to_gsheet(conn, SHEET_URL, data_to_save)
            st.success("데이터 저장 완료")

elif menu == "크레이지 번호 추출":
    st.title("🔥 크레이지 번호 분석 리포트")
    analyze_count = st.number_input("분석 범위(최근 회차)", 0, 100, 30)
    df = get_recent_data(conn, SHEET_URL, count=analyze_count)
    
    if not df.empty:
        analysis_df = get_crazy_analysis(df)
        if not analysis_df.empty:
            display_df = analysis_df.sort_values(by="통합크레이지점수", ascending=False)
            display_df.insert(0, '순위', range(1, len(display_df) + 1))
            
            # 숫자 중심의 깔끔한 데이터 테이블 (그림/막대 제거)
            st.dataframe(display_df, use_container_width=True, hide_index=True,
                column_config={
                    "순위": st.column_config.NumberColumn("순위"),
                    "번호": st.column_config.NumberColumn("번호"),
                    "현재연속": st.column_config.NumberColumn("현재(Curr)"),
                    "최대연속": st.column_config.NumberColumn("최대(Max)"),
                    "연속점수": st.column_config.NumberColumn("기세점수", format="%.1f"),
                    "징검다리점수": st.column_config.NumberColumn("탄성점수", format="%.1f"),
                    "통합크레이지점수": st.column_config.NumberColumn("최종점수", format="%.1f")
                })

            st.divider()
            st.subheader("📝 점수 산출 공식 및 수치 해석")
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.info("#### 🏃‍♂️ 기세 지수 (Streak Score)")
                st.latex(r"S_{streak} = \frac{(Max - Curr)}{Max} \times 100")
                st.markdown("""
                * **Max:** 해당 번호의 역대 최대 연속 출현 횟수
                * **Curr:** 현재 진행 중인 연속 출현 횟수
                * **해석:** 과거 기록 대비 현재 얼마나 더 나올 여력이 있는지 측정합니다.
                """)
            
            with col_right:
                st.info("#### 🌉 징검다리 탄성 (Bridge Elasticity)")
                st.markdown("1. **평균 간격($Gap_{avg}$):** 최근 10회 중 출현 사이 평균 간격")
                st.info("2. **기본 탄성 점수:**")
                st.latex(r"100 - (|1.0 - Gap_{avg}| \times 40)") 
                st.info("3. **최근성 보너스:**")
                st.latex(r"(마지막\ 출현\ 위치 + 1) \times 10")

elif menu == "특정 번호 분석":
    st.title("🔍 번호 심층 분석")
    target_num = st.number_input("번호", 1, 45, 1)
    df = get_recent_data(conn, SHEET_URL, count=50)
    res = analyze_specific_number(df, target_num)
    if res:
        st.write(res)

elif menu == "콜드 번호 추출":
    st.title("🧊 콜드 번호 리포트")
    df = get_recent_data(conn, SHEET_URL, count=0)
    cold_df = coldNum.get_cold_analysis(df)
    st.dataframe(cold_df.sort_values("현재미출현", ascending=False).head(15), use_container_width=True)

st.sidebar.divider()
st.sidebar.caption("v0.1 - 통계 분석 시스템")
