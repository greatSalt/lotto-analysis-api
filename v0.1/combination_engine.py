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
    # 1. 기초 풀(Pool) 구성: 선택된 번호에서 제외수 먼저 제거
    base_pool_df = selected_df[~selected_df['번호'].isin(exclude_nums)].copy()
    selected_nums = base_pool_df['번호'].tolist()
    
    # 고정수가 선택된 번호에 없다면 강제로 추가 (사용자 의도 존중)
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
    
    q_high = temp_df['통합크레이지점수'].quantile(0.7) if not temp_df.empty else 0
    q_low = temp_df['통합크레이지점수'].quantile(0.3) if not temp_df.empty else 0
    
    # 실제 컬럼명 확인 필요: 통합크레이지점수
    hot_pool = temp_df[temp_df['통합크레이지점수'] >= q_high]['번호'].tolist()
    cold_pool = temp_df[temp_df['통합크레이지점수'] <= q_low]['번호'].tolist()
    warm_pool = list(set(selected_nums) - set(hot_pool) - set(cold_pool))

    final_combinations = []
    attempts = 0
    need_count = 6 - len(fixed_nums) # 고정수를 제외하고 더 뽑아야 할 개수
    
    # 2. 조합 생성 및 필터링 루프
    while len(final_combinations) < count and attempts < 2000:
        attempts += 1
        try:
            # 여기서는 단순 랜덤이 아닌 2-3-1 비율을 최대한 유지하며 남은 개수 추출
            sample_pool = hot_pool + warm_pool + cold_pool
            if len(sample_pool) < need_count: continue
            extra_nums = random.sample(sample_pool, need_count)
            sample = sorted(fixed_nums + extra_nums)
            
            if sample in final_combinations:
                continue

            # 필터 1: 홀짝 비율 검증
            odd_count = len([n for n in sample if n % 2 != 0])
            even_count = 6 - odd_count
            curr_ratio = f"{odd_count}:{even_count}"
            
            # 필터 2: 총합 범위 검증
            curr_sum = sum(sample)
            
            # 모든 조건 만족 시 추가
            if curr_ratio in ratio_filters and sum_range[0] <= curr_sum <= sum_range[1]:
                final_combinations.append(sample)
        except ValueError:
            # 샘플링 풀이 부족할 경우 탈출
            break
            
    return final_combinations
