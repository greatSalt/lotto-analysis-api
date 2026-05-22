import pandas as pd
import streamlit as st

def render_sakai_analysis(df_raw):
    st.header("📊 회차별 종합 상세 분석")
    
    analysis_data = []
    
    latest_row = df_raw.iloc[0]
    
    next_round = int(latest_row['round']) + 1
    last_winning_numbers = [int(latest_row[f'n{i}']) for i in range(1,7)]
    last_bonus_number = int(latest_row['bonus'])
    
    magic_pool = make_funatsu_sakai_pool(last_winning_numbers, last_bonus_number)
    
    analysis_data.append({
        "예측 회차": f"<b>{next_round}</b>",
        "선별된 번호": ", ".join(map(str, magic_pool))
    })
    
    final_df = pd.DataFrame(analysis_data)
    
    # 1. 표에 적용할 CSS 스타일 정의
    table_style = """
    <style>
        table {
            width: 100%;
            border-collapse: collapse; /* 선이 중복되어 두꺼워지는 것 방지 */
        }
        th {
            text-align: center !important; /* 제목 컬럼 무조건 중앙 정렬 */
            background-color: #f1f3f5;
            border: 1px solid #ced4da !important;
            padding: 8px;
        }
        td {
            text-align: center; /* 내용도 중앙 정렬 */
            border: 1px solid #ced4da !important;
            padding: 8px;
        }
    </style>
    """
    
    # 2. 스타일과 HTML 표를 합쳐서 출력
    html_content = table_style + final_df.to_html(escape=False, index=False)
    st.markdown(html_content, unsafe_allow_html=True)
    
def make_funatsu_sakai_pool(last_winning_numbers, last_bonus_number):
    
    # 처음부터 중복을 제거할 set 자료형으로 방을 팝니다.
    magic_pool = set()
    
    # 1단계: 당첨번호 6개를 순회하며 본수와 주변수(+1, -1) 추가
    for n in last_winning_numbers:
        # 본수, 이전수, 다음수를 하나의 후보 리스트로 묶음
        candidates = [n - 1, n, n + 1]
        
        cal = n%7
        if cal == 1:
            temp = [n+6, n+8]
        elif cal == 0:
            temp = [n-8, n-6]
        else:
            temp = [n-8, n-6, n+6, n+8]
        
        candidates.extend(temp)
        # 후보 번호들을 하나씩 꺼내서 검사 후 세트에 추가
        for c in candidates:
            if 1 <= c <= 45: # 로또 번호 범위(1~45)인 경우에만!
                magic_pool.add(c) # set에 추가 (중복은 알아서 제거됨)
                
    candidates = [last_bonus_number-1, last_bonus_number+1]
    for c in candidates:
        if 1 <= c <= 45: # 로또 번호 범위(1~45)인 경우에만!
                magic_pool.add(c) # set에 추가 (중복은 알아서 제거됨)
            
    # 나중에 정렬된 상태로 보기 편하게 리스트로 바꾸어 리턴합니다.
    return sorted(list(magic_pool))