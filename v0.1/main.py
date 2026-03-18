import streamlit as st
import pandas as pd
import random
import datetime
import coldNum

from specialNum import analyze_specific_number
from streamlit_gsheets import GSheetsConnection
from into_lottoDB import save_to_gsheet, get_recent_data
from crazyLogic import get_crazy_analysis

st.set_page_config(page_title="로또 분석 프로 v0.1", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1q8P3SClxNSYsAXwBgk3__y44XxZwI_FTj-eE9uQeVHE/edit?gid=0#gid=0"

st.sidebar.title("🎮 메뉴 선택")
menu = st.sidebar.radio("원하는 기능을 선택하세요", ["데이터 입력", "크레이지 번호 추출", "콜드 번호 추출", "특정 번호 분석"])

if menu == "데이터 입력":
    st.title("🎰 로또 당첨 패턴 분석기")
    st.subheader("📥 데이터 입력")
    with st.form("lotto_input_form", clear_on_submit=True):
        col_drw = st.number_input("회차 입력", min_value=1, step=1)
        c = st.columns(6)
        n1 = c[0].number_input("No1", 1, 45)
        n2 = c[1].number_input("No2", 1, 45)
        n3 = c[2].number_input("No3", 1, 45)
        n4 = c[3].number_input("No4", 1, 45)
        n5 = c[4].number_input("No5", 1, 45)
        n6 = c[5].number_input("No6", 1, 45)
        st.write("보너스 번호")
        bonus = st.number_input("Bonus", 1, 45)
        if st.form_submit_button("DB 저장하기"):
            data_to_save = {"round": int(col_drw), "n1": n1, "n2": n2, "n3": n3, "n4": n4, "n5": n5, "n6": n6, "bonus": bonus}
            updated_df = save_to_gsheet(conn, SHEET_URL, data_to_save)
            st.success(f"{col_drw}회차 데이터가 저장되었습니다!")
            st.balloons()

elif menu == "크레이지 번호 추출":
    st.title("🔥 크레이지 번호 분석 리포트")
    col_config = st.columns([2, 3])
    with col_config[0]:
        analyze_count = st.number_input("분석할 최근 회차 범위 (0=전체)", min_value=0, value=30, step=5, key="crazy_range")
    df = get_recent_data(conn, SHEET_URL, count=analyze_count)
    if not df.empty:
        analysis_df = get_crazy_analysis(df)
        if not analysis_df.empty:
            display_df = analysis_df.sort_values(by="통합크레이지점수", ascending=False)
            display_df.insert(0, '순위', range(1, len(display_df) + 1))
            st.dataframe(display_df, use_container_width=True, hide_index=True,
                column_config={
                    "연속점수": st.column_config.ProgressColumn("연속 에너지", min_value=0, max_value=100, format="%.1f"),
                    "징검다리점수": st.column_config.ProgressColumn("징검다리 탄성", min_value=0, max_value=100, format="%.1f"),
                    "통합크레이지점수": st.column_config.NumberColumn("최종 점수", format="%.1f 🔥")
                })
            st.divider()
            with st.expander("📘 분석 공식 및 수치 산출 기준"):
                st.markdown("### **통합 점수 = (연속 지수 × 0.6) + (징검다리 탄성 × 0.4)**")
                c1, c2 = st.columns(2)
                with c1:
                    st.info("#### 🏃‍♂️ 연속 지수 (Streak: 60%)")
                    st.latex(r"S = \frac{(Max - Curr + 1)}{Max} \times 100")
                    st.write("**Max:** 역대 최대 연속 / **Curr:** 현재 연속")
                    st.write("- 과거 기록 경신 여력을 측정합니다.")
                    st.write("- 100점에 가까울수록 기록 경신 기세가 높음을 의미합니다.")
                with c2:
                    st.info("#### 🌉 징검다리 탄성 (Elasticity: 40%)")
                    st.write("**최근 10회차 간격 분석:**")
                    st.write("- **간격 점수:** 평균 미출현 간격이 1회(퐁당퐁당)일 때 100점 기준.")
                    st.write("- **최근성:** 마지막 출현이 1~2회차 이내일 때 가산점 부여.")
                    st.write("- 단순 빈도가 아닌 '다시 튀어오를 리듬'을 수치화합니다.")

elif menu == "특정 번호 분석":
    st.title("🔍 특정 번호 심층 분석")
    col_ui = st.columns([1, 1, 2])
    with col_ui[0]: target_num = st.number_input("분석할 번호 (1~45)", 1, 45, value=1)
    with col_ui[1]: analyze_count = st.number_input("분석 범위", min_value=0, value=50, step=10)
    df = get_recent_data(conn, SHEET_URL, count=analyze_count)
    if not df.empty:
        res = analyze_specific_number(df, target_num)
        if res:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("출현 횟수", f"{res['총출현횟수']}회")
            m2.metric("현재 연속", f"{res['현재연속출현']}회")
            m3.metric("최대 연속", f"{res['최대연속출현']}회")
            m4.metric("미출현 기간", f"{res['현재미출현기간']}회차")

elif menu == "콜드 번호 추출":
    st.title("🧊 콜드 번호 분석 리포트")
    df = get_recent_data(conn, SHEET_URL, count=0)
    if not df.empty:
        cold_df = coldNum.get_cold_analysis(df)
        display_cold = cold_df.sort_values(by="현재미출현", ascending=False).head(15)
        st.dataframe(display_cold, use_container_width=True, hide_index=True)

st.sidebar.divider()
st.sidebar.caption("본 프로그램은 통계 분석 도구이며 당첨을 보장하지 않습니다.")
