import streamlit as st
import pandas as pd
import plotly.express as px

from coldNum import get_cold_analysis
from savepicked import display_sidebar_picks, get_highlight_style, init_all_saved_data, save_to_sheets_by_type, save_recommended_picks
from specialNum import analyze_specific_number
from streamlit_gsheets import GSheetsConnection
from into_lottoDB import save_to_gsheet, get_recent_data, analyze_combination
from crazyLogic import get_crazy_analysis
from formular_description import display_formula_guide
import analysis_to_gsheet as saver
from iteration_predictor import render_carryover_analysis
from empty_zone_engine import get_confirmed_empty_zone, color_rows, apply_strategy_style
from combination_engine import generate_strategic_combinations, get_advanced_stat_analysis, get_comprehensive_analysis
from winning_skip_analysis import analyze_winning_skip_distribution, render_skip_group_weight_ui
from target_end_analysis import render_target_end_analysis

st.set_page_config(page_title="로또 분석 프로 v0.1", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1q8P3SClxNSYsAXwBgk3__y44XxZwI_FTj-eE9uQeVHE/edit?gid=0#gid=0"

# 1. 초기화 및 사이드바 표시 (최상단)
#init_saved_picks(conn, SHEET_URL)
init_all_saved_data(conn, SHEET_URL)

# --- 데이터 로드 및 사이드바 공통 설정 ---
# 분석에 필요한 데이터를 넉넉하게 한 번만 가져옵니다.
df_raw = get_recent_data(conn, SHEET_URL, count=0)    #모든 데이터를 가져온다. 

st.sidebar.title("🎮 메뉴 선택")

st.sidebar.title("🛠️ 통합 분석 설정")

#모든 메뉴에서 공통으로 사용할 회차범위를 설정
analyze_range = st.sidebar.slider(
    "통합 분석 범위 (최근 회차)", 
    min_value=5, 
    max_value=300, 
    value=30, 
    step=5
)

# 모든 메뉴에서 사용할 공통 분석 데이터 (슬라이싱)
df = df_raw.head(analyze_range).copy()

with st.sidebar:
    menu = st.sidebar.radio("기능 선택", ["데이터 입력", "크레이지 번호 추출", "콜드 번호 추출", "특정 번호 분석", "📊 이월수 예측", "🎯 추천번호 분석", "당첨번호 주기 분석", "동끝수 상세 분석"])
    display_sidebar_picks(conn, SHEET_URL) # 👈 어떤 메뉴에서든 내 번호가 보임

if menu == "데이터 입력":
    st.title("🎰 로또 데이터 입력 및 조합 분석")
    
    with st.form("lotto_input_form", clear_on_submit=False): # 분석을 위해 False 추천
        col_drw = st.number_input("회차", min_value=1, step=1)
        c = st.columns(6)
        n1 = c[0].number_input("No1", 1, 45, value=1)
        n2 = c[1].number_input("No2", 1, 45, value=2)
        n3 = c[2].number_input("No3", 1, 45, value=3)
        n4 = c[3].number_input("No4", 1, 45, value=4)
        n5 = c[4].number_input("No5", 1, 45, value=5)
        n6 = c[5].number_input("No6", 1, 45, value=6)
        bonus = st.number_input("Bonus", 1, 45, value=45)
        
        current_nums = [n1, n2, n3, n4, n5, n6]
        
        # 버튼 배치
        btn_col1, btn_col2 = st.columns(2)
        save_btn = btn_col1.form_submit_button("💾 DB 저장하기")
        analyze_btn = btn_col2.form_submit_button("🔍 조합 분석하기")

        if save_btn:
            data_to_save = {"round": int(col_drw), "n1": n1, "n2": n2, "n3": n3, "n4": n4, "n5": n5, "n6": n6, "bonus": bonus}
            save_to_gsheet(conn, SHEET_URL, data_to_save)
            st.success(f"{col_drw}회차 데이터 저장 완료!")

        if analyze_btn:
            st.divider()
            df_analysis, metrics = analyze_combination(current_nums, df, analyze_range)
            
            # 1. 개별 번호 상태 테이블(Crazy + Cold 엔진 결과)
            st.subheader("📊 번호별 정밀 지표")
            st.dataframe(df_analysis, use_container_width=True, hide_index=True)
            
            # 2. 조합 필터 (메트릭)
            st.subheader("⚙️ 조합 필터 검증")
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            m_col1.metric("홀짝", metrics["홀짝"])
            m_col2.metric("총합", metrics["총합"])
            m_col3.metric("AC", metrics["AC"])
            m_col4.metric("고저(저:고)", metrics["고저"])
            m_col5.metric("연번", metrics["연번"])

            # 로우 데이터 컬럼 (한 줄 표시)
            st.code(f"분석 조합: {sorted(current_nums)}")

elif menu == "크레이지 번호 추출":
    st.title("🔥 크레이지 번호 분석 리포트")
    
    st.divider()

    # 분석 데이터 호출
    #analyze_count = st.number_input("분석 범위(최근 회차)", 10, 100, 30)
    #df = get_recent_data(conn, SHEET_URL, count=analyze_count)
    
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
            cols = ['No.', '선택', '번호', '출현수', '출현율', '출현기대치', '현재연속', '최대연속', '연속점수', '탄성점수', '반등지수', '에너지지수', '평균스킵', '직전스킵', '현재스킵',  '변동성', '리듬점수', '박자상태', '임계점', '통합크레이지점수']
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
                    "출현수": st.column_config.NumberColumn("출현수"),
                    "출현율": st.column_config.NumberColumn("출현율", format="%.1f"),
                    "출현기대치": st.column_config.TextColumn("출현기대치"),
                    "현재연속": st.column_config.NumberColumn("현재연속"),
                    "최대연속": st.column_config.NumberColumn("최대연속"),
                    "연속점수": st.column_config.NumberColumn("연속점수", format="%.1f"),
                    "탄성점수": st.column_config.NumberColumn("탄성점수", format="%.1f"),
                    "반등지수": st.column_config.NumberColumn("반등지수", format="%.1f"),
                    "에너지지수": st.column_config.NumberColumn("에너지", format="%.2f"),
                    "평균스킵": st.column_config.NumberColumn("평균스킵", format="%.1f"),
                    "직전스킵": st.column_config.NumberColumn("직전스킵", format="%d"),
                    "현재스킵": st.column_config.NumberColumn("현재스킵", format="%d"),
                    "변동성": st.column_config.NumberColumn("변동성", format="%.2f"),
                    "리듬점수": st.column_config.NumberColumn("리듬점수", format="%.1f"),
                    "박자상태": st.column_config.TextColumn("박자상태"), # ✅ 추가 (🔥 표시용)   
                    "임계점": st.column_config.TextColumn("임계점"), # ✅ 추가 (🔥 표시용)
                    "통합크레이지점수": st.column_config.NumberColumn("최종점수", format="%.1f")
                },

                disabled=[c for c in display_df.columns if c != '선택']
            )

            # 7. 적용 버튼 및 데이터 저장
            if st.button("💾 선택 번호 저장"):
                new_picks = edited_df[edited_df['선택'] == True]['번호'].tolist()
                #save_picks_to_sheets(conn, SHEET_URL, new_picks)
                save_to_sheets_by_type(conn, SHEET_URL, new_picks, "PICK")
                st.toast("주요 번호가 저장되었습니다!")
                st.rerun()
        
            # --- 추가된 부분 ---
            st.divider() # 시각적 구분선
            saver.render_gsheet_button(edited_df, SHEET_URL)
            #바로가기 링크 제공 (아이콘과 버튼 스타일 활용)
            st.write("---") # 얇은 구분선
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # 클릭 시 새 탭으로 구글 시트가 열리는 링크 버튼
                st.link_button("📂 저장된 구글 시트 바로가기", SHEET_URL, use_container_width=True)
            
            with col2:
                # 시트 이용 팁 제공
                st.info("💡 **Tip**: 시트 상단 메뉴의 `보기 > 틀 고정`을 사용하면 번호를 더 편하게 보실 수 있습니다.")
            # ------------------

            st.divider()
            
            # --- [5] 공식 및 수치 해석 섹션 (최종 통합본) ---
            display_formula_guide(analyze_range)
            
elif menu == "특정 번호 분석":
    st.title("🔍 번호 심층 분석")
    
    # 입력 UI: 번호와 분석 범위를 나란히 배치
    col1, _ = st.columns([1, 2]) # 두 번째 컬럼은 무시, 입력창 크기 조절
    with col1:
        target_num = st.number_input("분석할 번호", 1, 45, 1)
    
    st.divider()

    # 설정된 범위(deep_analyze_count)만큼 데이터 호출
    #df = get_recent_data(conn, SHEET_URL, count=deep_analyze_count)
    
    if not df.empty:
        # 심층 분석 실행
        res = analyze_specific_number(df, target_num)
        
        if res:
            st.write(res)
            # 현재 분석 기준 회차 표시
            st.caption(f"※ 최근 {analyze_range}회차 데이터를 기반으로 분석된 결과입니다.")
    else:
        st.error("데이터를 불러오지 못했습니다. 구글 시트 연결 상태를 확인하세요.")


elif menu == "콜드 번호 추출":
    st.title("🧊 콜드 번호 리포트")
    
    # 데이터 호출
    #df = get_recent_data(conn, SHEET_URL, count=0)
    
    if not df.empty:
        # 세션에 데이터가 없거나 메뉴가 처음 로드될 때만 실행
        #if "cold_edited_df" not in st.session_state:
        cold_df = get_cold_analysis(df)
        display_cold = cold_df.sort_values("현재미출현", ascending=False).head(15).copy()
            # 구글 시트에서 기존 저장된 번호들 가져오기 (저장된 번호 로드)
        try:
            # SavedPicks 워크시트에서 번호 컬럼 추출
            saved_df = conn.read(spreadsheet=SHEET_URL, worksheet="SavedPicks")
            # PICK 유형만 필터링
            pick_only_df = saved_df[saved_df["유형"] == "PICK"]
            st.session_state.all_saved_picks = set(pd.to_numeric(pick_only_df["번호"], errors='coerce').dropna().astype(int))
        except:
            st.session_state.all_saved_picks = set()
        
        # 2. 인덱스를 1부터 15까지 새로 부여 (No. 표시용)
        display_cold = display_cold.reset_index(drop=True)
        display_cold.index = range(1, len(display_cold) + 1)
        display_cold = display_cold.reset_index().rename(columns={"index": "No."})
        
        # [핵심] 시트에 저장된 번호라면 '선택'을 True로 설정
        display_cold.insert(0, "선택", display_cold["번호"].apply(lambda x: x in st.session_state.all_saved_picks))
        # 세션 상태에 저장 (이제 rerun되어도 여기서 안 걸리고 아래 editor로 바로 감)
        st.session_state.cold_edited_df = display_cold
        
        # 3. 데이터 에디터로 변경 (사용자가 체크박스 조작 가능)
        # num_rows="fixed"로 설정하여 15개 행을 유지합니다.
        # st.data_editor의 결과를 다시 session_state에 저장하여 상태 유지
        edited_output = st.data_editor(
            st.session_state.cold_edited_df, 
            use_container_width=True,
            hide_index=True, # No. 컬럼을 따로 만들었으므로 인덱스는 숨김
            column_config={
                "No.": st.column_config.NumberColumn("No.", format="%d", disabled=True),
                "선택": st.column_config.CheckboxColumn("선택", default=False),
                "번호": st.column_config.NumberColumn("번호", format="%d", disabled=True),
                "현재미출현": st.column_config.NumberColumn("미출현 회차", format="%d회", disabled=True)
            },
            key="cold_num_editor"
        )
        # 에디터에서 변경된 내용을 세션 상태에 동기화
        #st.session_state.cold_edited_df = edited_output
        
        # 4. 저장 버튼 및 구글 시트 연동
        if st.button("📌 선택한 콜드번호 저장 및 공유", use_container_width=True):
            # A. 현재 화면에서 '체크된' 번호들
            currently_checked = set(edited_output[edited_output['선택'] == True]['번호'])
            # B. 현재 화면에서 '체크 해제된' 번호들 (기존에 있었더라도 지워야 할 경우를 위해)
            currently_unchecked = set(edited_output[edited_output['선택'] == False]['번호'])
            # C. [핵심] 전체 보관함 업데이트 (기존 전체 목록 + 새로 체크 - 체크 해제)
            final_picks = (st.session_state.all_saved_picks | currently_checked) - currently_unchecked
            
            # D. 최종 결과 저장
            save_to_sheets_by_type(conn, SHEET_URL, list(final_picks), "PICK")
            
            st.success(f"✅ 전체 보관함이 업데이트되었습니다! (총 {len(final_picks)}개)")
            
            # 세션 초기화 후 리런
            #del st.session_state.cold_edited_df
            st.rerun()
    else:
        st.error("데이터를 불러올 수 없습니다.")         
        
elif menu == "📊 이월수 예측":
    st.title("🔮이월수 전략 시뮬레이터")
    
    if not df.empty:
        render_carryover_analysis(df, analyze_range)
                
    # 확률 차트 (시각적 근거)
    st.write("💡 **이월수 개수별 표준 확률 분포**")
    chart_data = {"0개": 38, "1개": 43, "2개": 13, "3개+": 6}
    st.bar_chart(chart_data)

elif menu == "🎯 추천번호 분석":
    st.sidebar.subheader("⚙️ 멸 엔진 설정")
    #analyze_range = st.sidebar.slider("역사적 확률 분석 범위", 5, 300, 30) #range:min5~max300,default:30
    
    st.title("🎯 v2.5 전략 추천번호")
    
    #df = get_recent_data(conn, SHEET_URL)
    if not df.empty:
        decision = get_confirmed_empty_zone(df, analyze_range)
        
        # 멸구간 확정 브리핑
        st.subheader("🛡️ 멸구간 확정 리포트")
        for zone, data in decision.items():
            if data['is_empty']:
                st.error(f"🚫 **{zone} 제외 확정** : {data['reason']}")
            elif data['prob'] > 40:
                st.warning(f"⚠️ **{zone} 주의** : 멸 확률 {data['prob']:.1f}% (관찰 필요)")
        
        # 번호 필터링 및 우선순위 표시
        analysis_df = get_crazy_analysis(df)
        
        # 확정된 멸구간 번호 제외
        excluded_zones = [z for z, d in decision.items() if d['is_empty']]
        #zones_map = {'단번대':(1,10), '10번대':(11,20), '20번대':(21,30), '30번대':(31,40), '40번대':(41,45)}
        filtered_df = analysis_df.copy()
        
        # --- [추가] 전체 번호 선택 로직 시작 ---
        col_select_all, _ = st.columns([1, 4])
        with col_select_all:
            # 세션 상태를 활용하여 전체 선택 여부 관리
            select_all = st.checkbox("🔄 모든 번호 선택", value=False, key="all_nums_toggle")
        
        # 전체 선택이 체크되면 모든 행의 '선택' 컬럼을 True로 초기화
        if select_all:
            filtered_df['선택'] = True
        else:
            # 기존 저장된 픽이 있으면 그것만 체크, 없으면 False
            filtered_df['선택'] = filtered_df['번호'].isin(st.session_state.get('my_saved_picks', []))
        # --- 전체 번호 선택 로직 끝 ---
            
        # 4. 테이블 출력 세팅
        st.subheader("📊 전략 분석 테이블")
        st.info("🔵 **파란색**: 역사적 확률에 따른 **멸 확정** 구간 / 🟡 **노란색**: 멸 확률 40% 초과 **주의** 구간")
        
        # 4. 체크박스가 포함된 대화형 테이블 (st.data_editor 활용)
        # 컬럼 순서 및 편집 가능 여부 설정
        analysis_df['선택'] = False
        
        cols = ['선택', '번호', '통합크레이지점수', '출현수', '출현율', '현재연속', '최대연속', '반등지수', '에너지지수', '탄성점수', '리듬점수', '박자상태']
        available_cols = [c for c in cols if c in filtered_df.columns]
        
        edited_df = st.data_editor(
            apply_strategy_style(filtered_df[available_cols], decision),
            hide_index=True,
            use_container_width=True,
            column_config={
                "선택": st.column_config.CheckboxColumn(required=True),
                "번호": st.column_config.NumberColumn(format="%d"),
                "통합크레이지점수": st.column_config.NumberColumn(format="%.1f")
            },
            disabled=[c for c in available_cols if c != '선택'] # 선택 컬럼만 수정 가능
        )

        # 5. 선택된 번호로 조합 생성 섹션
        selected_numbers = edited_df[edited_df['선택'] == True]['번호'].tolist()
        
        # 6. 저장 버튼 및 데이터 업데이트
        st.divider()
        if st.button("💾 선택 번호 저장", use_container_width=True):
            # 체크된 번호들 추출 및 정수형 변환
            new_picks = [int(n) for n in edited_df[edited_df['선택'] == True]['번호'].tolist()]
            
            # 구글 시트에 저장
            #save_picks_to_sheets(conn, SHEET_URL, new_picks)
            save_to_sheets_by_type(conn, SHEET_URL, new_picks, "PICK")
            # 세션 상태 업데이트 (사이드바 즉시 반영)
            st.session_state.my_saved_picks = new_picks
            
            st.toast(f"🎯 {len(new_picks)}개 번호 저장 완료!")
            st.rerun()
        
        st.divider()
        st.subheader("🎲 실전 조합 생성기 (확장 필터)")
        
        if len(selected_numbers) >= 6:
            st.success(f"현재 선택된 번호 ({len(selected_numbers)}개): {sorted(selected_numbers)}")
            
            col_input1, col_input2 = st.columns(2)
            with col_input1:
                # 고정수 입력 UI
                fixed_nums = st.multiselect(
                    "📌 고정수 (FIX)", 
                    options=range(1, 46), 
                    default=st.session_state.get('fixed_nums', []),
                    key="fixed_multiselect" # 키 추가
                )

                if st.button("💾 고정수 시트 갱신", key="btn_fix_save"):
                    # 현재 선택된 fixed_nums를 시트에 덮어쓰기
                    save_to_sheets_by_type(conn, SHEET_URL, fixed_nums, "FIX")
                    # 세션 상태 업데이트 및 리런
                    st.session_state.fixed_nums = fixed_nums
                    st.rerun()
                    
            with col_input2:
                # 제외수 입력 UI
                exclude_nums = st.multiselect(
                    "🚫 제외수 (EX)", 
                    options=range(1, 46), 
                    default=st.session_state.get('exclude_nums', []),
                    key="exclude_multiselect" # 키 추가
                )
                
                if st.button("💾 제외수 시트 갱신", key="btn_ex_save"):
                    #현재 선택된 exclude_nums를 시트에 덮어쓰기
                    save_to_sheets_by_type(conn, SHEET_URL, exclude_nums, "EX")
                    
                    # 세션 상태 업데이트 및 리런
                    st.session_state.exclude_nums = exclude_nums
                    st.rerun()
                    
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.write("**추가 필터 1: 홀짝 비율**")
                ratio_options = ["0:6", "1:5", "2:4", "3:3", "4:2", "5:1", "6:0"]
                sel_oe = st.multiselect(
                    "허용 비율", 
                    options=ratio_options, 
                    default=st.session_state.get('sel_oe', ["3:3", "2:4"]), 
                    key='oe_input'
                )
            with col_f2:
                st.write("**추가 필터 2: 총합 범위**")
                sum_range = st.slider(
                    "총합 범위 설정", 
                    min_value=80, 
                    max_value=200, 
                    value=st.session_state.get('sum_range', (100, 170)), # 세션값이 있으면 사용, 없으면 기본값
                    step=1,
                    key='sum_input'
                )
                            
            # --- 실전 필터 적용 섹션 ---
            st.divider()
            with st.expander("🚀 필터링 조건 설정 (생성 시 적용)", expanded=True):
                row1_col1, row1_col2 = st.columns(2)
                with row1_col1:
                    sel_ac = st.number_input(
                        "최소 AC값", 
                        min_value=0, 
                        max_value=10, 
                        value=st.session_state.get('sel_ac', 7) # 로드된 값 사용
                    )
                with row1_col2:
                    sel_hl = st.multiselect(
                        "허용 고저비율", 
                        ["3:3", "2:4", "4:2", "1:5", "5:1", "0:6", "6:0"], # 0:6, 6:0 추가
                        default=st.session_state.get('sel_hl', ["3:3", "2:4", "4:2"]) # 로드된 값 사용
                        )
                row1_col1, row1_col2, row2_col3 = st.columns(3)    
                with row1_col1:
                    # index를 세션값에 맞춰 계산
                    con_options = [0, 1, 2]
                    saved_con = st.session_state.get('sel_con', 1)
                    # 만약 저장된 값이 옵션 리스트에 없으면 기본값 1번 인덱스 사용
                    con_index = con_options.index(saved_con) if saved_con in con_options else 1
                    
                    sel_con = st.selectbox("최대 연번허용", con_options, index=con_index)
                with row1_col2:
                    # [신규 추가] 동끝수 쌍 설정
                    # 보통 1~2쌍이 가장 많이 나오므로 기본값을 [1, 2]로 추천
                    pair_options = [0, 1, 2, 3]
                    saved_end = st.session_state.get('sel_end', [1, 2]) # 리스트 형태로 저장/로드
                    
                    sel_end = st.multiselect(
                        "허용 동끝수 쌍",
                        pair_options,
                        default=saved_end,
                        help="한 조합 내에 끝자리가 같은 숫자가 몇 쌍 있는지 설정합니다. (예: 12, 22는 1쌍)"
                    )
                with row2_col3:
                    # 2. [신규] 특정 동끝수 지정 (선택사항)
                    # 예: 7을 선택하면 (7, 17, 27, 37) 중 2개 이상이 포함된 조합을 우선시함
                    digit_options = list(range(10)) # 0~9까지
                    saved_target_end = st.session_state.get('sel_target_end', []) 
                    sel_target_end = st.multiselect(
                        "강제 지정 끝수 (선택)", 
                        digit_options, 
                        default=saved_target_end,
                        help="특정 끝수가 반드시 동끝수로 나오길 원할 때 선택하세요."
                    )
                        
            if st.button("📌 필터 설정값 저장"):
                with st.spinner("모든 필터 설정을 저장 중..."):
                    # 각 필터값을 리스트 형태로 변환하여 저장 함수 호출
                    save_to_sheets_by_type(conn, SHEET_URL, sel_oe, 'F_OE')
                    save_to_sheets_by_type(conn, SHEET_URL, [sel_ac], 'F_AC')
                    save_to_sheets_by_type(conn, SHEET_URL, [sel_con], 'F_CON')
                    save_to_sheets_by_type(conn, SHEET_URL, sel_hl, 'F_HL') # 리스트 그대로 전달
                    save_to_sheets_by_type(conn, SHEET_URL, [sum_range[0], sum_range[1]], 'F_SUM')
                    save_to_sheets_by_type(conn, SHEET_URL, sel_end, 'F_END') # 동끝수 필터값 저장
                    save_to_sheets_by_type(conn, SHEET_URL, sel_target_end, 'F_TARGET_END')
                    
                    # 고정수와 제외수도 함께 저장 (선택 사항)
                    #save_to_sheets_by_type(conn, SHEET_URL, fixed_nums, 'FIX')
                    #save_to_sheets_by_type(conn, SHEET_URL, exclude_nums, 'EX')
        
                    st.success("🎉 모든 분석 전략이 SavedPicks 시트에 통합 저장되었습니다!")
            # 1. 세션 상태 초기화 (코드 상단에 위치)
            if 'reco_results' not in st.session_state:
                st.session_state.reco_results = None
                
            if st.button("🚀 필터 적용 조합 추출", use_container_width=True):
                # 여기서 itertools.combinations 등을 활용해 필터를 통과한 조합만 출력
                # 이후 AC값, 동끝수 필터 등을 여기에 추가할 수 있음
                st.info("선택된 번호들로 필터를 만족하는 최적의 조합을 생성합니다.")
                            
                # 체크된 번호들의 로우데이터만 전달
                selected_df = edited_df[edited_df['선택'] == True]
                # 고정수가 6개 초과면 에러 처리
                if len(fixed_nums) > 6:
                    st.error("고정수는 최대 6개까지만 입력 가능합니다.")
                else:
                    with st.spinner('최적의 조합을 계산 중...'):
                        results = generate_strategic_combinations(
                            selected_df, 
                            ratio_filters = sel_oe, # UI 입력값 (멀티셀렉트)
                            sum_range = sum_range,      # UI 입력값 
                            skip_weights_df = st.session_state.get('skip_weight_df'), #사용자가 설정한 주기별 가중치 표 전달
                            fixed_nums = st.session_state.fixed_nums,  # UI 입력값
                            exclude_nums = st.session_state.exclude_nums,  # UI 입력값
                            min_ac=sel_ac,     # UI 입력값
                            allowed_hl=sel_hl, # UI 입력값 (멀티셀렉트)
                            max_con=sel_con,   # UI 입력값 (셀렉트박스)
                            count=5
                        )
                        
                        # [확인용] 41번 주기가 0인지 로그 출력 (나중에 삭제 가능)
                        st.write(f"DEBUG: 41번 현재 주기 -> {st.session_state.skip_dict.get(41)}")
                        
                        # [핵심] 결과를 세션 상태에 저장하여 화면에 고정
                        st.session_state.reco_results = results
                    if not st.session_state.reco_results:
                        st.warning("⚠️ 필터 조건을 만족하는 조합을 찾지 못했습니다. 범위를 넓혀주세요.")            
                    else:   st.balloons()
            # 2. 버튼 외부에서 결과를 출력 (결과가 있을 때만 실행)
            if st.session_state.reco_results:            
                    #if results:
                st.divider()
                st.subheader("✨ AI 추천 조합 (2-3-1 비율 적용)")
                # 🎨 범례(Legend) 표시 - 사용자가 색상의 의미를 알 수 있도록
                st.info("🎨 **번호 색상 범례**: ⬜ 이월수 (직전당첨) / 🟥 핫 (출현임박) / 🟨 웜 (일반) / 🟦 콜드 (장기미출)")
                st.success(f"✅ 고정수 {fixed_nums} 포함, 제외수 {exclude_nums} 제거 완료!")
                        
                # 폼을 사용하지 않고 개별 체크박스 상태를 추적하기 위해 리스트 생성
                to_save_picks = []
                        
                for i, combo_data in enumerate(st.session_state.reco_results):
                    combo_nums = sorted([n for n, group in combo_data])
                    col_chk, col_label, col_balls = st.columns([0.1, 0.15, 0.75])
                    # 1. 체크박스: 고유한 key를 부여하여 상태 유지
                    with col_chk:
                        if st.checkbox("", key=f"chk_reco_{i}"):
                            to_save_picks.append(combo_nums)
                            
                    with col_label:
                        st.markdown(f"**SET {i+1}**")
                                
                    # 번호별 색상 배지 (로또 공 색상 느낌)
                    with col_balls:
                        ball_html = ""
                        for n, group in combo_data:
                            # 🖍️ 그룹별 색상 매핑
                            if group == '이월수':
                                color = "white"      # ⬜ 이월수 (흰색 배경 + 검정 글자)
                            elif group == 'HOT':
                                color = "red"        # 🟥 핫 (빨간색)
                            elif group == 'WARM':
                                color = "yellow"     # 🟨 웜 (노란색/골드)
                            elif group == 'COLD':
                                color = "blue"       # 🟦 콜드 (파란색)
                            else:
                                color = "lightgrey"  # 데이터 오류 시 회색
                                
                            ball_html += f"![{n}](https://img.shields.io/badge/-{n}-{color}?style=flat-square&border_radius=50) "
                        st.markdown(ball_html, unsafe_allow_html=True)
                        
                st.divider()

                # 3. 저장 버튼: 'COMBI' 유형으로 저장
                if st.button("💾 선택한 조합 My Lucky Picks에 저장 (유형: COMBI)", use_container_width=True):
                    if not to_save_picks:
                        st.warning("저장할 조합을 먼저 체크해주세요!")
                    else:
                        with st.spinner('구글 시트에 저장 중...'):
                            # 기존 저장 함수 호출 (유형을 COMBI로 지정)
                            for pick in to_save_picks:
                                save_to_sheets_by_type(conn, SHEET_URL, pick, 'COMBI')
                                    
                            st.success(f"✅ {len(to_save_picks)}개의 조합이 COMBI 유형으로 저장되었습니다!")
                            # 저장 후 결과 화면을 지우고 싶다면 아래 주석 해제
                            st.session_state.reco_results = None
                            # 사이드바 즉시 갱신을 위해 앱 재실행
                            st.rerun()
                                    
                st.caption("※ 체크박스를 선택하고 저장 버튼을 누르면 사이드바에 즉시 반영됩니다.")
                    
        else:
            st.warning("조합을 만들려면 최소 6개 이상의 번호를 위 테이블에서 체크해 주세요.")

        # 5. 하단 요약 리포트
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.error(f"🚫 **완전 제외 구간**: {', '.join(excluded_zones) if excluded_zones else '없음'}")
        with col2:
            warning_zones = [z for z, d in decision.items() if not d['is_empty'] and d['prob'] > 40]
            st.warning(f"⚠️ **멸 주의 구간**: {', '.join(warning_zones) if warning_zones else '없음'}")
        
        st.divider()
        st.subheader("📊 정밀 통계 리포트 (수학적 확률 대조)")
        
        ratio_df, sum_df = get_advanced_stat_analysis(df)
        
        # 컬럼 설정 (편차 강조를 위한 스타일링은 간단히 텍스트로 처리)
        st.write("### ⚖️ 홀짝 비율 정밀 분석")
        st.dataframe(
            ratio_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "실제%": st.column_config.NumberColumn("실제 출현 비중", format="%.1f%%"),
                "이론%": st.column_config.NumberColumn("이론 확률", format="%.1f%%"),
                "편차": st.column_config.NumberColumn("편차", format="%+.1f%%") # 부호(+/-) 표시
            }
        )
        
        st.write("### 🔢 총합 구간 정밀 분석")
        st.dataframe(
            sum_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "실제%": st.column_config.NumberColumn("실제 출현 비중", format="%.1f%%"),
                "이론%": st.column_config.NumberColumn("이론 확률", format="%.1f%%"),
                "편차": st.column_config.NumberColumn("편차", format="%+.1f%%") # 부호(+/-) 표시
            }
        )
        
        # 실전 베팅 가이드
        with st.expander("💡 통계 수치 해석 가이드"):
            st.markdown("""
            * **편차가 (+)인 경우:** 해당 구간이 최근 유독 많이 나왔습니다. 조만간 출현 빈도가 줄어들 가능성(회귀)이 있습니다.
            * **편차가 (-)인 경우:** 이론상 더 나와야 하는데 최근 뜸한 구간입니다. **'반등 포인트'**로 잡고 조합에 포함하는 것을 추천합니다.
            * **황금 구간:** 홀짝 **3:3 / 2:4 / 4:2** 및 총합 **100~160** 사이가 전체 당첨의 약 80%를 차지합니다.
            """)

        st.divider()
        st.subheader("🛡️ v2.5 고급 품질 분석 리포트")
        
        ac_df, hl_df, con_df = get_comprehensive_analysis(df)
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.write("**📐 AC값 분포 (복잡도)**")
            st.dataframe(ac_df, use_container_width=True, hide_index=True)
            st.caption("7 미만은 규칙적 조합으로 제외 권장")
        
        with col_b:
            st.write("**🌓 고저 비율**")    # L:1~22, H:23~45
            hl_df.columns = ["비율(L:H)", "출현"]
            st.dataframe(hl_df, use_container_width=True, hide_index=True)
            st.caption("3:3 비율이 가장 이상적")
        
        with col_c:
            st.write("**🔗 연번 출현 빈도**")
            st.dataframe(con_df, use_container_width=True, hide_index=True)
            st.caption("보통 0~1쌍이 전체의 80%")

elif menu == "당첨번호 주기 분석":
    
    st.subheader("📊 회차별 당첨번호 주기 분석")
    
    if not df_raw.empty:
        results_df, skip_stats = analyze_winning_skip_distribution(df_raw, analyze_range)
        
        # 통계와 별개로, 현재 1~45번이 '지금' 몇 주기에 있는지 크레이지 로직으로 계산합니다.
        df_crazy = get_crazy_analysis(df_raw) # 크레이지 엔진 호출
        
        # 1~45번 전체의 실시간 현재스킵을 딕셔너리로 저장 (41번: 0)
        st.session_state.skip_dict = dict(zip(df_crazy['번호'], df_crazy['현재스킵']))
        
        # 그래프 표시
        fig = px.bar(skip_stats, x='구간', y='확률', 
                     title=f"최근 {analyze_range}회차 당첨번호 출현 주기 분포",
                     labels={'구간': '스킵 주기 구간', '확률': '평균 당첨 비중'},
                     text='확률')
        # 텍스트 포맷을 소수점 1자리 혹은 퍼센트로 보기 좋게 변경 (선택사항)
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        st.plotly_chart(fig)
        
        final_weight_table = render_skip_group_weight_ui(skip_stats)
        if final_weight_table is not None:
            st.session_state['skip_weight_df'] = final_weight_table
    
    else:
        st.error("데이터가 없습니다.")

elif menu == "동끝수 상세 분석":
    # 세션에 저장된 로또 히스토리와 입력 회차 범위를 전달
    render_target_end_analysis(df_raw, analyze_range)

st.sidebar.divider()
st.sidebar.caption("v0.1 - 통계 분석 시스템")
