import random
import pandas as pd

def generate_strategic_combinations(selected_df, ratio_filters, sum_range, fixed_nums, exclude_nums, count=5):
    """
    selected_df: 사용자가 체크한 번호들의 데이터프레임
    ratio_filters: ['3:3', '2:4'] 형태의 홀짝 비율 리스트
    sum_range: (min, max) 형태의 총합 튜플
    fixed_nums: [1, 7] 형태의 고정수 리스트
    exclude_nums: [10, 45] 형태의 제외수 리스트
    count: 생성할 조합 개수
    """
    # 기초 풀(Pool) 구성: 선택된 번호에서 제외수 먼저 제거
    base_pool_df = selected_df[~selected_df['번호'].isin(exclude_nums)].copy()
    # 고정수가 선택된 번호에 없다면 강제로 추가 (사용자 의도 존중)
    selected_nums = base_pool_df['번호'].tolist()
    
    for fn in fixed_nums:
        if fn not in selected_nums:
            selected_nums.append(fn)
    
    if len(selected_nums) < 6:
        return []

    # 1. 핫/웜/콜드 그룹 분리 (상대적 점수 기준)
    # 점수 상위 30% : HOT / 하위 30% : COLD / 나머지 : WARM
    # 고정수 제외하고 분리하여 샘플링 유연성 확보
    remaining_pool = [n for n in selected_nums if n not in fixed_nums]
    temp_df = base_pool_df[base_pool_df['번호'].isin(remaining_pool)]
    
    if not temp_df.empty:
        q_high = temp_df['통합크레이지점수'].quantile(0.7) if not temp_df.empty else 0
        q_low = temp_df['통합크레이지점수'].quantile(0.3) if not temp_df.empty else 0
    
        # 실제 컬럼명 확인 필요: 통합크레이지점수
        hot_pool = temp_df[temp_df['통합크레이지점수'] >= q_high]['번호'].tolist()
        cold_pool = temp_df[temp_df['통합크레이지점수'] <= q_low]['번호'].tolist()
        
    # [최적화] 루프 진입 전 고정수들의 그룹 정보 미리 태깅 (외부 함수 get_group 사용)
    fixed_with_group = [[n, get_group(n, hot_pool, cold_pool)] for n in fixed_nums]
    
    # 고정수를 제외한 나머지 번호들의 바구니를 미리 제작
    remaining_pool_with_group = [
        [n, get_group(n, hot_pool, cold_pool)] 
        for n in selected_nums if n not in fixed_nums
    ]
    
    final_combinations = []
    attempts = 0
    need_count = 6 - len(fixed_nums) # 고정수를 제외하고 더 뽑아야 할 개수
    
    # 2. 조합 생성 및 필터링 루프
    while len(final_combinations) < count and attempts < 2000:
        attempts += 1
        try:
            if len(remaining_pool_with_group) < need_count:
                break
            
            # 부족한 개수만큼 샘플링
            extra_with_group = random.sample(remaining_pool_with_group, need_count)
            
            # 최종 조합 (고정수 + 추가수)
            full_combo = fixed_with_group + extra_with_group
            full_combo.sort(key=lambda x: x[0]) # 번호순 정렬
            
            # 중복 체크용 번호 리스트
            just_nums = [x[0] for x in full_combo]
            if just_nums in [[n[0] for n in c] for c in final_combinations]:
                continue

            # 필터 1: 홀짝 비율 검증
            odd_count = len([n for n in just_nums if n % 2 != 0])
            even_count = 6 - odd_count
            curr_ratio = f"{odd_count}:{even_count}"
            
            # 필터 2: 총합 범위 검증
            curr_sum = sum(just_nums)
            
            # 모든 조건 만족 시 추가
            if curr_ratio in ratio_filters and sum_range[0] <= curr_sum <= sum_range[1]:
                final_combinations.append(full_combo)
        except (ValueError, Exception):
            # 샘플링 풀이 부족할 경우 탈출
            break
            
    return final_combinations
    
def get_group(n, hot_pool, cold_pool):
    """
    특정 번호(n)가 어느 점수 그룹에 속하는지 판별하는 외부 함수
    """
    if n in hot_pool:
        return 'HOT'
    elif n in cold_pool:
        return 'COLD'
    return 'WARM'

def get_ratio_analysis(df):
    """최근 회차 범위 내 홀짝 비율 분석 및 추천 로직"""
    ratios = []
    for _, row in df.iterrows():
        # 당첨번호 6개 추출 (보너스 제외)
        nums = [row[f'n{i}'] for i in range(1, 7)]
        odd_count = len([n for n in nums if n % 2 != 0])
        even_count = 6 - odd_count
        ratios.append(f"{odd_count}:{even_count}")
    
    # 비율별 빈도수 계산
    ratio_counts = pd.Series(ratios).value_counts()
    total_draws = len(df)
    
    # 이론적 확률 (수학적 기대치)
    theoretical_probs = {
        "3:3": 33.3, "2:4": 23.3, "4:2": 23.3, 
        "1:5": 9.3,  "5:1": 9.3,  "0:6": 0.8, "6:0": 0.8
    }
    
    analysis_data = []
    for ratio, count in ratio_counts.items():
        actual_prob = (count / total_draws) * 100
        theo_prob = theoretical_probs.get(ratio, 0)
        
        # 확률 차이 계산 (기세 분석)
        diff = actual_prob - theo_prob
        
        # 추천 상태 결정
        if diff > 5: status = "🔥 과열 (주의)"
        elif diff < -5: status = "💎 반등 기대 (추천)"
        else: status = "✅ 정상 (안정)"
        
        analysis_data.append({
            "비율": ratio,
            "출현수": count,
            "현재확률": f"{actual_prob:.1f}%",
            "이론확률": f"{theo_prob:.1f}%",
            "상태": status
        })
        
    return pd.DataFrame(analysis_data).sort_values("비율")
    
def get_advanced_stat_analysis(df):
    """n1~n6 컬럼을 이용한 정밀 통계 분석 (수치 데이터 포함)"""
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    total_draws = len(df)
    ratios, sums = [], []
    
    for _, row in df.iterrows():
        try:
            nums = [int(row[f'n{i}']) for i in range(1, 7)]
            odd = len([n for n in nums if n % 2 != 0])
            ratios.append(f"{odd}:{6-odd}")
            sums.append(sum(nums))
        except: continue

    # 1. 홀짝 상세 통계 (이론 확률 vs 실제 확률)
    ratio_counts = pd.Series(ratios).value_counts()
    theo_ratios = {
        "3:3": 33.3, "2:4": 23.3, "4:2": 23.3, 
        "1:5": 9.3,  "5:1": 9.3,  "0:6": 0.8, "6:0": 0.8
    }
    
    ratio_data = []
    for r, theo in theo_ratios.items():
        count = int(ratio_counts.get(r, 0))
        actual = (count / total_draws * 100) if total_draws > 0 else 0
        diff = actual - theo  # 편차
        
        # 상태 판정 (편차 5% 기준)
        status = "🔥 과열" if diff > 5 else "💎 반등" if diff < -5 else "✅ 정상"
        
        ratio_data.append({
            "비율": r,
            "출현(회)": count,
            "실제%": round(actual, 2),
            "이론%": theo,
            "편차": round(diff, 2),
            "상태": status
        })

    # 2. 총합 상세 통계 (구간별 분포)
    bins = [0, 80, 100, 120, 140, 160, 180, 1000]
    labels = ["80미만", "80-100", "101-120", "121-140", "141-160", "161-180", "180초과"]
    sum_cats = pd.cut(sums, bins=bins, labels=labels)
    sum_counts = sum_cats.value_counts()
    
    # 총합 이론 분포 (약 10만 회 시뮬레이션 기준 표준 분포값)
    theo_sums = {
        "80-100": 13.5, "101-120": 24.5, "121-140": 24.5, 
        "141-160": 17.5, "161-180": 9.5, "80미만": 5.0, "180초과": 5.5
    }
    
    sum_data = []
    for lbl in labels:
        count = int(sum_counts.get(lbl, 0))
        actual = (count / total_draws * 100) if total_draws > 0 else 0
        theo = theo_sums.get(lbl, 0)
        diff = actual - theo
        
        status = "🔥 과열" if diff > 7 else "💎 반등" if diff < -7 else "✅ 정상"
        
        sum_data.append({
            "구간": lbl,
            "출현(회)": count,
            "실제%": round(actual, 2),
            "이론%": theo,
            "편차": round(diff, 2),
            "상태": status
        })

    return pd.DataFrame(ratio_data).sort_values("비율"), pd.DataFrame(sum_data)

def get_comprehensive_analysis(df):
    """AC값, 고저비율, 연번 분포를 포함한 종합 분석"""
    if df is None or df.empty:
        return None

    total_draws = len(df)
    ac_list, hl_list, con_list = [], [], []

    for _, row in df.iterrows():
        try:
            nums = sorted([int(row[f'n{i}']) for i in range(1, 7)])
            
            # 1. AC값 계산
            diffs = set()
            for i in range(len(nums)):
                for j in range(i + 1, len(nums)):
                    diffs.add(nums[j] - nums[i])
            ac_val = len(diffs) - (len(nums) - 1)
            ac_list.append(ac_val)
            
            # 2. 고저 비율 (Low: 1~22, High: 23~45)
            low_cnt = len([n for n in nums if n <= 22])
            hl_list.append(f"{low_cnt}:{6-low_cnt}")
            
            # 3. 연번 개수 (연속된 숫자 쌍)
            con_cnt = 0
            for i in range(len(nums) - 1):
                if nums[i+1] - nums[i] == 1:
                    con_cnt += 1
            con_list.append(con_cnt)
        except: continue

    # --- 데이터프레임 생성 로직 (요약) ---
    # AC값 분포 (기대치: 7~10)
    ac_df = pd.Series(ac_list).value_counts().sort_index().reset_index()
    ac_df.columns = ['AC값', '출현']
    
    # 고저 비율 분포 (기대치: 3:3, 2:4, 4:2)
    hl_df = pd.Series(hl_list).value_counts().reset_index()
    hl_df.columns = ['고저비율', '출현']
    
    # 연번 분포 (기대치: 0~1쌍)
    con_df = pd.Series(con_list).value_counts().sort_index().reset_index()
    con_df.columns = ['연번쌍', '출현']

    return ac_df, hl_df, con_df

def filter_combination_v2_5(nums):
    """생성된 조합이 3대 필터를 통과하는지 검사"""
    # 1. AC값 필터 (7 이상)
    diffs = set()
    s_nums = sorted(nums)
    for i in range(6):
        for j in range(i+1, 6):
            diffs.add(s_nums[j] - s_nums[i])
    ac = len(diffs) - 5
    if ac < 7: return False
    
    # 2. 고저 비율 필터 (0:6, 6:0 같은 극단적 경우 제외)
    low = len([n for n in nums if n <= 22])
    if low == 0 or low == 6: return False
    
    # 3. 연번 필터 (연번이 3쌍 이상인 비현실적 조합 제외)
    con = 0
    for i in range(5):
        if s_nums[i+1] - s_nums[i] == 1: con += 1
    if con >= 3: return False
    
    return True

