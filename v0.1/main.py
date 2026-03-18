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

# --- 1. 데이터 입력 화면 (중략 - 기존 코드 유지) ---
if menu == "데이터 입력":
    st.title("🎰 로또 당첨 패턴 분석기")
    # ... (기존 데이터 입력 로직)

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

            # --- 업데이트된 공식 가이드 설명 ---
            with st.expander("📘 크레이지 통합 점수 공식 가이드 (업데이트됨)"):
                st.markdown("### **Total Score = (연속 지수 × 0.6) + (징검다리 탄성 × 0.4)**")
                c1, c2 = st.columns(2)
                with c1:
                    st.info("#### 🏃‍♂️ 연속 지수 (Streak)")
                    st.latex(r"S_{streak} = \frac{(Max - Curr + 1)}{Max} \times 100")
                    st.write("과거 기록 경신 여력을 측정합니다. 점수가 높을수록 현재 기세가 과거 기록 대비 더 뻗어나갈 가능성이 큼을 의미합니다.")
                with c2:
                    st.info("#### 🌉 징검다리 탄성 (Bridge Elasticity)")
                    st.write("""
                    **간격 분석(Interval Analysis) 도입:**
                    * **리듬감 측정:** 최근 10회차 내 출현 간격이 규칙적일수록(평균 간격 1회) 높은 점수를 부여합니다.
                    * **최근성 가중치:** 최근에 출현했을수록 탄성이 살아있다고 판단하며, 너무 오래 쉬면 탄성 점수가 급격히 감소합니다.
                    * **단순 빈도 탈피:** 단순히 많이 나온 번호가 아닌, '다시 나올 타이밍'이 된 번호를 찾아냅니다.
                    """)
        else:
            st.warning("선택한 범위 내에 분석 대상이 되는 번호가 없습니다.")

# --- 3. 특정 번호 분석 및 4. 콜드 번호 추출 (중략 - 기존 코드 유지) ---
# ...
