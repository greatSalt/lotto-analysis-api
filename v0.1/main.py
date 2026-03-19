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
    analyze_count = st.number_input("분석 범위(최근 회차)", 10, 100, 50)
    df = get_recent_data(conn, SHEET_URL, count=analyze_count)
    
    if not df.empty:
        analysis_df = get_crazy_analysis(df)
        if not analysis_df.empty:
            display_df = analysis_df.sort_values(by="통합크레이지점수", ascending=False)
            display_df.insert(0, '순위', range(1, len(display_df) + 1))
            
            # --- [핵심 수정] 진한 색상 및 '노란색 임계점' 로직 ---
            def highlight_independence(row):
                styles = [''] * len(row)
                
                # 스킵 차이 계산 (절대값)
                skip_diff = abs(row['직전스킵'] - row['평균스킵'])
                
                # 1. [신규] 반등 임계점 (스킵 차이가 1 이내) -> 진한 노란색 (가장 강력한 후보)
                if skip_diff <= 1:
                    styles = ['background-color: #F1C40F; color: black; font-weight: bold;'] * len(row)
                
                # 2. 독립적 반등 (직전스킵 > 평균스킵) -> 진한 빨강 (에너지 응축)
                elif row['직전스킵'] > row['평균스킵']:
                    styles = ['background-color: #E74C3C; color: white; font-weight: bold;'] * len(row)
                
                # 3. 현재 미출현 중(Curr=0) -> 진한 파랑 (잠재적 콜드)
                elif row['현재연속'] == 0:
                    styles = ['background-color: #3498DB; color: white; font-weight: bold;'] * len(row)
                    
                return styles

            styled_df = display_df.style.apply(highlight_independence, axis=1)

            st.dataframe(styled_df, use_container_width=True, hide_index=True,
                column_config={
                    "순위": st.column_config.NumberColumn("순위"),
                    "번호": st.column_config.NumberColumn("번호"),
                    "현재연속": st.column_config.NumberColumn("현재(Curr)"),
                    "최대연속": st.column_config.NumberColumn("최대(Max)"),
                    "평균스킵": st.column_config.NumberColumn("평균스킵"),
                    "직전스킵": st.column_config.NumberColumn("직전스킵"),
                    "연속점수": st.column_config.NumberColumn("기세점수", format="%.1f"),
                    "징검다리점수": st.column_config.NumberColumn("탄성점수", format="%.1f"),
                    "통합크레이지점수": st.column_config.NumberColumn("최종점수", format="%.1f")
                })

            st.markdown("""
            * 🟨 **진한 노란색:** 직전스킵과 평균스킵 차이가 1 이내 (**반등 임계점 도달 / 강력 후보**)
            * 🔴 **진한 빨간색:** 직전스킵 > 평균스킵 (**에너지 응축 / 독립적 반등**)
            * 🔵 **진한 파란색:** 현재 미출현 중 (**잠재적 콜드 / 반등 대기**)
            """)

            st.divider()
            
            # --- [원본 보존] 공식 및 수치 해석 섹션 ---
            st.subheader("📝 점수 산출 공식 및 수치 해석")
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.info("#### 🏃‍♂️ 기세 지수 (Streak Score)")
                st.latex(r"S_{streak} = \frac{(Max - Curr)}{Max} \times 100")
                st.markdown("* **해석:** 과거 기록 대비 현재 얼마나 더 나올 여력이 있는지 측정합니다.")
                
                st.success("#### ⏳ 독립적 스킵 주기 (Skip Interval)")
                st.markdown("""
                * **차이 1 이내(노란색):** 번호가 자신의 평균 리듬에 정확히 도달했습니다. **출현 확률이 매우 높은 지점**입니다.
                """)
            
            with col_right:
                st.info("#### 🌉 징검다리 탄성 (Bridge Elasticity)")
                st.markdown("1. **평균 간격($Gap_{avg}$):** 최근 10회 중 출현 사이 평균 간격")
                st.latex(r"100 - (|1.0 - Gap_{avg}| \times 40)") 
                st.markdown("* **해석:** 최근 10회 내에서 번호가 얼마나 규칙적인 리듬을 유지하는지 측정합니다.")


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
