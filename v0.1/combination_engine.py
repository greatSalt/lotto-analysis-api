import random
import pandas as pd

def generate_strategic_combinations(selected_df, ratio_filters, sum_range, count=5):
    """
    selected_df: 사용자가 체크한 번호들의 데이터프레임
    ratio_filters: ['3:3', '2:4'] 형태의 홀짝 비율 리스트
    sum_range: (min, max) 형태의 총합 튜플
    count: 생성할 조합 개수
    """
    selected_nums = selected_df['번호'].tolist()
    
    if len(selected_nums) < 6:
        return []

    # 1. 핫/웜/콜드 그룹 분리 (상대적 점수 기준)
    # 점수 상위 30% : HOT / 하위 30% : COLD / 나머지 : WARM
    q_high = selected_df['통합크레이지점수'].quantile(0.7)
    q_low = selected_df['통합크레이지점수'].quantile(0.3)
    
    hot_pool = selected_df[selected_df['통합크레이지점수'] >= q_high]['번호'].tolist()
    cold_pool = selected_df[selected_df['통합크레이지점_score'] <= q_low]['번호'].tolist() # 오타 수정 가능성 대비
    # 실제 컬럼명 확인 필요: 통합크레이지점수
    hot_pool = selected_df[selected_df['통합크레이지점수'] >= q_high]['번호'].tolist()
    cold_pool = selected_df[selected_df['통합크레이지점수'] <= q_low]['번호'].tolist()
    warm_pool = selected_df[(selected_df['통합크레이지점수'] > q_low) & 
                            (selected_df['통합크레이지점수'] < q_high)]['번호'].tolist()

    # 안전장치: 풀이 부족할 경우 최소 인원 강제 할당
    if len(hot_pool) < 2: hot_pool = selected_nums[:2]
    if len(cold_pool) < 1: cold_pool = selected_nums[-1:]
    warm_pool = list(set(selected_nums) - set(hot_pool) - set(cold_pool))

    final_combinations = []
    attempts = 0
    
    # 2. 조합 생성 및 필터링 루프
    while len(final_combinations) < count and attempts < 2000:
        attempts += 1
        try:
            # 2-3-1 전략 샘플링
            sample = random.sample(hot_pool, 2) + random.sample(warm_pool, 3) + random.sample(cold_pool, 1)
            sample.sort()
            
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
