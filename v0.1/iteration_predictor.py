

import streamlit as st
import pandas as pd
import numpy as np

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

    # 4. 하단 예측: 스킵 주기에 따른 번호 추천
    st.divider()
    st.subheader("🔮 금주 이월 확률 예측")
    
    # 확률 기반 예측 개수 결정
    pred_count = recent_10_counts.idxmax()
    pred_prob = (recent_10_counts.max() / 10) * 100
    
    st.info(f"💡 통계 근거: 이번 회차는 **{pred_count}개**가 나올 확률이 **{pred_prob}%**로 가장 높습니다.")
    
    last_nums = win_nums_list[0]
    st.write(f"🔎 **지난주 번호({last_nums})의 현재 미출현(Skip) 기간:**")
    
    cols = st.columns(6)
    for idx, num in enumerate(last_nums):
        # [업그레이드] 단순히 '유력'이 아니라 현재 스킵값을 직접 보여줌
        now_skip = calculate_skip_manually(num, 0, win_nums_list)
        with cols[idx]:
            st.metric(label=f"번호 {num}", value=f"{now_skip}회", 
                      delta="이월 유력" if now_skip >= 10 else None)

'''
def predict_by_probability(df):
    # 1. 전체 이월수 히스토리 생성 (최신순 -> 과거순)
    iter_history = []
    for i in range(len(df) - 1):
        curr = set(df.iloc[i][['n1', 'n2', 'n3', 'n4', 'n5', 'n6']])
        prev = set(df.iloc[i+1][['n1', 'n2', 'n3', 'n4', 'n5', 'n6']])
        iter_history.append(len(curr & prev))
    
    # 2. 직전 회차(1217회)의 이월수 개수 확인
    last_iter_count = iter_history[0] 
    
    # 3. 과거 데이터에서 '직전 회차와 같은 개수'였던 사례들 찾기
    # 예: 과거에 이월수가 1개였을 때, 그 다음 회차는 어땠는가?
    next_counts = []
    for i in range(1, len(iter_history) - 1):
        if iter_history[i] == last_iter_count:
            next_counts.append(iter_history[i-1]) # '그다음' 결과 저장
            
    if not next_counts:
        return 1, "참조 데이터 부족으로 표준 확률 적용"

    # 4. 빈도수 계산 (0개, 1개, 2개...)
    prob_0 = next_counts.count(0) / len(next_counts) * 100
    prob_1 = next_counts.count(1) / len(next_counts) * 100
    prob_2 = next_counts.count(2) / len(next_counts) * 100
    
    # 5. 가장 확률이 높은 개수 선택
    max_prob = max(prob_0, prob_1, prob_2)
    if max_prob == prob_1:
        predicted = 1
    elif max_prob == prob_2:
        predicted = 2
    else:
        predicted = 0
        
    reason = f"과거 {last_iter_count}개 이월 후 다음 회차에 {predicted}개가 나온 실제 빈도는 {max_prob:.1f}%입니다."
    
    return predicted, reason, {0: prob_0, 1: prob_1, 2: prob_2}

def predict_with_numbers(df, current_nums_info):
    # 1. 개수 예측 (기존 로직 사용)
    predicted_count, reason, prob_dist = predict_by_probability(df)
    
    # 2. 외부 함수 호출 (apply 사용)
    # Pandas가 각 행을 calculate_refined_score 함수의 'row' 인자로 전달합니다.
    current_nums_info['이월확률'] = current_nums_info.apply(calculate_refined_score, axis=1)
    
    # 확률 상위권 번호 추출
    top_targets = current_nums_info.sort_values(by='이월확률', ascending=False)
    
    # 예측 개수(predicted_count)만큼 번호 선정
    recommended_nums = top_targets.head(predicted_count)
    
    return predicted_count, reason, recommended_nums


def predict_iteration_count(df, current_nums_info):
    # 1. 최근 5회차간의 실제 이월수 개수 리스트 생성
    # (n1~n6 컬럼을 집합으로 변환하여 윗행과 교집합 개수 산출)
    iter_history = []
    for i in range(len(df) - 1):
        curr = set(df.iloc[i][['n1', 'n2', 'n3', 'n4', 'n5', 'n6']])
        prev = set(df.iloc[i+1][['n1', 'n2', 'n3', 'n4', 'n5', 'n6']])
        iter_history.append(len(curr & prev))
    
    recent_iters = iter_history[:5] # 최근 5회차 이월수 기록
    avg_iter = sum(recent_iters) / len(recent_iters) if recent_iters else 0

    # 2. 직전 번호들의 '기세 잔여' 에너지 (10번, 31번 등)
    # (최대연속 > 현재연속) 인 번호들의 개수
    potential_energy = len(current_nums_info[current_nums_info['현재연속'] < current_nums_info['최대연속']])

    # 3. 최종 예측 로직
    if avg_iter <= 0.8 and potential_energy >= 2:
        count = 2
        reason = f"최근 이월 흐름이 저조({avg_iter:.1f}개)하고, 기세가 남은 번호가 {potential_energy}개 포착되어 2개 이월 가능성 높음"
    elif avg_iter >= 1.6:
        count = 1
        reason = f"최근 이월 과다 출현({avg_iter:.1f}개)에 따른 통계적 회귀로 1개 예상"
    else:
        count = 1
        reason = "표준 출현 확률(43%) 및 안정적 흐름에 근거하여 1개 예상"

    return count, reason
    
def calculate_refined_score(row):
    """
    Pandas apply용 외부 함수: 이월 적합도 및 기세 임계점 보정 로직
    """
    # 1. 기초 데이터 추출
    curr_streak = row.get('현재연속', 0)
    max_streak = row.get('최대연속', 1)
    occurrence_rate = row.get('출현율', 13.3)
    
    # 2. 기세 점수 (streak_part) 산출: 임계점 도달 시 브레이크
    if curr_streak > 0:
        if curr_streak >= max_streak:
            streak_part = 0  # 역대 최고치 도달/초과 시 0점 (꺾일 타이밍)
        else:
            streak_part = (curr_streak / max_streak) * 100
    else:
        streak_part = 0

    # 3. 기존 복합 지표 가중치 계산 (30/50/10/5/5 비율)
    current_score = (
        (row.get('반등지수', 0) * 30) +
        (streak_part * 0.5) + # 업데이트된 기세 점수 반영
        (row.get('에너지지수', 0) * 10) +
        (row.get('탄성점수', 0) * 0.05) +
        (row.get('리듬점수', 0) * 0.05)
    )

    # 4. [G] 추가 보정: 출현율 체급 가산점 (수학적 기대치 13.3% 기준)
    current_score += (occurrence_rate - 13.3) * 0.5

    # 5. 최종 총합 점수 보정 (이월수 전용 멀티플라이어 필터)
    total_score = current_score
    
    if curr_streak > 0:
        if curr_streak < max_streak:
            # 기세 유지 구간 (기록에 여유가 있을수록 1.0 ~ 1.2배)
            momentum_factor = 1.0 + (1.0 - (curr_streak / max_streak)) * 0.2
            total_score *= momentum_factor
        elif curr_streak == max_streak:
            # 임계점 도달 (0.5배 강제 하락)
            total_score *= 0.5
        else:
            # 기세 초과 경신 (0.3배 강제 하락)
            total_score *= 0.3
            
    return total_score
'''
            
