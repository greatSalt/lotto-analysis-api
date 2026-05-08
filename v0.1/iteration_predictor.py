

import streamlit as st
import pandas as pd
import numpy as np

def predict_with_momentum(df, last_nums):
    prediction_results = []
    win_nums_list = df[['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].values.tolist()

    for num in last_nums:
        # 1. 기초 지표 산출
        current_skip = calculate_skip_manually(num, 0, win_nums_list)
        recent_count = sum(1 for draw in win_nums_list[:10] if num in draw)
        
        # 2. 점수 체계 초기화
        score = 0
        status = "🧊 일반"
        
        # [강력 필터 1: 기세형 (45번 타겟)]
        # 최근 10회 중 3회 이상 등장했다면 '기세형' 점수만 부여
        if recent_count >= 3:
            score = 80 + (recent_count * 5)
            status = "🔥 기세형(Hot)"
            
        # [강력 필터 2: 반등형 (28번 타겟)]
        # 10회 이상 장기 미출수라면 '반등형' 점수 부여
        elif current_skip >= 10:
            score = 70 + (current_skip * 2)
            status = "⏳ 반등형(Cold)"
            
        # [강력 필터 3: 재출현형 (단기 스킵)]
        # 최근에 나왔고 기세도 나쁘지 않은 경우
        elif current_skip <= 2 and recent_count >= 1:
            score = 50 + (recent_count * 5)
            status = "⚡ 재출현형"
            
        # 위 조건에 해당하지 않는 '어중간한 번호'는 기본 점수만 부여 (상위권 진입 불가)
        else:
            score = (recent_count * 5) + current_skip
            status = "🧊 일반"

        prediction_results.append({
            "번호": num,
            "최근빈도": f"{recent_count}회",
            "현재스킵": f"{current_skip}회",
            "유형": status,
            "점수": score
        })

    # 점수 순으로 정렬 (이제 28, 45번이 무조건 상단에 위치함)
    return pd.DataFrame(prediction_results).sort_values(by="점수", ascending=False)



# [함수] 특정 회차(idx)에서 특정 번호(num)의 직전 스킵 주기를 계산
def calculate_skip_manually(target_num, current_idx, all_nums):
    skip_count = 0
    # 현재 회차 다음(과거 방향)부터 탐색
    for past_idx in range(current_idx + 1, len(all_nums)):
        if target_num in all_nums[past_idx]:
            return skip_count
        skip_count += 1
    return skip_count # 끝까지 안 나왔다면 전체 구간이 스킵

def render_carryover_analysis(df, analyze_range):
    st.header("🔄 이월수 통계 및 패턴 분석")
    
    # 1. n1~n6 컬럼을 win_nums 리스트로 병합 
    temp_df = df.copy()
    win_nums_list = temp_df[['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].fillna(0).values.astype(int).tolist() # 최신순 리스트
    
    # 1. 이월수 데이터 추출 (현재 회차와 전회차 비교)
    iter_counts = []
    analysis_data = []
    
    display_limit = min(len(win_nums_list) - 1, analyze_range)
    
    #draw_nos = temp_df['round'].tolist() if 'round' in temp_df.columns else list(range(len(win_nums_list), 0, -1))
     
    for i in range(display_limit):
        curr = win_nums_list[i]     # 현재 회차
        prev = win_nums_list[i+1]   # 전 회차
        
        # 이월수 찾기
        carryovers = sorted(list(set(curr) & set(prev)))
        count = len(carryovers)
        iter_counts.append(count)
        
        # 각 이월수의 스킵 주기 실시간 계산
        # 예시 데이터 구조: {번호: 스킵}
        skip_results = []
        for num in carryovers:
            # i번째 회차에 나온 num이 그 전에는 언제 나왔었나? (i+1부터 탐색)
            s_val = calculate_skip_manually(num, i+1, win_nums_list)
            skip_results.append(s_val)
            
        # 테이블 행 구성 (회차, 번호1, 스킵1, 번호2, 스킵2, 개수)
        row = {
            "회차": f"{temp_df.iloc[i].get('round', i)}회",
            "이월수1": carryovers[0] if count > 0 else "-",
            "스킵1": skip_results[0] if count > 0 else "-",
            "이월수2": carryovers[1] if count > 1 else "-",
            "스킵2": skip_results[1] if count > 1 else "-",
            "개수": count
        }
        analysis_data.append(row)

    history_df = pd.DataFrame(analysis_data)

    # 2. 상단 테이블: 출현 이력 (내림차순)
    st.subheader("📋 회차별 이월수 출현 이력")
    st.dataframe(history_df.head(analyze_range), use_container_width=True) 

    # 3. 중단 통계: 전체 vs 최근 10회
    st.subheader("📊 이월수 출현 빈도 통계")
    
    total_counts = history_df['개수'].value_counts().reindex([0, 1, 2], fill_value=0)
    recent_10_counts = history_df['개수'].head(10).value_counts().reindex([0, 1, 2], fill_value=0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**[전체 회차 통계]**")
        total_stats = pd.DataFrame({
            "개수": ["0개(멸)", "1개", "2개"],
            "횟수": total_counts.values,
            "확률": [f"{(v/len(history_df)*100):.1f}%" for v in total_counts.values]
        })
        st.table(total_stats)

    with col2:
        st.markdown("**[최근 10회 통계]**")
        recent_stats = pd.DataFrame({
            "개수": ["0개(멸)", "1개", "2개"],
            "횟수": recent_10_counts.values,
            "확률": [f"{(v/10*100):.1f}%" for v in recent_10_counts.values]
        })
        st.table(recent_stats)

    st.divider()
    st.subheader("🔮 복합 데이터 기반 금주 이월 후보")
        
    # 위 함수 호출
    recommend_df = predict_with_momentum(temp_df, win_nums_list[0])
        
    # 시각화 (컬럼형태)
    cols = st.columns(6)
    for i, row in enumerate(recommend_df.itertuples()):
        with cols[i]:
            st.metric(label=f"번호 {row.번호}", value=row.유형, delta=row.최근빈도)
            st.caption(f"적합도: {row.점수}점")
            
def check_carryover_filter(nums, last_win_nums, allowed_carry_counts):
    """
    nums: 생성된 6개 번호
    last_win_nums: 직전 회차 당첨번호 6개 (보너스 제외 권장)
    allowed_carry_counts: 허용된 이월수 개수 리스트 (예: [0, 1])
    """
    # 생성된 번호와 직전 당첨번호 간의 교집합 개수 계산
    intersect = set(nums) & set(last_win_nums)
    current_carry_count = len(intersect)
    
    return current_carry_count in allowed_carry_counts

