import streamlit as st
import pandas as pd
import random
import datetime

from streamlit_gsheets import GSheetsConnection
from into_lottoDB import save_to_gsheet, get_recent_data
from crazyLogic import get_crazy_analysis  # 수정된 로직이 반영된 모듈

# 설정 및 연결
st.set_page_config(page_title="로또 분석 프로 v0.1", layout="wide") # 리포트 가독성을 위해 wide 레이아웃 권장
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1q8P3SClxNSYsAXwBgk3__y44XxZwI_FTj-eE9uQeVHE/edit?gid=0#gid=0"

# 사이드바 메뉴 구성
st.sidebar.title("🎮 메뉴 선택")
menu = st.sidebar.radio("원하는 기능을 선택하세요", ["데이터 입력", "크레이지 번호 추출"])

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
    
    # 회차 선택 UI (메인 화면 상단 배치, 디폴트 30)
    col_config = st.columns([2, 3])
    with col_config[0]:
        analyze_count = st.number_input(
            "분석할 최근 회차 범위를 입력하세요 (0=전체)", 
            min_value=0, 
            value=30, 
            step=5
        )
    
    df = get_recent_data(conn, SHEET_URL, count=analyze_count)
    
    if not df.empty:
        # 회차 범위 및 실제 분석 개수 계산
        latest_round = df['round'].max()
        earliest_round = df['round'].min()
        actual_round_count = df['round'].nunique()
        
        st.subheader(f"✨ {earliest_round}회 ~ {latest_round}회 분석 결과")
        
        # 분석 함수 호출 (crazyLogic.py)
        analysis_df = get_crazy_analysis(df)
        
        if not analysis_df.empty:
            # 데이터 가공 및 정렬
            display_df = analysis_df.copy()
            display_df.columns = ["번호", "현재연속출현횟수", "최대연속출현횟수", "연속출현확률"]
            
            # 확률 기준 내림차순 정렬 후 순위(No.) 부여
            display_df = display_df.sort_values(by="연속출현확률", ascending=False)
            display_df.insert(0, 'No.', range(1, len(display_df) + 1))

            st.write(f"📊 최근 {actual_round_count}개 회차 데이터를 기반으로 분석을 완료했습니다.")
            
            # 테이블 출력
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "No.": st.column_config.NumberColumn("순위"),
                    "번호": st.column_config.NumberColumn("로또번호"),
                    "연속출현확률": st.column_config.NumberColumn(format="%.1f %%")
                }
            )
            
            # 상위 추천 번호
            st.divider()
            top_6_rank = display_df.head(6)["번호"].tolist()
            st.success(f"✅ 현재 기세 기준 추천 조합(순위 1~6위): {sorted(top_6_rank)}")

            # 공식 가이드 설명
            st.markdown(f"""
            ---
            ### 📘 크레이지 분석 공식 가이드
            이 리포트는 **현재 기세가 살아있는 번호**만을 대상으로 분석합니다.
            
            1. **분석 대상:** 현재 연속으로 출현 중인 번호만 표시 (현재 연속출현횟수 0회인 번호 제외)
            2. **연속출현확률 공식:** $$ \\frac{{\\text{{과거 최대 연속출현}} - \\text{{현재 연속출현}}}}{{\\text{{과거 최대 연속출현}}}} \\times 100 $$
            3. **의미:** * 확률이 **높을수록** 과거 최대 기록 대비 현재 더 나올 수 있는 여력이 큼을 의미합니다.
               * 확률이 **0%에 가까울수록** 현재 기세가 이미 과거의 최고 기록에 도달했음을 의미합니다.
            """)
        else:
            st.warning("선택한 범위 내에 현재 연속 출현 중인 번호가 없습니다.")

st.sidebar.divider()
st.sidebar.caption("본 프로그램은 통계적 재미를 위한 것이며, 당첨을 보장하지 않습니다.")
