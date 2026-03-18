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
            st.success("저장 완료!")

elif menu == "크레이지 번호 추출":
    st.title("🔥 크레이지 번호 분석 리포트")
    analyze_count = st.number_input("분석 범위(최근 회차)", 0, 100, 30)
    df = get_recent_data(conn, SHEET_URL, count=analyze_count)
    
    if not df.empty:
        analysis_df = get_crazy_analysis(df)
        display_df = analysis_df.sort_values(by="통합크레이지점수", ascending=False)
        display_df.insert(0, '순위', range(1, len(display_df) + 1))
        
        st.dataframe(display_df, use_container_width=True, hide_index=True,
            column_config={
                "연속점수": st.column_config.ProgressColumn("기세(연속)", min_value=0, max_value=100),
                "징검다리점수": st.column_config.ProgressColumn("탄성(리듬)", min_value=0, max_value=100),
                "통합크레이지점수": st.column_config.NumberColumn("최종 점수", format="%.1f 🔥")
            })

        st.divider()
        with st.expander("💡 점수 계산법 (직관 가이드)"):
            st.markdown("### **최종 점수 = (기세 점수 × 0.6) + (탄성 점수 × 0.4)**")
            
            c1, c2 = st.columns(2)
            with c1:
                st.info("#### 🏃‍♂️ 기세(연속) 점수 기준")
                st.write("- **100점:** 현재 기록이 역대 최대 기록을 막 돌파했음")
                st.write("- **80점:** 역대 최대 기록까지 약 1~2회 남았음")
                st.write("- **50점:** 이제 막 연속 출현을 시작했음")
                st.caption("※ 과거 기록(Max) 대비 현재(Curr)의 진행률을 봅니다.")
            
            with c2:
                st.info("#### 🌉 탄성(리듬) 점수 기준")
                st.write("- **100점:** 최근 10회 중 '한 번 쉬고 한 번 나오기' 완벽 유지")
                st.write("- **70점:** 최근 10회 중 3~4번 나오며 리듬 유지 중")
                st.write("- **30점:** 가끔 나오지만 리듬이 불규칙하거나 뜸함")
                st.caption("※ 최근 10회차 내 '평균 간격'과 '최근성'을 봅니다.")

elif menu == "특정 번호 분석":
    st.title("🔍 번호 심층 분석")
    target_num = st.number_input("번호", 1, 45, 1)
    df = get_recent_data(conn, SHEET_URL, count=50)
    res = analyze_specific_number(df, target_num)
    if res:
        st.json(res)

elif menu == "콜드 번호 추출":
    st.title("🧊 콜드 번호")
    df = get_recent_data(conn, SHEET_URL, count=0)
    cold_df = coldNum.get_cold_analysis(df)
    st.dataframe(cold_df.sort_values("현재미출현", ascending=False).head(15))

st.sidebar.divider()
st.sidebar.caption("v0.1 - 데이터 기반 통계 분석")
