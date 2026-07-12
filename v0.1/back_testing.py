import streamlit as st
import pandas as pd

from comprehensive_analysis import get_detailed_status
from into_lottoDB import render_ball_ui
from empty_zone_engine import get_empty_finder

def bt_main_func(df_raw):
    selection_menu = bt_sel_func()
    
    if selection_menu == "이월수 예측":
        st.subheader("🧪 이월수 예측 백테스팅")
        # run_carryover_backtest() 호출
        pass
    elif selection_menu == "멸구간 예측":
        st.subheader("🧪 멸구간 예측 백테스팅")
        run_empty_zone_backtest(df_raw, count=25) 
    elif selection_menu == "보너스 번호의 이월확률":
        run_bonus_carry_backtest()
    else:
        pass
    
def bt_sel_func():
    col1, _ = st.columns(2)
    with col1: 
        func_options = ["선택 안 함", "이월수 예측",  "멸구간 예측", "보너스 번호의 이월확률"]
        
        # 1. 세션 스테이트 초기화 (존재하지 않을 때만)
        if 'f_opt' not in st.session_state:
            st.session_state.f_opt = "선택 안 함"
        
        # 2. 안전한 인덱스 계산 (데이터 검증 포함)
        current_val = st.session_state.f_opt
        # 현재 값이 리스트에 없으면 기본값(0) 사용
        target_index = func_options.index(current_val) if current_val in func_options else 0
        
        # 3. 위젯 설정
        st.selectbox(
            "Back Testing",    
            options=func_options,
            index=target_index,
            key='f_opt'
        )
                    
    st.divider()
    return st.session_state.f_opt
    
def run_empty_zone_backtest(df_raw, count=25):
    
    # 멸구간 정의 및 컬럼 설정
    zones = {
        "단번대": lambda n: 1 <= n <= 9,
        "10번대": lambda n: 10 <= n <= 19,
        "20번대": lambda n: 20 <= n <= 29,
        "30번대": lambda n: 30 <= n <= 39,
        "40번대": lambda n: 40 <= n <= 45
    }
    #num_cols = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']
    
    results = []
    if not df_raw.empty:
        target_rows = df_raw.head(count).astype(int)
        for idx in range(len(target_rows)):
            row = target_rows.iloc[idx]
            round_num = row['round']
            picked_nums = [row[f'n{i}'] for i in range(1, 7)]
            emptyzones = get_empty_finder(picked_nums, zones)   # 멸구간 찾기
            status_map, _ = get_detailed_status(idx, df_raw)
            ball_html = render_ball_ui(picked_nums, status_map, size=20)

            results.append({
                "회차": row['round'],
                "당첨 번호 구성": ball_html, # 여기에 공 UI 삽입
                "멸구간": ", ".join(emptyzones) if emptyzones else "없음"
            })
    
        df_result = pd.DataFrame(results)
        
         # Streamlit에서 HTML 표 출력 (unsafe_allow_html=True 필수)
        st.write(df_result.to_html(escape=False, index=False), unsafe_allow_html=True)
        
def run_bonus_carry_backtest(df_raw, count=50):
    
    results = []
    if not df_raw.empty:
        target_rows = df_raw.head(count).astype(int)
        for idx in range(len(target_rows)):
            row = target_rows.iloc[idx]
            round_num = row['round']
            picked_nums = [row[f'n{i}'] for i in range(1, 7)]
            status_map, _ = get_detailed_status(idx, df_raw)
            ball_html = render_ball_ui(picked_nums, status_map, size=20)
            
            bonus_num = [row['bonus']]
            bonus_ball_html = render_ball_ui(bonus_num, status_map, size=20)
            
            # 이월 확인 로직
            carry_text = "-"
            if idx + 1 < len(df_raw):
                # target_rows 대신 전체 df_raw에서 참조하는 것이 안전
                pre_bonus_num = int(df_raw.iloc[idx + 1]['bonus']) #이전 회차의 보너스 번호
                is_carry = pre_bonus_num in picked_nums
                
                # 시각적 강조를 위한 HTML 적용
                if is_carry:
                    carry_text = '<span style="color:#FF4B4B; font-weight:bold;">✅ 이월</span>'
                else:
                    carry_text = '<span style="color:#CCCCCC;">❌ -</span>'
            
            results.append({
                "회차": row['round'],
                "당첨 번호 구성": ball_html, # 여기에 공 UI 삽입
                "보너스번호": bonus_ball_html,
                "보너스번호 이월": carry_text
            })
    
        df_result = pd.DataFrame(results)
        
         # Streamlit에서 HTML 표 출력 (unsafe_allow_html=True 필수)
        st.write(df_result.to_html(escape=False, index=False), unsafe_allow_html=True)
    