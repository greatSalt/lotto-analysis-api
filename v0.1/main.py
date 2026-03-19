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
            # 1. 기본 정렬
            display_df = analysis_df.sort_values(by="통합크레이지점수", ascending=False).copy()
            
            # 2. [추가] 순번(No.) 컬럼 생성 (1부터 시작)
            display_df.insert(0, 'No.', range(1, len(display_df) + 1))
            
            # 3. 체크박스 상태 반영
            display_df['선택'] = display_df['번호'].apply(lambda x: x in st.session_state.my_saved_picks)
            
            # 4. 컬럼 순서 조정 (No.를 가장 앞으로, 그 다음 선택)
            cols = ['No.', '선택', '번호', '현재연속', '최대연속', '평균스킵', '직전스킵', '연속점수', '징검다리점수', '통합크레이지점수']
            display_df = display_df[cols]

            # 5. 스타일 적용
            styled_df = display_df.style.apply(get_highlight_style, axis=1)

            # 6. 데이터 에디터 출력
            edited_df = st.data_editor(
                styled_df,
                hide_index=True, # 기존의 0부터 시작하는 인덱스는 숨김
                use_container_width=True,
                column_config={
                    "No.": st.column_config.NumberColumn("No.", format="%d"),
                    "선택": st.column_config.CheckboxColumn("선택", default=False),
                    "번호": st.column_config.NumberColumn("번호"),
                    "평균스킵": st.column_config.NumberColumn("평균스킵", format="%.1f"),
                    "연속점수": st.column_config.NumberColumn("기세점수", format="%.1f"),
                    "징검다리점수": st.column_config.NumberColumn("탄성점수", format="%.1f"),
                    "통합크레이지점수": st.column_config.NumberColumn("최종점수", format="%.1f")
                },
                disabled=[c for c in display_df.columns if c != '선택']
            )

            # 7. 적용 버튼 및 데이터 저장
            if st.button("💾 선택 번호 저장"):
                new_picks = edited_df[edited_df['선택'] == True]['번호'].tolist()
                save_picks_to_sheets(conn, SHEET_URL, new_picks)
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
                st.latex(r"|Skip_{last} - Skip_{avg}| \le 1")
                st.markdown("- **의미:** 자기 주기 회귀")
                st.caption("평균 주기만큼 쉬고 반등을 준비하는 최적 타이밍")
            
            with c2:
                st.error("#### 🔴 빨간색 (에너지 응축)")
                st.latex(r"Skip_{last} > Skip_{avg}")
                st.markdown("- **의미:** 평균 초과 미출현")
                st.caption("평소보다 오래 침묵하여 에너지가 과응축된 상태")
            
            with c3:
                st.info("#### 🔵 파란색 (미출현/콜드)")
                st.latex(r"Streak_{curr} = 0")
                st.markdown("- **의미:** 연속 출현 중단")
                st.caption("최근 당첨 번호에서 빠져 흐름이 멈춘 상태")

            st.caption("※ 모든 수치는 사용자님의 '분석 범위' 설정에 따라 실시간으로 재계산됩니다.")

elif menu == "특정 번호 분석":
    st.title("🔍 번호 심층 분석")
    
    # 입력 UI: 번호와 분석 범위를 나란히 배치
    col1, col2 = st.columns(2)
    with col1:
        target_num = st.number_input("분석할 번호", 1, 45, 1)
    with col2:
        # 분석 범위 입력 추가 (기본 100회차, 최대 500회차까지 확장 가능)
        deep_analyze_count = st.number_input("심층 분석 범위(최근 회차)", 10, 500, 30)
    
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
    
    # 데이터 호출
    df = get_recent_data(conn, SHEET_URL, count=0)
    
    if not df.empty:
        cold_df = coldNum.get_cold_analysis(df)
        
        # 1. 미출현 회차순으로 정렬 후 상위 15개 추출
        display_cold = cold_df.sort_values("현재미출현", ascending=False).head(15).copy()
        
        # 2. 인덱스를 1부터 15까지 새로 부여 (No. 표시용)
        display_cold.index = range(1, len(display_cold) + 1)
        
        # 3. 데이터프레임 출력 (인덱스 이름을 'No.'로 지정)
        st.dataframe(
            display_cold, 
            use_container_width=True,
            column_config={
                "index": st.column_config.NumberColumn("No.", format="%d")
            }
        )
        
        st.info("💡 '현재미출현' 수치가 높을수록 오랫동안 나오지 않은 '차갑게 식은' 번호들입니다.")
    else:
        st.error("데이터를 불러올 수 없습니다.")


st.sidebar.divider()
st.sidebar.caption("v0.1 - 통계 분석 시스템")
