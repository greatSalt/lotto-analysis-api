import streamlit as st
import pandas as pd

import coldNum
from savepicked import init_saved_picks, display_sidebar_picks, save_picks_to_sheets, get_highlight_style
from specialNum import analyze_specific_number
from streamlit_gsheets import GSheetsConnection
from into_lottoDB import save_to_gsheet, get_recent_data
from crazyLogic import get_crazy_analysis

st.set_page_config(page_title="로또 분석 프로 v0.1", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1q8P3SClxNSYsAXwBgk3__y44XxZwI_FTj-eE9uQeVHE/edit?gid=0#gid=0"

# 1. 초기화 및 사이드바 표시 (최상단)
init_saved_picks(conn, SHEET_URL)

st.sidebar.title("🎮 메뉴 선택")
# 사이드바 메뉴 선택 아래에 바로 배치
with st.sidebar:
    menu = st.sidebar.radio("기능 선택", ["데이터 입력", "크레이지 번호 추출", "콜드 번호 추출", "특정 번호 분석"])
    display_sidebar_picks(conn, SHEET_URL) # 👈 어떤 메뉴에서든 내 번호가 보임
    
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
    
    st.divider()

    # 분석 데이터 호출
    analyze_count = st.number_input("분석 범위(최근 회차)", 10, 100, 30)
    df = get_recent_data(conn, SHEET_URL, count=analyze_count)
    
    if not df.empty:
        analysis_df = get_crazy_analysis(df)
        if not analysis_df.empty:
            # 기본 정렬 및 데이터 가공
            display_df = analysis_df.sort_values(by="통합크레이지점수", ascending=False)
            
            # 체크박스 상태 반영 (저장된 번호는 체크된 상태로 시작)
            display_df['선택'] = display_df['번호'].apply(lambda x: x in st.session_state.my_saved_picks)
            
            # 컬럼 순서 조정
            cols = ['선택', '번호', '현재연속', '최대연속', '평균스킵', '직전스킵', '연속점수', '징검다리점수', '통합크레이지점수']
            display_df = display_df[cols]

            # --- [2] 스타일 적용 (savepicked.py의 굵은 글씨 + 배경색 로직) ---
            styled_df = display_df.style.apply(get_highlight_style, axis=1)

            # --- [3] 데이터 에디터 (체크박스 및 굵은 글씨 출력) ---
            edited_df = st.data_editor(
                styled_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "선택": st.column_config.CheckboxColumn("선택", default=False),
                    "번호": st.column_config.NumberColumn("번호"),
                    "평균스킵": st.column_config.NumberColumn("평균스킵", format="%.1f"),
                    "직전스킵": st.column_config.NumberColumn("직전스킵"),
                    "연속점수": st.column_config.NumberColumn("기세점수", format="%.1f"),
                    "징검다리점수": st.column_config.NumberColumn("탄성점수", format="%.1f"),
                    "통합크레이지점수": st.column_config.NumberColumn("최종점수", format="%.1f")
                },
                disabled=[c for c in display_df.columns if c != '선택'] # 선택 열만 수정 가능
            )

            # --- [4] 적용 버튼 및 데이터 저장 ---
            if st.button("💾 선택 번호 저장"):
                # 체크된 행에서 번호만 추출하여 세션 저장
                new_picks = edited_df[edited_df['선택'] == True]['번호'].tolist()
                save_picks_to_sheets(conn, SHEET_URL, new_picks) # 영구 저장 실행
                st.toast("주요 번호가 저장되었습니다!")
                st.rerun()

            st.divider()
            
            # --- [5] 공식 및 수치 해석 섹션 (원본 보존) ---
            st.subheader("📝 점수 산출 공식 및 수치 해석")
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.info("#### 🏃‍♂️ 기세 지수 (Streak Score)")
                st.latex(r"S_{streak} = \frac{(Max - Curr)}{Max} \times 100")
                st.markdown("* **Max:** 역대 최대 연속 출현 / **Curr:** 현재 연속 출현")
                
                st.success("#### ⏳ 독립적 스킵 주기 (Skip Interval)")
                st.markdown("""
                * **차이 1 이내(노란색):** 번호가 자신의 평균 리듬에 정확히 도달했습니다.
                * **저장된 번호:** 표에서 **아주 굵은 글씨**와 테두리로 강조됩니다.
                """)
            
            with col_right:
                st.info("#### 🌉 징검다리 탄성 (Bridge Elasticity)")
                st.markdown("1. **평균 간격($Gap_{avg}$):** 최근 10회 중 출현 사이 평균 간격")
                st.latex(r"100 - (|1.0 - Gap_{avg}| \times 40)") 
                st.markdown("* **해석:** 최근 10회 내에서 번호가 얼마나 규칙적인 리듬을 유지하는지 측정합니다.")
            
            st.divider()
            
            # --- [5] 공식 및 수치 해석 섹션 (색상별 정밀 가이드) ---
            st.subheader("📝 색상별 전략 및 공식 해석")
            
            # 3개의 컬럼으로 나누어 시각적으로 배치
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.warning("#### 🟡 노란색 (임계점 도달)")
                # 절대값 기호를 사용한 임계점 공식
                st.latex(r"|Skip_{curr} - Skip_{avg}| \le 1")
                st.markdown("""
                - **상태:** 고유 리듬 도달
                - **해석:** 번호가 자신의 평균 주기 근처에 도달하여 **반등 확률이 가장 높은** 최적의 타이밍입니다.
                """)

            with c2:
                st.error("#### 🔴 빨간색 (에너지 응축)")
                # 평균 초과 공식
                st.latex(r"Skip_{curr} > Skip_{avg}")
                st.markdown("""
                - **상태:** 통계적 회귀 임박
                - **해석:** 평균보다 훨씬 긴 시간 동안 미출현하여 **에너지가 극도로 응축**된 상태입니다.
                """)

            with c3:
                st.info("#### 🔵 파란색 (최근 기세)")
                # 연속 출현 지표
                st.latex(r"Streak_{curr} = 0")
                st.markdown("""
                - **상태:** 핫 넘버 (Hot Number)
                - **해석:** 방금 막 당첨되어 **출현 기세가 살아있는** 번호입니다. 연쇄 출현 흐름을 포착합니다.
                """)
            
            st.caption("※ 모든 수치는 사용자님의 '분석 범위' 설정에 따라 실시간으로 재계산됩니다.")

elif menu == "특정 번호 분석":
    st.title("🔍 번호 심층 분석")
    
    # 입력 UI: 번호와 분석 범위를 나란히 배치
    col1, col2 = st.columns(2)
    with col1:
        target_num = st.number_input("분석할 번호", 1, 45, 1)
    with col2:
        # 분석 범위 입력 추가 (기본 100회차, 최대 500회차까지 확장 가능)
        deep_analyze_count = st.number_input("심층 분석 범위(최근 회차)", 10, 500, 100)
    
    st.divider()

    # 설정된 범위(deep_analyze_count)만큼 데이터 호출
    df = get_recent_data(conn, SHEET_URL, count=deep_analyze_count)
    
    if not df.empty:
        # 심층 분석 실행
        res = analyze_specific_number(df, target_num)
        
        if res:
            st.write(res)
            # 현재 분석 기준 회차 표시
            st.caption(f"※ 최근 {deep_analyze_count}회차 데이터를 기반으로 분석된 결과입니다.")
    else:
        st.error("데이터를 불러오지 못했습니다. 구글 시트 연결 상태를 확인하세요.")


elif menu == "콜드 번호 추출":
    st.title("🧊 콜드 번호 리포트")
    df = get_recent_data(conn, SHEET_URL, count=0)
    cold_df = coldNum.get_cold_analysis(df)
    st.dataframe(cold_df.sort_values("현재미출현", ascending=False).head(15), use_container_width=True)

st.sidebar.divider()
st.sidebar.caption("v0.1 - 통계 분석 시스템")
