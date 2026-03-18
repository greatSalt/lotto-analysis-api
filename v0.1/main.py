import streamlit as st
import pandas as pd
import random
import datetime
import coldNum

from specialNum import analyze_specific_number
from streamlit_gsheets import GSheetsConnection
from into_lottoDB import save_to_gsheet, get_recent_data
from crazyLogic import get_crazy_analysis

# 설정 및 연결
st.set_page_config(page_title="로또 분석 프로 v0.1", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1q8P3SClxNSYsAXwBgk3__y44XxZwI_FTj-eE9uQeVHE/edit?gid=0#gid=0"

# 사이드바 메뉴 구성
st.sidebar.title("🎮 메뉴 선택")
menu = st.sidebar.radio("원하는 기능을 선택하세요", ["데이터 입력", "크레이지 번호 추출", "콜드 번호 추출", "특정 번호 분석"])

# --- 1. 데이터 입력 화면 ---
if menu == "데이터 입력":
    st.title("🎰 로또 당첨 패턴 분석기")
    st.subheader("📥 데이터 입력")
    st.info("최신 회차의 당첨 번호를 입력하고 시트에 저장하세요.")
    
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
            data_to_save = {
                "round": int(col_drw),
                "n1": n1, "n2": n2, "n3": n3,
                "n4": n4, "n5": n5, "n6": n6,
                "bonus": bonus
            }
            updated_df = save_to_gsheet(conn, SHEET_URL, data_to_save)
            st.success(f"{col_drw}회차 데이터가 저장되었습니다!")
            st.balloons()
            st.dataframe(updated_df.head(5))

# --- 2. 크레이지 번호 추출 화면 ---
elif menu == "크레이지 번호 추출":
    st.title("🔥 크레이지 번호 분석 리포트")
    
    col_config = st.columns([2, 3])
    with col_config[0]:
        analyze_count = st.number_input(
            "분석할 최근 회차 범위를 입력하세요 (0=전체)", 
            min_value=0, value=30, step=5, key="crazy_range"
        )
    
    df = get_recent_data(conn, SHEET_URL, count=analyze_count)
    
    if not df.empty:
        latest_round = df['round'].max()
        earliest_round = df['round'].min()
        actual_round_count = df['round'].nunique()
        
        st.subheader(f"✨ {earliest_round}회 ~ {latest_round}회 분석 결과")
        
        analysis_df = get_crazy_analysis(df)
        
        if not analysis_df.empty:
            # 통합 점수 기준 정렬 및 데이터 가공
            display_df = analysis_df.sort_values(by="통합크레이지점수", ascending=False)
            display_df.insert(0, '순위', range(1, len(display_df) + 1))

            st.write(f"📊 최근 {actual_round_count}개 회차 데이터를 기반으로 통합 에너지를 분석했습니다.")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "순위": st.column_config.NumberColumn("순위"),
                    "번호": st.column_config.NumberColumn("로또번호"),
                    "연속점수": st.column_config.ProgressColumn("연속 에너지", min_value=0, max_value=100, format="%.1f"),
                    "징검다리점수": st.column_config.ProgressColumn("징검다리 탄성", min_value=0, max_value=100, format="%.1f"),
                    "통합크레이지점수": st.column_config.NumberColumn("최종 점수", format="%.1f 🔥")
                }
            )
            
            st.divider()
            top_6_rank = display_df.head(6)["번호"].tolist()
            st.success(f"✅ 통합 크레이지 추천 조합(1~6위): {sorted(top_6_rank)}")

            # --- 공식 가이드 설명 추가 ---
            with st.expander("📘 크레이지 통합 점수 공식 가이드 (필독)"):
                st.markdown("### **Total Score = (연속 지수 × 0.6) + (징검다리 지수 × 0.4)**")
                c1, c2 = st.columns(2)
                with c1:
                    st.info("#### 🏃‍♂️ 연속 지수 (Streak)")
                    st.latex(r"S_{streak} = \frac{(Max - Curr + 1)}{Max} \times 100")
                    st.write("과거 기록 경신 여력을 측정합니다. 점수가 높을수록 현재 기세가 과거 기록 대비 더 뻗어나갈 가능성이 큼을 의미합니다.")
                with c2:
                    st.info("#### 🌉 징검다리 지수 (Bridge)")
                    st.latex(r"S_{bridge} = \frac{\text{Count in 10 rounds}}{5} \times 100")
                    st.write("최근 10회 내 출현 빈도를 측정합니다. 잠시 쉬더라도 금방 다시 튀어나오는 탄성을 점수화합니다.")
        else:
            st.warning("선택한 범위 내에 분석 대상이 되는 번호가 없습니다.")

# --- 3. 특정 번호 분석 화면 ---
elif menu == "특정 번호 분석":
    st.title("🔍 특정 번호 심층 분석")
    
    col_ui = st.columns([1, 1, 2])
    with col_ui[0]:
        target_num = st.number_input("분석할 번호 (1~45)", 1, 45, value=1)
    with col_ui[1]:
        analyze_count = st.number_input("분석 회차 범위 (0=전체)", min_value=0, value=50, step=10, key="special_range")
    
    df = get_recent_data(conn, SHEET_URL, count=analyze_count)
    
    if not df.empty:
        latest_round = df['round'].max()
        earliest_round = df['round'].min()
        actual_count = len(df)
        
        res = analyze_specific_number(df, target_num) 
        
        if res:
            st.subheader(f"📑 {target_num}번 분석 리포트 ({earliest_round}회 ~ {latest_round}회)")
            st.info(f"선택하신 최근 {actual_count}개 회차 데이터를 바탕으로 분석한 결과입니다.")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("범위 내 출현 횟수", f"{res['총출현횟수']}회")
            m2.metric("현재 연속 기록", f"{res['현재연속출현']}회")
            m3.metric("과거 최대 연속", f"{res['최대연속출현']}회")
            m4.metric("현재 미출현 기간", f"{res['현재미출현기간']}회차")
            
            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🚩 상태 진단")
                if res['현재연속출현'] > 0:
                    st.success(f"🔥 {target_num}번은 현재 {res['현재연속출현']}회 연속 등장하며 흐름을 타고 있습니다!")
                else:
                    st.warning(f"🧊 {target_num}번은 현재 {res['현재미출현기간']}회차 동안 출현하지 않았습니다.")
                
                if res['최근출현회차'] > 0:
                    st.write(f"**마지막 출현 회차:** {res['최근출현회차']}회")
                else:
                    st.write("**해당 범위 내 출현 기록이 없습니다.**")
            with col_b:
                st.subheader("📅 최근 출현 기록 (최신순)")
                if res['출현기록']:
                    st.write(res['출현기록'][:20]) 
                    st.caption("최대 20개까지만 표시됩니다.")
                else:
                    st.write("기록 없음")

# --- 4. 콜드 번호 추출 화면 ---
elif menu == "콜드 번호 추출":
    st.title("🧊 콜드 번호 분석 리포트")
    st.info("오랫동안 출현하지 않아 통계적 반등이 기대되는 번호들을 분석합니다.")
    
    df = get_recent_data(conn, SHEET_URL, count=0)
    
    if not df.empty:
        cold_df = coldNum.get_cold_analysis(df)
        display_cold = cold_df.sort_values(by="현재미출현", ascending=False).head(15)
        display_cold.insert(0, '순위', range(1, len(display_cold) + 1))
        
        st.subheader("📊 장기 미출현 번호 TOP 15")
        st.dataframe(
            display_cold,
            use_container_width=True,
            hide_index=True,
            column_config={
                "콜드지수": st.column_config.NumberColumn("반등 임계점", format="%.1f %%")
            }
        )
        
        st.divider()
        st.markdown("""
        ### 💡 콜드 번호 활용 팁
        * **반등 임계점:** 해당 번호의 과거 최대 미출현 기록에 얼마나 근접했는지를 나타냅니다. 
        * **전략:** 100%에 가까운 번호는 조만간 출현할 확률이 통계적으로 높아진 상태입니다.
        * **조합:** 크레이지 번호(Hot) 4개 + 콜드 번호(Cold) 2개 조합을 추천합니다.
        """)
        
st.sidebar.divider()
st.sidebar.caption("본 프로그램은 통계적 재미를 위한 것이며, 당첨을 보장하지 않습니다.")
