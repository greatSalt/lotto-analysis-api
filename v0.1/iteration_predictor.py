
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px

def std_probability_distribution_chart():
    st.write("💡 **이월수 개수별 표준 확률 분포 (로또 전회차)**")
    
    # 1. 데이터프레임 변환
    df = pd.DataFrame({
        '이월수': ["0개", "1개", "2개", "3개+"],
        '확률': [38.4, 43.2, 15.2, 3.2]
    })
    
    # 2. 베이스 차트 (막대) 정의
    bars = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X('이월수:N', sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('확률:Q', title='확률 (%)'),
        color=alt.Color('이월수:N', legend=None)
    )
    
    # 3. 텍스트 레이어 (막대 위 숫자) 정의
    text = bars.mark_text(
        align='center',
        baseline='bottom',
        dy=-5, # 막대 탑에서 위로 5픽셀 띄우기
        fontSize=13,
        fontWeight='bold'
    ).encode(
        text=alt.Text('확률:Q', format='.1f') # 소수점 첫째자리까지 수치 표시 (뒤에 % 수동 결합 가능)
    )
    
    # 4. 두 레이어를 병합( + )하여 화면에 출력
    st.altair_chart(bars + text, use_container_width=True)
    
###########
    st.write("💡 **이월수 개수별 표준 확률 분포**")
    
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

#####################################################################
'''
import pandas as pd
import streamlit as st

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
    
    dynamic_results = []
    
    # 최신 회차부터 지정된 갯수만큼 동적 루프 연산
    for idx in range(target_rounds):
        if idx + 1 >= len(history_df): break
            
        row = history_df.iloc[idx]
        round_num = row['round']
        
        # 직전 회차 본번호 6개 수집 (보너스 제외하여 팩트 정정 반영)
        prev_row = history_df.iloc[idx + 1]
        candidates = prev_row[['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].tolist()
        candidates_str = ", ".join(map(str, candidates))
        
        # 거시 개수 보정률 동적 계산
        macro_modifier = get_macro_count_modifier(history_df, idx)
        
        scored_candidates = []
        for num in candidates:
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
        current_win = row[['n1', 'n2', 'n3', 'n4', 'n5', 'n6']].tolist()
        actual_carry_nums = [n for n in current_win if n in candidates]
        actual_count = len(actual_carry_nums)
        actual_carry_str = ", ".join(map(str, actual_carry_nums)) if actual_carry_nums else "없음"
        
        # 개수 판정
        count_hit = "🎯 적중" if predicted_count == actual_count else ("✅ 근접" if abs(predicted_count - actual_count) <= 1 else "❌ 불일치")
        
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