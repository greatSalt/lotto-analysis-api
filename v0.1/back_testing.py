import streamlit as st

def bt_main_func():
    selection_menu = bt_sel_func()
    
    if selection_menu == "이월수 예측":
        st.subheader("🧪 이월수 예측 백테스팅")
        # run_carryover_backtest() 호출
        pass
    elif selection_menu == "멸구간 예측":
        st.subheader("🧪 멸구간 예측 백테스팅")
        # run_empty_zone_backtest() 호출
        pass
    
def bt_sel_func():
    col1, _ = st.columns(2)
    with col1: 
        func_options = ["선택 안 함", "이월수 예측",  "멸구간 예측"]
        if 'f_opt' not in st.session_state or st.session_state.f_opt not in func_options:
            st.session_state.f_opt = ["선택 안 함"]
        
        st.selectbox(
            "Back Testing",    
            options=func_options,
            index=func_options.index(st.session_state.f_opt), # 현재 저장된 값의 인덱스 지정
            key='func_opt_widget'
        )
                    
    st.divider()
    
    return st.session_state.f_opt