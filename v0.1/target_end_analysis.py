import streamlit as st
import pandas as pd
from collections import Counter

def render_target_end_analysis(history_df, target_rounds):
    """
    동끝수 상세 분석 메뉴: 3개의 분석 표를 출력
    """
    st.header("🔢 동끝수(Same Ending Digit) 상세 분석")
    st.info(f"💡 최근 {target_rounds}회차 동안의 동끝수 패턴을 분석합니다.")

    # 1. 데이터 추출 및 기초 분석
    recent_df = history_df.head(target_rounds).copy()
    analysis_data = []

    for idx, row in recent_df.iterrows():
        # 당첨번호 6개 추출
        nums = [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]
        # 끝수 리스트 생성 (예: [12, 22, 3] -> [2, 2, 3])
        end_digits = [n % 10 for n in nums]
        
        # 끝수별 출현 빈도 계산
        counts = Counter(end_digits)
        
        # 2개 이상 나온 끝수(동끝수)와 그에 해당하는 번호들 찾기
        target_ends = [digit for digit, count in counts.items() if count >= 2]
        same_end_nums = [n for n in nums if n % 10 in target_ends]
        
        # 동끝수 쌍(Pair)의 개수 (예: [2,2, 5,5] 면 2쌍)
        pair_count = len(target_ends)
        
        analysis_data.append({
            "회차": int(row['round']),
            "동끝수": sorted(same_end_nums) if same_end_nums else "-",
            "동끝수갯수": pair_count,
            "raw_ends": target_ends # 내부 통계용
        })

    # 전체 데이터프레임 생성
    df_base = pd.DataFrame(analysis_data)

    # --- [표 1] 회차별 상세 현황 (최신순) ---
    st.subheader("1️⃣ 회차별 동끝수 현황 (최신순)")
    # 리스트 형태를 문자열로 예쁘게 변환
    df_display1 = df_base[["회차", "동끝수", "동끝수갯수"]].copy()
    # 리스트 내부의 숫자들도 소수점 없이 문자열화 (None인 경우 '-' 처리)
    # 반드시 int()를 먼저 거쳐서 소수점을 완전히 제거한 후 str로 변환합니다.
    df_display1["동끝수"] = df_display1["동끝수"].apply(
        lambda x: ", ".join(map(str, [int(n) for n in x])) if isinstance(x, list) else "-"
    )
    
    # 동끝수갯수에 Int64 적용 (None이 생겨도 정수형 유지)
    df_display1["동끝수갯수"] = df_display1["동끝수갯수"].astype("Int64")
    
    st.table(df_display1.sort_values(by="회차", ascending=False))

    # --- [표 2] 끝수별 출현 빈도 (내림차순) ---
    st.subheader("2️⃣ 끝수별 동끝수 출현 빈도 (가장 많이 나온 순)")
    all_appeared_ends = []
    for item in analysis_data:
        all_appeared_ends.extend(item["raw_ends"])
    
    if all_appeared_ends:
        df_ends = pd.Series(all_appeared_ends).value_counts().reset_index()
        df_ends.columns = ["동끝수", "횟수"]
        
        # [핵심] Int64 타입으로 소수점 강제 제거
        df_ends["동끝수"] = df_ends["동끝수"].astype("Int64")
        df_ends["횟수"] = df_ends["횟수"].astype("Int64")
        
        st.table(df_ends) # Series.value_counts()는 이미 내림차순 정렬됨
    else:
        st.write("분석 범위 내에 동끝수가 없습니다.")

    # --- [표 3] 동끝수 쌍 개수별 빈도 (내림차순) ---
    st.subheader("3️⃣ 동끝수 쌍(Pair) 개수 분포 (가장 많이 나온 순)")
    df_pairs = df_base["동끝수갯수"].value_counts().reset_index()
    df_pairs.columns = ["동끝수갯수", "횟수"]
    st.table(df_pairs) # 내림차순 정렬됨

def check_same_end_digit_filter(nums, allowed_pairs, target_digits):
    """
    nums: 생성된 6개 번호 리스트
    allowed_pairs: 허용된 동끝수 쌍 개수 리스트 (예: [1, 2])
    target_digits: 강제 지정 끝수 리스트 (예: [7])
    """
    # 1. 끝수 리스트 추출 (예: [7, 17, 23, 34, 41, 45] -> [7, 7, 3, 4, 1, 5])
    end_digits = [n % 10 for n in nums]
    
    # 2. 끝수별 빈도 계산
    from collections import Counter
    counts = Counter(end_digits)
    
    # 3. 동끝수(2개 이상 출현)인 끝수들만 추출
    # 예: 끝수가 [7, 7, 3, 4, 1, 5] 라면 active_ends는 [7]이 됨
    active_ends = [digit for digit, count in counts.items() if count >= 2]
    current_pair_count = len(active_ends)
    
    # --- [조건 1] 동끝수 쌍 개수 검사 ---
    if current_pair_count not in allowed_pairs:
        return False
    
    # --- [조건 2] 지정 끝수 포함 여부 검사 (설정이 있을 경우만) ---
    if target_digits:
        # active_ends에 있는 모든 동끝수가 내가 선택한 target_digits 안에 포함되어 있어야 함!
        # 즉, 선택하지 않은 숫자(예: 3, 9)가 동끝수 그룹에 하나라도 끼어있으면 즉시 탈락
        is_all_allowed = all(ae in target_digits for ae in active_ends)
        if not is_all_allowed:
            return False
        # 지정한 끝수 중 하나라도 실제 동끝수(active_ends)에 포함되어 있는지 확인
        # 예: target_digits가 [7]인데 active_ends에 7이 있으면 통과
        #has_target = any(td in active_ends for td in target_digits)
        #if not has_target:
            #return False
            
    return True

