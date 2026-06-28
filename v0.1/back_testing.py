import streamlit as st
import pandas as pd

from comprehensive_analysis import get_detailed_status
from into_lottoDB import render_ball_ui

def bt_main_func(df_raw):
    selection_menu = bt_sel_func()
    
    if selection_menu == "이월수 예측":
        st.subheader("🧪 이월수 예측 백테스팅")
        # run_carryover_backtest() 호출
        pass
    elif selection_menu == "멸구간 예측":
        st.subheader("🧪 멸구간 예측 백테스팅")
        run_empty_zone_backtest(df_raw, count=25) 
        pass
    else:
        pass
    
def bt_sel_func():
    col1, _ = st.columns(2)
    with col1: 
        func_options = ["선택 안 함", "이월수 예측",  "멸구간 예측"]
        if 'f_opt' not in st.session_state or st.session_state.f_opt not in func_options:
            st.session_state.f_opt = "선택 안 함"
        
        st.selectbox(
            "Back Testing",    
            options=func_options,
            index=func_options.index(st.session_state.f_opt), # 현재 저장된 값의 인덱스 지정
            key='f_opt'
        )
                    
    st.divider()
    
    return st.session_state.f_opt
    
def run_empty_zone_backtest(df_raw, count=25):
    
    results = []
    if not df_raw.empty:
        target_rows = df_raw.head(count)
        for idx in range(len(target_rows)):
            row = target_rows.iloc[idx]
            round_num = row['round']
            picked_nums = [row[f'n{i}'] for i in range(1, 7)]
            status_map, _ = get_detailed_status(idx, target_rows)
            ball_html = render_ball_ui(picked_nums, status_map, size=45)

            results.append({
                "회차": row['round'],
                "당첨 번호 구성": ball_html, # 여기에 공 UI 삽입
            })
    
        df_result = pd.DataFrame(results)
        
         # Streamlit에서 HTML 표 출력 (unsafe_allow_html=True 필수)
        st.write(df_result.to_html(escape=False, index=False), unsafe_allow_html=True)