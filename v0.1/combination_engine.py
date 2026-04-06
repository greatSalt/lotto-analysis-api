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

