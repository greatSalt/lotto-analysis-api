def analyze_winning_skip_distribution(history_df, target_rounds=10):
    """
    사용자 제안: 회차별 주기 구간 비중을 합산하여 확률(가중치) 산출
    """
    # 1. 구간 정의 (labels는 UI와 일치시킴)
    bins = [-1, 0, 3, 6, 9, 14, 24, 1000]
    labels = ["0주기", "1~3주기", "4~6주기", "7~9주기", "10~14주기", "15~24주기", "25주기 이상"]
    
    # 각 회차의 비중 데이터를 담을 리스트
    round_ratios = []
    # 개별 당첨 기록 (표시용)
    all_individual_results = []

    recent_rounds = history_df.head(target_rounds)
    
    for idx, row in recent_rounds.iterrows():
        round_num = row['round']
        winning_nums = [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]
        
        # 현재 회차의 구간별 카운트 초기화
        current_counts = {label: 0 for label in labels}
        
        for num in winning_nums:
            prev_appearances = history_df.iloc[idx+1:]
            last_idx = prev_appearances[(prev_appearances['n1'] == num) | 
                                        (prev_appearances['n2'] == num) | 
                                        (prev_appearances['n3'] == num) | 
                                        (prev_appearances['n4'] == num) | 
                                        (prev_appearances['n5'] == num) | 
                                        (prev_appearances['n6'] == num)].index
            
            skip_val = last_idx[0] - idx - 1 if not last_idx.empty else 100 # 콜드는 큰 값 부여
            
            # 구간 판별
            for i in range(len(bins)-1):
                if bins[i] < skip_val <= bins[i+1]:
                    current_counts[labels[i]] += 1
                    break
            
            all_individual_results.append({"회차": round_num, "번호": num, "주기": skip_val})
            
        # [핵심] 회차별 비중 계산 (개수 / 6.0)
        round_ratio = {label: count / 6.0 for label in labels}
        round_ratios.append(round_ratio)

    # 2. 결과 데이터프레임 생성
    analysis_results = pd.DataFrame(all_individual_results)
    
    # 3. [핵심] 모든 회차의 비중을 합산하여 평균값 산출
    # 이 과정에서 콜드번호가 하나라도 포함된 회차의 지분(16.6%)이 통계에 정확히 반영됩니다.
    avg_ratios = pd.DataFrame(round_ratios).mean().reset_index()
    avg_ratios.columns = ['구간', '확률']
    
    # 기존 코드와의 호환성을 위해 빈도수 역산 (표시용)
    total_samples = target_rounds * 6
    avg_ratios['출현빈도'] = (avg_ratios['확률'] * total_samples).round(0).astype(int)
    
    return analysis_results, avg_ratios

def render_skip_group_weight_ui(group_stats):
    """
    group_stats: 이미 구간별 평균 비중(확률)이 계산된 데이터프레임
    """
    st.markdown("### ⚙️ 구간별 당첨 통계 및 가중치 설정 (회차 비중 방식)")
    
    # [핵심] 확률의 10배를 기본 가중치로 설정
    group_stats['가중치'] = (group_stats['확률'] * 10).round(2)
    
    # 세션 상태 관리
    if 'skip_weight_df' not in st.session_state:
        st.session_state.skip_weight_df = group_stats
    else:
        # 데이터 갱신
        st.session_state.skip_weight_df['출현빈도'] = group_stats['출현빈도']
        st.session_state.skip_weight_df['확률'] = group_stats['확률']
        st.session_state.skip_weight_df['가중치'] = group_stats['가중치']
        
    st.info("💡 **회차별 비중 합산 방식**으로 계산되었습니다. 콜드번호 구간의 확률이 더 합리적으로 산출됩니다.")
    
    edited_df = st.data_editor(
        st.session_state.skip_weight_df,
        column_config={
            "구간": st.column_config.TextColumn("스킵 주기 구간", disabled=True),
            "출현빈도": st.column_config.NumberColumn("추정 빈도수", format="%d회", disabled=True),
            "확률": st.column_config.ProgressColumn("평균 점유율(비중)", format="%.4f", min_value=0, max_value=1),
            "가중치": st.column_config.NumberColumn(
                "가중치(비중x10)", 
                min_value=0.0, max_value=10.0, step=0.1, format="%.1f"
            )
        },
        hide_index=True,
        use_container_width=True,
        key="skip_editor"
    )
    
    st.session_state.skip_weight_df = edited_df
    return edited_df
