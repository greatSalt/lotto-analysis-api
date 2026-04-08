import streamlit as st
import pandas as pd

import coldNum
from savepicked import display_sidebar_picks, get_highlight_style, init_all_saved_data, save_to_sheets_by_type
from specialNum import analyze_specific_number
from streamlit_gsheets import GSheetsConnection
from into_lottoDB import save_to_gsheet, get_recent_data
from crazyLogic import get_crazy_analysis
from formular_description import display_formula_guide
import analysis_to_gsheet as saver
from iteration_predictor import predict_iteration_count, predict_with_numbers
from empty_zone_engine import get_confirmed_empty_zone, color_rows, apply_strategy_style
from combination_engine import generate_strategic_combinations, get_advanced_stat_analysis, get_comprehensive_analysis

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
    min_value=10, 
    max_value=300, 
    value=30, 
    step=5
)

# 모든 메뉴에서 사용할 공통 분석 데이터 (슬라이싱)
df = df_raw.head(analyze_range).copy()

with st.sidebar:
    menu = st.sidebar.radio("기능 선택", ["데이터 입력", "크레이지 번호 추출", "콜드 번호 추출", "특정 번호 분석", "📊 이월수 예측", "🎯 추천번호 분석"])
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
            # ------------------

            st.divider()
            
            # --- [5] 공식 및 수치 해석 섹션 (최종 통합본) ---
            display_formula_guide(analyze_range)
            
elif menu == "특정 번호 분석":
    st.title("🔍 번호 심층 분석")
    
    # 입력 UI: 번호와 분석 범위를 나란히 배치
    col1 = st.columns([1, 2]) # 입력창 크기 조절
    with col1:
        target_num = st.number_input("분석할 번호", 1, 45, 1)
    '''with col2:
        # 분석 범위 입력 추가 (기본 100회차, 최대 500회차까지 확장 가능)
        deep_analyze_count = st.number_input("심층 분석 범위(최근 회차)", 10, 500, 30)'''
    
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
        if "cold_edited_df" not in st.session_state:
            cold_df = coldNum.get_cold_analysis(df)
            display_cold = cold_df.sort_values("현재미출현", ascending=False).head(15).copy()
            # 구글 시트에서 기존 저장된 번호들 가져오기 (저장된 번호 로드)
            try:
                # SavedPicks 워크시트에서 번호 컬럼 추출
                saved_df = conn.read(spreadsheet=SHEET_URL, worksheet="SavedPicks")
                saved_picks = saved_df["번호"].tolist()
            except:
                saved_picks = []
        
            # 2. 인덱스를 1부터 15까지 새로 부여 (No. 표시용)
            display_cold.index = range(1, len(display_cold) + 1)
            display_cold = display_cold.reset_index().rename(columns={"index": "No."})
        
            # [핵심] 시트에 저장된 번호라면 '선택'을 True로 설정
            display_cold.insert(0, "선택", display_cold["번호"].apply(lambda x: x in saved_picks))
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
        st.session_state.cold_edited_df = edited_output
        
        # 4. 저장 버튼 및 구글 시트 연동
        if st.button("📌 선택한 콜드번호 저장 및 공유", use_container_width=True):
            # 현재 에디터 상태에서 선택된 번호 추출
            current_df = st.session_state.cold_edited_df
            # 체크된 번호들만 리스트로 추출
            selected_nums = current_df[current_df['선택'] == True]['번호'].tolist()
            
            if not selected_nums:
                st.warning("공유할 번호를 먼저 선택해주세요.")
            else:
                # [기존 함수 활용] 구글 시트에 선택된 번호 업데이트
                # 예: update_google_sheet(selected_nums, "COLD_STRATEGY")
                #save_picks_to_sheets(conn, SHEET_URL, selected_nums)
                save_to_sheets_by_type(conn, SHEET_URL, selected_nums, "PICK")
                # 저장 후 세션 데이터를 최신화하기 위해 세션 삭제 후 재실행 (시트 데이터 다시 읽기 위함)
                del st.session_state.cold_edited_df  
                st.rerun() # 사이드바 갱신을 위해 앱 재실행
        st.info("💡 체크된 번호는 이미 'My Lucky Picks'에 저장된 번호입니다.")
        st.info("💡 '현재미출현' 수치가 높을수록 오랫동안 나오지 않은 '차갑게 식은' 번호들입니다.")
    else:
        st.error("데이터를 불러올 수 없습니다.")

elif menu == "📊 이월수 예측":
    st.title("🔮이월수 전략 시뮬레이터")
    
    # 분석 데이터 호출
    #analyze_count = st.number_input("분석 범위(최근 회차)", 10, 100, 30)
    if st.button("📊 이월수 기대치 예측 실행"):
        #df = get_recent_data(conn, SHEET_URL, count=analyze_count)
        
        if not df.empty:
            analysis_df = get_crazy_analysis(df)
            
            if not analysis_df.empty:
                # 최신 회차(1행)에서 당첨번호 6개 추출
                # df의 컬럼명이 'num1', 'num2'... 식이라고 가정할 때:
                last_win_row = df.iloc[0]
                last_nums = [last_win_row['n1'], last_win_row['n2'], last_win_row['n3'], 
                             last_win_row['n4'], last_win_row['n5'], last_win_row['n6']]
                
                # 분석 데이터(analysis_df)에서 해당 6개 번호의 행만 필터링하여 기세(streak) 정보 확보
                current_nums_info = analysis_df[analysis_df['번호'].isin(last_nums)].copy()
#------------------------------------------------------------------------------------------------
                # [트랩 1] 최근 추세 기반 예측 (Moving Average)
                count1, reason1 = predict_iteration_count(df, current_nums_info)

                next_round = int(last_win_row['round']) + 1 if 'round' in last_win_row else "다음"
                st.subheader(f"📊 Trap 1: {next_round}회차 추세 분석 (Momentum)")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric(label="예측 개수", value=f"{count1}개")
                with col2:
                    st.info(f"**추세 근거:** {reason1}")
                    
                st.divider()    
#------------------------------------------------------------------------------------------------                    
                # [트랩 2] 과거 사례 확률 기반 예측 (Probability Matrix)
                count2, reason2, recommended_df = predict_with_numbers(df, current_nums_info)
                
                #next_round = int(last_win_row['round']) + 1 if 'round' in last_win_row else "다음"
                st.subheader(f"🎯 Trap 2: {next_round}회차 확률 기반 추천 (예측 {count2}개)")
                st.write(f"**확률 근거:** {reason2}")

                # 추천 번호 표시 (0개일 경우 대비)
                if not recommended_df.empty:
                    cols = st.columns(len(recommended_df))
                    for i, (idx, row) in enumerate(recommended_df.iterrows()):
                        with cols[i]:
                            st.markdown(f"""
                            <div style="text-align: center; padding: 10px; border: 2px solid #ff4b4b; border-radius: 10px; background-color: #f9f9f9;">
                                <h2 style="margin: 0; color: #333;">{int(row['번호'])}</h2>
                                <p style="font-size: 0.8em; color: #666; margin-bottom: 5px;">이월 확률</p>
                                <h3 style="color: #ff4b4b; margin: 0;">{row['이월확률']:.1f}%</h3>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ 이번 회차는 이월수가 발생하지 않을 확률이 높습니다.")
                        
                st.caption("※ Trap 2는 v2.3 엔진의 기세/반등/체급 지표를 결합한 개별 번호의 재출현 기대치입니다.")
#------------------------------------------------------------------------------------------------

                
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
        #for zone in excluded_zones:
            #start, end = zones_map[zone]
            #filtered_df = filtered_df[~filtered_df['번호'].between(start, end)]
        if '선택' not in filtered_df.columns:
            filtered_df.insert(0, '선택', filtered_df['번호'].isin(st.session_state.my_saved_picks))
            
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
                ratio_filter = st.multiselect("허용 비율", ["3:3", "2:4", "4:2"], default=["3:3", "2:4"])
            with col_f2:
                st.write("**추가 필터 2: 총합 범위**")
                sum_range = st.slider("총합 범위 설정", 100, 200, (110, 160))

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
                        results = generate_strategic_combinations(selected_df, ratio_filter, sum_range, fixed_nums, exclude_nums)
                    
                    if results:
                        st.divider()
                        st.balloons()
                        st.subheader("✨ AI 추천 조합 (2-3-1 비율 적용)")
                        # 🎨 범례(Legend) 표시 - 사용자가 색상의 의미를 알 수 있도록
                        st.info("🎨 **번호 색상 범례**: 🟥 핫 (상위 30%) / 🟨 웜 (중간 40%) / 🟦 콜드 (하위 30%)")
                        st.success(f"✅ 고정수 {fixed_nums} 포함, 제외수 {exclude_nums} 제거 완료!")
                        
                        for i, combo in enumerate(results):
                            c1, c2 = st.columns([1, 5])
                            c1.markdown(f"**SET {i+1}**")
                            # 번호별 색상 배지 (로또 공 색상 느낌)
                            ball_html = ""
                            for n, group in combo:
                                # 🖍️ 그룹별 색상 매핑
                                if group == 'HOT':
                                    color = "red"        # 🟥 핫 (빨간색)
                                elif group == 'WARM':
                                    color = "yellow"     # 🟨 웜 (노란색/골드)
                                else:
                                    color = "blue"       # 🟦 콜드 (파란색)
                                ball_html += f"![{n}](https://img.shields.io/badge/-{n}-{color}?style=flat-square&border_radius=50) "
                            c2.markdown(ball_html, unsafe_allow_html=True)
                            
                        st.caption("※ 핫(상위점수 2개), 웜(중간점수 3개), 콜드(하위점수 1개) 비율로 생성되었습니다.")
                    else:
                        st.warning("⚠️ 필터 조건을 만족하는 조합을 찾지 못했습니다. 범위를 넓혀주세요.")
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
            st.write("**🌓 고저 비율 (1~22 : 23~45)**")
            st.dataframe(hl_df, use_container_width=True, hide_index=True)
            st.caption("3:3 비율이 가장 이상적")
        
        with col_c:
            st.write("**🔗 연번 출현 빈도**")
            st.dataframe(con_df, use_container_width=True, hide_index=True)
            st.caption("보통 0~1쌍이 전체의 80%")


st.sidebar.divider()
st.sidebar.caption("v0.1 - 통계 분석 시스템")
