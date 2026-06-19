import streamlit as st
import pandas as pd
import Config
#import numpy as np
#import plotly.express as px

#-----------------------------------------------------------------#

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

#-----------------------------------------------------------------#

#test code
def get_number_skip_value(history_df, target_idx, num):
    """특정 회차(target_idx) 직전 기준, 해당 번호의 스킵 주기(몇 주 미출현했는지) 계산"""
    """
    history_df: 최신순으로 정렬된 데이터프레임
    target_idx: 데이터프레임의 행 인덱스 (iloc)
    num: 찾으려는 번호
    """
    # target_idx에 해당하는 실제 round 번호를 가져옴(기준 회차 번호)
    target_round = history_df.iloc[target_idx]['round']
    
    # 1. 기준 회차보다 작거나 같은(더 과거의) 데이터만 필터링
    prev_history = history_df[history_df['round'] < target_round]
    
    # 2. 해당 번호가 출현한 행 찾기
    appearances = prev_history[(prev_history['n1'] == num) | (prev_history['n2'] == num) | 
                               (prev_history['n3'] == num) | (prev_history['n4'] == num) | 
                               (prev_history['n5'] == num) | (prev_history['n6'] == num)]
    
    if appearances.empty:
        return 100  # 콜드 번호 가상 주기
    
    # 3. 가장 최근 출현 회차 번호와 현재 타겟 회차 번호의 차이 계산
    latest_appearance_round = appearances['round'].max()
    return target_round - latest_appearance_round - 1
    
def get_calculated_weight(num_skip_val, weight_df):
    """번호의 스킵 주기를 기반으로 UI 가중치 테이블에서 해당 가중치 매핑"""
    # UI에서 등록된 가중치 딕셔너리 변환
    weight_dict = dict(zip(weight_df['구간'], weight_df['가중치']))
    
    if num_skip_val == 0: return weight_dict.get("0주기", 1.0)
    elif 1 <= num_skip_val <= 3: return weight_dict.get("1~3주기", 1.0)
    elif 4 <= num_skip_val <= 6: return weight_dict.get("4~6주기", 1.0)
    elif 7 <= num_skip_val <= 9: return weight_dict.get("7~9주기", 1.0)
    elif 10 <= num_skip_val <= 14: return weight_dict.get("10~14주기", 1.0)
    elif 15 <= num_skip_val <= 24: return weight_dict.get("15~24주기", 1.0)
    else: return weight_dict.get("25주기 이상", 1.0)

def get_historical_deviation(history_df, target_idx, num):
    """특정 회차 직전 기준, 해당 번호의 [25주 출현율 - 50주 출현율] 편차 산출"""
    """
    history_df: 최신순으로 정렬된 50주 데이터프레임
    target_idx: 데이터프레임의 행 인덱스 (iloc)
    num: 찾으려는 번호
    """
    
    df_50 = history_df.iloc[target_idx + 1 : target_idx + 51]
    df_25 = history_df.iloc[target_idx + 1 : target_idx + 26]
    
    if len(df_50) < 50: 
        if Config.DEBUG:# [debug console code]
            # 터미널이나 콘솔 창에서 필터링 과정을 정확하게 추적할 수 있습니다.
            log_msg = f"[[25주 출현율 - 50주 출현율] 편차 산출] 조건확인 -> 50주기{len(df_50)} < 50: 0.0 return"
            # [메모리 보호] 실시간 렌더링 과부하를 막기 위해 상시 300개 스냅샷 유지
            if len(st.session_state.filter_debug_logs) >= 300:
                st.session_state.filter_debug_logs.pop(0) # 가장 오래된 로그 하나 제거
                            
            st.session_state.filter_debug_logs.append(log_msg)
        return 0.0  # 데이터 부족 시 0 처리
    
    count_50 = 0
    count_25 = 0
    cols = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']
    
    for _, row in df_50.iterrows():
        if num in [row[c] for c in cols]: count_50 += 1
    for _, row in df_25.iterrows():
        if num in [row[c] for c in cols]: count_25 += 1
        
    prob_50 = count_50 / 50.0   # 50주기 출현율
    prob_25 = count_25 / 25.0   # 20주기 출현율
    return prob_25 - prob_50    # 개별 번호의 출현율 편차 = 25주기(추세선) - 50주기(기준선)

def calculate_momentum_score(history_df, target_idx, num):
    
    target_round = history_df.iloc[target_idx]['round']
    # 최근 5주 데이터 추출
    recent_5_weeks = history_df[history_df['round'] < target_round].head(5)

    # 최근 5주간 출현 횟수 계산
    count = recent_5_weeks[['n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'bonus']].apply(
        lambda x: (x == num).any(), axis=1
    ).sum()

    # '최근성' 가중치 추가: 직전 회차(target_round - 1)에 나왔던 번호인가?
    # 직전 회차에 등장했던 번호라면 가산점을 더 크게 부여 (이월 가속도)
    prev_row = history_df[history_df['round'] == target_round - 1].iloc[0]
    is_in_prev = num in [prev_row['n1'], prev_row['n2'], prev_row['n3'], prev_row['n4'], prev_row['n5'], prev_row['n6'], prev_row['bonus']]
    
    base_score = count * 0.2    # 2회 이상일 경우 기본 모멘텀 보너스 
    recent_bonus = 0.8 if is_in_prev else 0.0 # 직전 회차면 0.8점 추가
    
    if Config.DEBUG:# [debug console code]
            # 터미널이나 콘솔 창에서 필터링 과정을 정확하게 추적할 수 있습니다.
            log_msg = f"[target_idx: {target_idx}, target_round: {target_round}, num: {num}, count: {count}, base_score+recent_bonus: {base_score}+{recent_bonus} recent_5_weeks: {recent_5_weeks}"
            # [메모리 보호] 실시간 렌더링 과부하를 막기 위해 상시 300개 스냅샷 유지
            if len(st.session_state.filter_debug_logs) >= 300:
                st.session_state.filter_debug_logs.pop(0) # 가장 오래된 로그 하나 제거
                            
            st.session_state.filter_debug_logs.append(log_msg)
    
    return base_score + recent_bonus        

def count_historical_carryover(df, num):
    """
    해당 번호가 과거 전체 회차에서 이월(직전 회차 등장 후 다음 회차 또 등장)된 횟수를 계산
    """
    count = 0
    # 전체 회차를 순회하며 이월 사례 카운트
    for i in range(0, len(df) - 1):
        prev_row = df.iloc[i+1]
        curr_row = df.iloc[i]
        
        # 이전 회차 7개 번호 중 num이 있고, 현재 회차 6개 번호(당첨번호)에 또 등장하면 이월
        prev_nums = [prev_row['n1'], prev_row['n2'], prev_row['n3'], prev_row['n4'], prev_row['n5'], prev_row['n6'], prev_row['bonus']]
        curr_nums = [curr_row['n1'], curr_row['n2'], curr_row['n3'], curr_row['n4'], curr_row['n5'], curr_row['n6']]
        
        if num in prev_nums and num in curr_nums:
            count += 1
    return count
    
def get_carryover_rankings(history_df, test_rounds=1228):
    # 1. 직전 회차 데이터 추출
    prev_row = history_df[history_df['round'] == test_rounds - 1].iloc[0]
    candidates = [prev_row['n1'], prev_row['n2'], prev_row['n3'], 
                  prev_row['n4'], prev_row['n5'], prev_row['n6'], prev_row['bonus']]
    
    scored_candidates = []
    
    for num in set(candidates):
        # 2. 이월 체질 측정 (과거 이월 이력)
        hist_rate = count_historical_carryover(history_df, num)
        
        # 3. 최근 5주간 활성도
        recent_5_weeks = history_df[history_df['round'] < test_rounds].head(5)
        recent_freq = recent_5_weeks[['n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'bonus']].apply(
            lambda x: (x == num).any(), axis=1
        ).sum()
        
        # 4. 이월 전용 점수 산출
        final_score = (hist_rate * 0.6) + (recent_freq * 0.4)
        
        scored_candidates.append({
            "번호": num,
            "최종점수": round(final_score, 2),
            "역사적체질": hist_rate,
            "최근활동성": recent_freq
        })
        
    return pd.DataFrame(scored_candidates).sort_values(by='최종점수', ascending=False)

def run_carryover_fusion_backtest(history_df, weight_df, test_rounds=25):
    """
    [핵심 매크로] 이월수 개수 편차와 주기별 가중치를 결합한 통합 백테스팅 함수
    """
    backtest_summary = []
    
    df_sort = history_df.sort_values(by='round', ascending=False) # 항상 내림차순(최신순) 정렬
    df = df_sort.head(76).copy()

    # 최근 25주기만 돌면서 검증
    for idx in range(test_rounds):
    #for idx in range(1):
        row = df.iloc[idx]
        round_num = row['round']
        
        # 1. 직전 회차의 당첨번호 6개 + 보너스번호 1개 = 총 7개 후보 수집 (사각지대 제거)
        prev_row = df.iloc[idx + 1]
        candidates = [prev_row['n1'], prev_row['n2'], prev_row['n3'], prev_row['n4'], prev_row['n5'], prev_row['n6'], prev_row['bonus']]
        
        scored_candidates = []
        ref_score = get_calculated_weight(0, weight_df) + 0.1 # 기준점수 = 0주기 가중치 + 0.1
        
        # 2. 후보 번호별 융합 스코어링 연산
        for num in candidates:
            # A. 현재 속한 주기 및 가중치 확인
            skip_val = get_number_skip_value(df, idx, num)
            weight = get_calculated_weight(skip_val, weight_df)
            
            # 모멘텀(단기 급상승) 가중치 적용
            m_score = calculate_momentum_score(df, idx, num)
            
            # B. 장단기 편차 확인
            deviation = get_historical_deviation(df, idx, num)
            
            # 최종 이월 점수(fusion_score): 개별번호 편차가 (-)일수록(냉각상태) 가중치를 증폭하여 나올 확률이 높게 판단하기 위한 기준점
            fusion_score = weight * (1.0 - deviation) + m_score
            
            scored_candidates.append({
                "번호": num,
                "편차": deviation,
                "주기가중치": weight,
                "최종점수": round(fusion_score, 2)
            })
            
        scored_df = pd.DataFrame(scored_candidates)
        
        st.dataframe(scored_df, use_container_width=True, hide_index=True)
        
        # 3. 판별 기준 수립: 최종 스코어가 특정 임계치(예: 4.5점)를 넘기는 정예 번호 필터링
        # 주기가중치가 높으면서(-0주기는 원래 높음) 편차가 마이너스인 녀석들이 최상위로 치솟음
        #prime_candidates = scored_df[scored_df['최종점수'] >= 4.5].sort_values(by="최종점수", ascending=False)
        prime_candidates = scored_df[scored_df['최종점수'] >= ref_score].sort_values(by="최종점수", ascending=False)
        predicted_count = len(prime_candidates)
        predicted_nums = prime_candidates['번호'].tolist()
        
        # 4. 실제 결과와 매칭 평가
        actual_win_nums = [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]
        actual_carry_nums = [n for n in actual_win_nums if n in candidates]
        actual_count = len(actual_carry_nums)
        
        # 적중 여부 판정 (C언어 스타일 조건 판별)
        count_hit = "🎯 적중" if predicted_count == actual_count else ("✅ 근접" if abs(predicted_count - actual_count) <= 1 else "❌ 불일치")
        num_hit_count = len([n for n in predicted_nums if n in actual_win_nums])
        
        backtest_summary.append({
            "회차": round_num,
            "예측 이월수": f"{predicted_count}개",
            "실제 이월수": f"{actual_count}개",
            "개수판정": count_hit,
            "예측 타겟번호": predicted_nums,
            "실제 이월번호": actual_carry_nums,
            "맞춘 번호수": f"{num_hit_count}개"
        })
        
    return pd.DataFrame(backtest_summary)

'''    
def std_probability_distribution_chart():
    st.write("💡 **이월수 개수별 표준 확률 분포 (로또 전회차)**")
    
    # 1. 데이터 세팅 (정밀 소수점 반영)
    chart_data = pd.DataFrame({
        "이월수": ["0개", "1개", "2개", "3개+"],
        "확률": [38.4, 43.2, 15.2, 3.2]
    })
    
    # 2. Plotly 막대 차트 생성 (text 옵션으로 막대 위에 수치 지정)
    fig = px.bar(
        chart_data, 
        x="이월수", 
        y="확률", 
        text=chart_data["확률"].apply(lambda x: f"{x}%"), # 숫자 뒤에 % 기호 붙이기
        color="이월수", # 막대별 색상 다르게
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # 3. 차트 레이아웃 정밀 튜닝 (텍스트 위치 및 여백 조정)
    fig.update_traces(
        textposition="outside", # 텍스트를 막대 바깥(위)에 표시
        textfont_size=14,       # 글자 크기
        hovertemplate="이월수: %{x}<br>확률: %{y}%<extra></extra>" # 마우스 올렸을 때 창
    )
    
    fig.update_layout(
        yaxis_title="확률 (%)",
        xaxis_title="이월수 갯수",
        font=dict(family="NanumGothic, Malgun Gothic, sans-serif"), # 한글 깨짐 방지 폰트 가이드
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False # 범례 숨기기 (깔끔하게)
    )
    
    # 4. Streamlit 화면에 렌더링
    st.plotly_chart(fig, use_container_width=True)

'''
'''
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

#####################################################################
'''            

#####################################################################
'''
def get_dynamic_skip_value(history_df, target_idx, num):
    """실시간 기준, 해당 번호의 스킵 주기(미출현 회차 수) 동적 계산"""
    prev_history = history_df.iloc[target_idx + 1:]
    appearances = prev_history[(prev_history['n1'] == num) | (prev_history['n2'] == num) | 
                               (prev_history['n3'] == num) | (prev_history['n4'] == num) | 
                               (prev_history['n5'] == num) | (prev_history['n6'] == num)]
    if appearances.empty:
        return 100
    return appearances.index[0] - target_idx - 1

def get_dynamic_weight(num_skip_val, weight_df):
    """동적으로 바뀐 주기를 기반으로 세션 가중치 테이블과 매핑"""
    weight_dict = dict(zip(weight_df['구간'], weight_df['가중치']))
    if num_skip_val == 0: return weight_dict.get("0주기", 4.4)
    elif 1 <= num_skip_val <= 3: return weight_dict.get("1~3주기", 2.6)
    elif 4 <= num_skip_val <= 6: return weight_dict.get("4~6주기", 2.6)
    elif 7 <= num_skip_val <= 9: return weight_dict.get("7~9주기", 2.6)
    elif 10 <= num_skip_val <= 14: return weight_dict.get("10~14주기", 1.0)
    elif 15 <= num_skip_val <= 24: return weight_dict.get("15~24주기", 0.5)
    else: return weight_dict.get("25주기 이상", 0.2)

def get_dynamic_deviation(history_df, target_idx, num):
    """실시간 회차 직전 기준, 해당 번호의 [25주 출현율 - 50주 출현율] 편차 산출"""
    df_50 = history_df.iloc[target_idx + 1 : target_idx + 51]
    df_25 = history_df.iloc[target_idx + 1 : target_idx + 26]
    
    if len(df_50) < 50: return 0.0
    
    count_50 = sum(df_50[['n1','n2','n3','n4','n5','n6']].isin([num]).sum(axis=1))
    count_25 = sum(df_25[['n1','n2','n3','n4','n5','n6']].isin([num]).sum(axis=1))
        
    return (count_25 / 25.0) - (count_50 / 50.0)

def get_macro_count_modifier(history_df, target_idx):
    """
    [거시적 지표] 최신 25주기 대비 50주기 이월수 빈도 편차를 구하여 
    이번 회차에 적용할 거시 보정계수(디버프/버프)를 동적으로 반환
    """
    # target_idx 직전 50회와 25회 구간 설정
    df_50 = history_df.iloc[target_idx + 1 : target_idx + 51]
    
    # 직전 50회 동안의 이월수 분포 계산
    carryover_counts = []
    for idx in range(len(df_50) - 1):
        current_win = df_50.iloc[idx][['n1','n2','n3','n4','n5','n6']].tolist()
        prev_win = df_50.iloc[idx+1][['n1','n2','n3','n4','n5','n6']].tolist()
        actual_carry = len([n for n in current_win if n in prev_win])
        carryover_counts.append(actual_carry)
        
    # 최근 25회와 과거 25회의 1개 이월 빈도 비교 (과열/냉각 측정)
    recent_25 = carryover_counts[:25]
    count_1_recent = recent_25.count(1) / 25.0
    
    # 1개 이월이 장기 평균(약 43%)보다 과열되어 있으면 디버프 조절
    if count_1_recent > 0.45:
        return 0.85  # 과열 디버프 (가짜 후보 가지치기)
    else:
        return 1.05  # 냉각 버프 (진입 장벽 완화)

def render_dynamic_carryover_analysis_ui(history_df, weight_df, target_rounds=25):
    """
    [최종 완성형 UI 함수]
    데이터를 동적으로 계산하여 실시간 백테스팅 테이블을 Streamlit에 표출
    """
    st.markdown("### 🔄 실시간 연산형 이월수 융합 백데이터 결과표")
    st.caption("※ 고정 데이터가 아닙니다. 새로운 회차가 업데이트되면 연산 결과가 실시간으로 자동 갱신됩니다.")
    
    # [데이터 준비] 필수 변수 및 컬럼 정제
    cols = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']
    history_df[cols] = history_df[cols].fillna(0).astype(int)
    dynamic_results = []
    
    # 💡 인덱스를 -1부터 시작하여 [미래 예측 + 백테스팅]을 한 번에 처리
    # idx = -1: 1229회 예측 (1228회 데이터 참조)
    # idx = 0 ~ 24: 백테스팅 (1228회부터 25회분)
    for idx in range(-1, target_rounds):
        # 예측 루프와 백테스팅 루프의 경계 처리, 1229회는 미래이므로 실제 결과값이 없습니다.
        if idx == -1:
            row_label = "1229회(예상)"
            target_data = history_df.iloc[0] # 가장 최신 데이터(1228회)
            candidates = target_data[cols].tolist()
            # 📍 표시: 데이터가 없음을 명시하여 연산 오류를 방지합니다.
            actual_count = "-" 
            actual_carry_str = "-"
            macro_modifier = get_macro_count_modifier(history_df, -1)
        else:
            # 📍 표시: 과거 백테스팅 루프는 실제 결과값이 존재합니다.
            if idx >= len(history_df) - 1: break
            row_label = str(history_df.iloc[idx]['round']) + "회"
            target_data = history_df.iloc[idx]
            candidates = history_df.iloc[idx + 1][cols].tolist() # 직전 회차 데이터
            # 📍 표시: 실제 당첨번호와 후보군을 비교해 정확도를 측정합니다.
            current_win = target_data[cols].tolist()
            actual_carry_nums = [n for n in current_win if n in candidates]
            actual_count = len(actual_carry_nums)
            actual_carry_str = ", ".join(map(str, actual_carry_nums))
            macro_modifier = get_macro_count_modifier(history_df, idx)
        
        scored_candidates = []
        for num in candidates:
            num = int(float(num))   # 번호를 무조건 정수(int)로 변환 
            
            skip_val = get_dynamic_skip_value(history_df, idx, num)
            weight = get_dynamic_weight(skip_val, weight_df)
            deviation = get_dynamic_deviation(history_df, idx, num)
            
            # 미시 융합 스코어에 거시 보정률까지 동적 연산 결합
            final_score = (weight * (1.0 - deviation)) * macro_modifier
            scored_candidates.append({"번호": num, "점수": final_score})
            
        # 커트라인 4.5점 통과 검증
        prime_nums = [round(c['점수'], 2) for c in scored_candidates if c['점수'] >= 4.5]
        prime_candidate_nums = [c['번호'] for c in scored_candidates if c['점수'] >= 4.5]
        
        # 최고 점수 데이터 포맷팅
        if prime_candidate_nums:
            best_target = ", ".join([f"{n}번({s})" for n, s in zip(prime_candidate_nums, prime_nums)])
            predicted_count = len(prime_candidate_nums)
        else:
            max_idx = pd.DataFrame(scored_candidates)['점수'].idxmax()
            best_target = f"없음 (최고 {scored_candidates[max_idx]['점수']:.2f})"
            predicted_count = 0
            
        # 실제 이월 결과 실시간 대조 (24번 오차 완벽 해결)
        current_win = target_data[['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].tolist()
        actual_carry_nums = [n for n in current_win if n in candidates]
        actual_count = len(actual_carry_nums)
        actual_carry_str = ", ".join(map(str, actual_carry_nums)) if actual_carry_nums else "없음"
        
        # 개수 판정
        count_hit = "🎯 적중" if predicted_count == actual_count else ("✅ 근접" if abs(predicted_count - actual_count) <= 1 else "❌ 불일치")
        
        round_num = row_label # 위 분기(idx == -1 등)에서 정의된 row_label을 사용
        candidates_str = ", ".join(map(str, candidates)) # candidates 리스트를 문자열로 변환
        
        dynamic_results.append([
            round_num, candidates_str, best_target, macro_modifier, 
            f"{predicted_count}개", f"{actual_count}개", count_hit, actual_carry_str
        ])
        
    # 데이터프레임 빌드
    columns = ["회차", "직전 후보군 (본번호)", "최고 점수 보유 번호 (최종 스코어)", "거시 보정", "예측 개수", "실제 이월수", "개수 판정", "실제 이월 번호"]
    report_df = pd.DataFrame(dynamic_results, columns=columns)
    
    # UI 표 표출
    st.data_editor(
        report_df,
        column_config={
            "회차": st.column_config.NumberColumn("회차", format="%d회", disabled=True),
            "거시 보정": st.column_config.NumberColumn("거시 보정률", format="%.2f", disabled=True),
        },
        hide_index=True, use_container_width=True, key="dynamic_fusion_table"
    )
    
    # 실시간 스코어 연산 통계
    total_rounds = len(report_df)
    hit_count = len(report_df[report_df['개수 판정'] == "🎯 적중"])
    st.success(f"📈 **동적 엔진 실시간 적중 통계** ➔ 25개 구간 중 **{hit_count}회차** 정확히 적중 (적중률: **{(hit_count/total_rounds)*100:.1f}%**)")
'''
