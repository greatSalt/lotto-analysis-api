import streamlit as st
import pandas as pd
import coldNum
from specialNum import analyze_specific_number
from streamlit_gsheets import GSheetsConnection
from into_lottoDB import save_to_gsheet, get_recent_data
from crazyLogic import get_crazy_analysis

# 기본 설정
st.set_page_config(page_title="로또 분석 프로 v0.1", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1q8P3SClxNSYsAXwBgk3__y44XxZwI_FTj-eE9uQeVHE/edit?gid=0#gid=0"

# 사이드바
st.sidebar.title("🎮 메뉴 선택")
menu = st.sidebar.radio("기능 선택", ["데이터 입력", "크레이지 번호 추출", "콜드 번호 추출", "특정 번호 분석"])

# --- 1. 데이터 입력 ---
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
            st.success("데이터가 성공적으로 저장되었습니다!")

# --- 2. 크레이지 번호 추출 ---
elif menu == "크레이지 번호 추출":
    st.title("🔥 크레이지 번호 분석 리포트")
    analyze_count = st.number_input("분석 범위(최근 회차)", 0, 100, 30)
    df = get_recent_data(conn, SHEET_URL, count=analyze_count)
    
    if not df.empty:
        analysis_df = get_crazy_analysis(df)
        if not analysis_df.empty:
            display_df = analysis_df.sort_values(by="통합크레이지점수", ascending=False)
            display_df.insert(0, '순위', range(1, len(display_df) + 1))
            
            st.dataframe(display_df, use_container_width=True, hide_index=True,
                column_config={
                    "연속점수": st.column_config.ProgressColumn("기세(연속)", min_value=0, max_value=100, format="%.1f"),
                    "징검다리점수": st.column_config.ProgressColumn("탄성(리듬)", min_value=0, max_value=100, format="%.1f"),
                    "통합크레이지점수": st.column_config.NumberColumn("최종 점수", format="%.1f 🔥")
                })

            st.divider()
            
            # --- 공식 및 수치 해석 가이드 섹션 ---
            st.subheader("📝 점수 산출 공식 및 수치 해석")
            st.markdown("### **최종 점수 = (기세 점수 × 0.6) + (탄성 점수 × 0.4)**")
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.info("#### 🏃‍♂️ 기세 지수 (Streak Score)")
                st.latex(r"S_{streak} = \frac{(Max - Curr + 1)}{Max} \times 100")
                st.markdown("""
                **[변수 설명]**
                * **Max:** 해당 번호의 역대 최대 연속 출현 횟수
                * **Curr:** 현재 진행 중인 연속 출현 횟수
                
                **[수치 해석 가이드]**
                * **100점에 가까울수록:** 과거 기록을 막 경신하기 시작했거나 기세가 최고조임을 의미합니다.
                * **점수가 낮을수록:** 이미 과거 기록을 한참 초과하여 통계적 반락(미출현) 가능성이 있음을 시사합니다.
                """)
            
            with col_right:
                st.info("#### 🌉 징검다리 탄성 (Bridge Elasticity)")
                st.markdown("""
                최근 10회차 내에서 번호가 얼마나 규칙적인 리듬(퐁당퐁당)으로 튀어 오르는지 측정합니다.
                
                **[계산 단계]**
                1. **평균 간격($Gap_{avg}$):** 최근 10회 중 출현한 회차들 사이의 평균 미출현 일수 계산.
                """)
                st.info("2. **기본 탄성 점수:**")
                st.latex(r"100 - (|1.0 - Gap_{avg}| \times 40)") 
                st.markdown("(간격이 1회일 때 100점 만점 기준)")
                st.info("3. **최근성 보너스:**")
                st.latex(r"(마지막\ 출현\ 위치 + 1) \times 10")
                st.markdown("*(최근 1~2회차 내에 나왔을수록 탄성이 살아있다고 판단)*")
                
                st.info("**[수치 해석 가이드]**")
                st.markdown("""
                * **80점 이상:** 매우 규칙적인 징검다리 패턴 (예: 출-미-출-미-출) 
                * **40점 이하:** 불규칙하거나 최근 출현 기세가 꺾인 상태
                """)
        else:
            st.warning("분석 범위 내에 현재 출현 중인 크레이지 번호가 없습니다.")

# --- 3. 특정 번호 분석 ---
elif menu == "특정 번호 분석":
    st.title("🔍 번호 심층 분석")
    target_num = st.number_input("번호", 1, 45, 1)
    df = get_recent_data(conn, SHEET_URL, count=50)
    if not df.empty:
        res = analyze_specific_number(df, target_num)
        if res:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("총 출현", f"{res['총출현횟수']}회")
            m2.metric("현재 연속", f"{res['현재연속출현']}회")
            m3.metric("최대 연속", f"{res['최대연속출현']}회")
            m4.metric("미출현 기간", f"{res['현재미출현기간']}회차")

# --- 4. 콜드 번호 추출 ---
elif menu == "콜드 번호 추출":
    st.title("🧊 콜드 번호 리포트")
    df = get_recent_data(conn, SHEET_URL, count=0)
    if not df.empty:
        cold_df = coldNum.get_cold_analysis(df)
        st.dataframe(cold_df.sort_values("현재미출현", ascending=False).head(15), use_container_width=True)

st.sidebar.divider()
st.sidebar.caption("v0.1 - 데이터 기반 통계 분석 시스템")
