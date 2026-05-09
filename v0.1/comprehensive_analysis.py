import streamlit as st
import pandas as pd

def get_number_status_dynamic(target_idx, df_raw, analyze_range):
    """
    사용자가 설정한 analyze_range를 기준으로 해당 회차 시점의 번호 성격 분류
    """
    # 해당 회차 직전부터 설정된 범위만큼 과거 데이터 슬라이싱
    past_df = df_raw.iloc[target_idx + 1 : target_idx + 1 + analyze_range]
    
    if past_df.empty:
        return set(), set(), set()

    # 1. 핫넘버: 설정된 범위(analyze_range) 내 출현한 번호
    all_nums = []
    for j in range(1, 7):
        all_nums.extend(past_df[f'n{j}'].tolist())
    hot_candidates = set(all_nums)
    
    # 2. 콜드넘버: 보통 핫넘버 기준의 2배 범위 혹은 전체 미출현 번호로 규정
    # 여기서는 설정 범위 내에 한 번도 안 나온 번호를 콜드로 정의 (분석 일관성 유지)
    all_possible = set(range(1, 46))
    cold_candidates = all_possible - hot_candidates
    
    # 3. 미들넘버: 핫/콜드 경계가 모호한 경우 (필요 시 로직 확장 가능)
    # 현재는 설정 범위 기준으로 이분법적 분류가 우선임
    middle_candidates = set() 
    
    return hot_candidates, middle_candidates, cold_candidates

def render_comprehensive_analysis(df_raw, analyze_range, display_count=20):
    st.header("📊 회차별 당첨번호 종합 분석")
    st.info(f"💡 현재 설정된 **{analyze_range}회차 분석 범위**를 기준으로 성격을 분류합니다.")

    analysis_data = []
    
    # 최근 회차부터 순회
    for i in range(display_count):
        if i >= len(df_raw): break
        
        row = df_raw.iloc[i]
        curr_nums = [int(row[f'n{j}']) for j in range(1, 7)]
        
        # --- 핵심: 메인 설정 범위를 사용하여 당시 성격 계산 ---
        hot_nums, _, cold_nums = get_number_status_dynamic(i, df_raw, analyze_range)
        
        # 이월수 계산 (직전 회차와 대조)
        carry_nums = []
        if i + 1 < len(df_raw):
            last_nums = [int(df_raw.iloc[i+1][f'n{j}']) for j in range(1, 7)]
            carry_nums = list(set(curr_nums) & set(last_nums))
        
        # 번호별 공 디자인 (HTML)
        balls_html = ""
        for n in curr_nums:
            bg = "#FF4B4B" if n in hot_nums else "#1E90FF"
            border = "2.5px solid #FFD700" if n in carry_nums else "1px solid #777777"
            
            # f-string 내부의 줄바꿈을 없애고 한 줄로 작성합니다.
            ball_style = f"background-color:{bg}; color:white; padding:2px 8px; margin:2px; border-radius:12px; border:{border}; font-weight:bold; display:inline-block; font-size:13px;"
            balls_html += f'<span style="{ball_style}">{n}</span>'
        
        analysis_data.append({
            "회차": f"<b>{int(row['round'])}회</b>",
            "당첨번호 분석": balls_html,
            "이월수": ", ".join(map(str, sorted(carry_nums))) if carry_nums else "-",
            "이월수갯수": len(carry_nums)
        })

    # 결과 테이블 렌더링
    final_df = pd.DataFrame(analysis_data)
    st.markdown(final_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th {
        background-color: #f0f2f6;
        text-align: center !important;
    }
    td {
        text-align: center !important;
        vertical-align: middle !important;
    }
    </style>
    """, unsafe_allow_html=True)
