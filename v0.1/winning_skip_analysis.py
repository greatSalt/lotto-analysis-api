import pandas as pd
import plotly.express as px
import streamlit as st

#당첨번호 주기(Skip) 분석 및 시각화 로직
def analyze_winning_skip_distribution(history_df, target_rounds=10):
    """
    history_df: 전체 당첨 번호 데이터 (회차, 번호1~6 포함)
    target_rounds: 분석할 최근 회차 범위 (사용자 입력값)
    """
    skip_data = []
    
    # 최근 n회차의 당첨 번호들만 순회
    recent_rounds = history_df.head(target_rounds)
    
    for idx, row in recent_rounds.iterrows():
        round_num = row['round']
        winning_nums = [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]
        
        for num in winning_nums:
            # 해당 번호가 이 회차(idx) 이전에는 언제 나왔는지 찾기
            prev_appearances = history_df.iloc[idx+1:]
            last_idx = prev_appearances[(prev_appearances['n1'] == num) | 
                                        (prev_appearances['n2'] == num) | 
                                        (prev_appearances['n3'] == num) | 
                                        (prev_appearances['n4'] == num) | 
                                        (prev_appearances['n5'] == num) | 
                                        (prev_appearances['n6'] == num)].index
            
            if not last_idx.empty:
                skip_val = last_idx[0] - idx - 1 # 주기 계산
            else:
                skip_val = target_rounds+10 # 아주 오래된 미출현수
                
            skip_data.append({"회차": round_num, "번호": num, "주기": skip_val})
            
    analysis_results = pd.DataFrame(skip_data)
    
    # 주기별 출현 빈도 계산 (0, 1, 2, 3...)
    skip_counts = analysis_results['주기'].value_counts().sort_index().reset_index()
    skip_counts.columns = ['주기', '출현빈도']
    
    # 확률(가중치) 계산: 해당 주기의 빈도 / 전체 번호 수
    total_nums = len(analysis_results)
    skip_counts['확률'] = (skip_counts['출현빈도'] / total_nums).round(4)
    
    return analysis_results, skip_counts

def render_skip_group_weight_ui(skip_stats):
    """
    skip_stats: 개별 주기(0, 1, 2...)별 빈도가 담긴 데이터프레임
    """
    st.markdown("### ⚙️ 구간별 당첨 통계 및 가중치 설정")
    
    # 1. 사용자 정의 구간 설정
    bins = [-1, 0, 3, 6, 9, 14, 24, 100]
    labels = ["0주기", "1~3주기", "4~6주기", "7~9주기", "10~14주기", "15~24주기", "25주기 이상"]
    
    # 개별 주기 데이터를 구간별로 그룹화
    skip_stats['구간'] = pd.cut(skip_stats['주기'], bins=bins, labels=labels)
    group_stats = skip_stats.groupby('구간', observed=True).agg({
        '출현빈도': 'sum'
    }).reset_index()
    
    # 2. 확률 계산 (전체 대비 해당 구간의 비중)
    total_hits = group_stats['출현빈도'].sum()
    group_stats['확률'] = (group_stats['출현빈도'] / total_hits).round(4)
    
    # [핵심] 확률의 10배를 기본 가중치로 설정
    group_stats['가중치'] = (group_stats['확률'] * 10).round(2)
    
    # 3. 세션 상태를 이용한 가중치 관리 (최초 1회 초기화)
    if 'skip_weight_df' not in st.session_state:
        # 초기 가중치는 모두 1.0으로 설정 (혹은 확률 기반으로 자동 계산 가능)
        group_stats['가중치'] = 1.0
        st.session_state.skip_weight_df = group_stats
    else:
        # 기존에 수정하던 값이 있다면 빈도와 확률만 최신화
        st.session_state.skip_weight_df['출현빈도'] = group_stats['출현빈도']
        st.session_state.skip_weight_df['확률'] = group_stats['확률']

    # 4. st.data_editor를 이용한 편집 가능한 표 출력
    st.info("💡 **가중치** 컬럼을 수정하여 조합 생성 시 비중을 조절하세요. (예: 1.5는 50% 강조)")
    
    edited_df = st.data_editor(
        st.session_state.skip_weight_df,
        column_config={
            "구간": st.column_config.TextColumn("스킵 주기 구간", disabled=True),
            "출현빈도": st.column_config.NumberColumn("당첨 빈도수", format="%d회", disabled=True),
            "확률": st.column_config.ProgressColumn("당첨 확률", format="%.2f", min_value=0, max_value=1),
            "가중치": st.column_config.NumberColumn(
                "가중치(확률x10)", 
                help="값이 클수록 해당 구간 번호가 더 많이 뽑힙니다.",
                min_value=0.0, max_value=5.0, step=0.1, format="%.1f"
            )
        },
        hide_index=True,
        use_container_width=True,
        key="skip_editor"
    )
    
    # 수정된 결과 저장
    st.session_state.skip_weight_df = edited_df
    return edited_df

# 사용 예시:
# skip_stats = analyze_winning_skip_distribution(...) 에서 나온 결과 전달
# final_weight_table = render_skip_group_weight_ui(skip_stats)
