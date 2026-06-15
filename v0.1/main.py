import streamlit as st
import pandas as pd
import plotly.express as px

from coldNum import get_cold_analysis
from savepicked import display_sidebar_picks, get_highlight_style, init_all_saved_data, save_to_sheets_by_type, save_recommended_picks
from specialNum import analyze_specific_number
from streamlit_gsheets import GSheetsConnection
from into_lottoDB import save_to_gsheet, get_recent_data, analyze_combination, data_input_func
from crazyLogic import get_crazy_analysis
from formular_description import display_formula_guide
import analysis_to_gsheet as saver
from iteration_predictor import render_carryover_analysis
from empty_zone_engine import display_lotto_empty_zone_matrix
from combination_engine import generate_strategic_combinations, get_advanced_stat_analysis, get_comprehensive_analysis, display_filter_setting, disp_recommended_nums_table, display_stat_report, combination_by_filter
from winning_skip_analysis import analyze_winning_skip_distribution, render_skip_group_weight_ui
from target_end_analysis import render_target_end_analysis
from comprehensive_analysis import render_comprehensive_analysis
from funatsu_sakai import render_sakai_analysis 

st.set_page_config(page_title="로또 분석 프로 v0.1", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1q8P3SClxNSYsAXwBgk3__y44XxZwI_FTj-eE9uQeVHE/edit?gid=0#gid=0"

# 앱이 처음 켜질 때 강제 리로드 플래그를 False로 방 만들기
if 'menu_changed_reload' not in st.session_state:
    st.session_state.menu_changed_reload = False
    st.cache_data.clear()  # 👈 브라우저 새로고침(F5) 시에만 작동!

# 1. 초기화 및 사이드바 표시 (최상단)
init_all_saved_data(conn, SHEET_URL, force_reload=st.session_state.menu_changed_reload)

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

# 메뉴가 바뀌었으므로 다음 화면 갱신 때 시트를 강제로 읽으라고 신호를 줌
def trigger_reload():
    st.session_state.menu_changed_reload = True

with st.sidebar:
    menu = st.sidebar.radio("기능 선택", ["데이터 입력", "크레이지 번호 추출", "콜드 번호 추출", "특정 번호 분석", "📊 이월수 예측", "🎯 추천번호 분석", "당첨번호 주기 분석", "동끝수 상세 분석", "종합 분석", "후나츠 사카이 분류"], on_change=trigger_reload)
    display_sidebar_picks(conn, SHEET_URL) # 👈 어떤 메뉴에서든 내 번호가 보임

if menu == "데이터 입력":
    try:
        st.title("🎰 로또 데이터 입력 및 조합 분석")
        data_input_func(conn, SHEET_URL, df, analyze_range)
    except Exception as e:
        # 에러가 나면 화면에 에러 서류를 길게 출력해서 붙잡아둠
        st.exception(e)
        
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
    st.title("🎯 v2.5 전략 추천번호")
    
    if not df.empty:
        '''
        decision = get_confirmed_empty_zone(df, analyze_range)
        
        # 멸구간 확정 브리핑
        st.subheader("🛡️ 멸구간 확정 리포트")
        for zone, data in decision.items():
            if data['is_empty']:
                st.error(f"🚫 **{zone} 제외 확정** : {data['reason']}")
            elif data['prob'] > 40:
                st.warning(f"⚠️ **{zone} 주의** : 멸 확률 {data['prob']:.1f}% (관찰 필요)")
        
        # 확정된 멸구간 번호 제외
        excluded_zones = [z for z, d in decision.items() if d['is_empty']]
        '''
        selected_numbers, edited_df = disp_recommended_nums_table(conn, SHEET_URL, df)
        
        st.divider()
        st.subheader("🎲 실전 조합 생성기 (확장 필터)")
        
        if len(selected_numbers) >= 6:  #선택된 번호가 6개이상일 때만 조합 가능
            st.success(f"현재 선택된 번호 ({len(selected_numbers)}개): {sorted(selected_numbers)}")
            display_filter_setting(conn, SHEET_URL) #적용할 필터들을 표시 및 설정
            combination_by_filter(conn, SHEET_URL, df, edited_df)    #필터 적용 조합 추출
        else:
            st.warning("조합을 만들려면 최소 6개 이상의 번호를 위 테이블에서 체크해 주세요.")
    
        # 5. 하단 요약 리포트
        display_lotto_empty_zone_matrix(df)
        
        '''
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.error(f"🚫 **완전 제외 구간**: {', '.join(excluded_zones) if excluded_zones else '없음'}")
        with col2:
            warning_zones = [z for z, d in decision.items() if not d['is_empty'] and d['prob'] > 40]
            st.warning(f"⚠️ **멸 주의 구간**: {', '.join(warning_zones) if warning_zones else '없음'}")
        '''
        
        st.divider()
        display_stat_report(df)

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
    
elif menu == "종합 분석":
    render_comprehensive_analysis(df_raw, analyze_range)

elif menu == "후나츠 사카이 분류":
    render_sakai_analysis(df_raw, analyze_range)
    
st.sidebar.divider()
st.sidebar.caption("v0.1 - 통계 분석 시스템")
