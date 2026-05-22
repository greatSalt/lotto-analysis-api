import pandas as pd
import streamlit as st

def render_sakai_analysis(df_raw):
    st.header("📊 회차별 종합 상세 분석")
    
    analysis_data = []
    
    latest_row = df_raw.iloc[0]
    last_winning_numbers = [int(latest_row[f'n{i}']) for i in range(1,7)]
    last_bonus_number = int(latest_row['bonus'])
    
    magic_pool = make_funatsu_sakai_pool(last_winning_numbers, last_bonus_number)
    
    analysis_data.append({
        "회차": f"<b>{int(latest_row['round'])}</b>",
        "선별된 번호": ", ".join(map(str, magic_pool))
    })
    
    final_df = pd.DataFrame(analysis_data)
    st.markdown(final_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    
def make_funatsu_sakai_pool(last_winning_numbers, last_bonus_number):
    
    # 처음부터 중복을 제거할 set 자료형으로 방을 팝니다.
    magic_pool = set()
    
    # 1단계: 당첨번호 6개를 순회하며 본수와 주변수(+1, -1) 추가
    for n in last_winning_numbers:
        # 본수, 이전수, 다음수를 하나의 후보 리스트로 묶음
        candidates = [n - 1, n, n + 1]
        
        # 후보 번호들을 하나씩 꺼내서 검사 후 세트에 추가
        for c in candidates:
            if 1 <= c <= 45: # 로또 번호 범위(1~45)인 경우에만!
                magic_pool.add(c) # set에 추가 (중복은 알아서 제거됨)
                
    # 나중에 정렬된 상태로 보기 편하게 리스트로 바꾸어 리턴합니다.
    return sorted(list(magic_pool))