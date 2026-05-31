import random
import pandas as pd
import streamlit as st
from target_end_analysis import check_same_end_digit_filter
from iteration_predictor import check_carryover_filter
from funatsu_sakai import make_funatsu_sakai_pool
from empty_zone_engine import apply_strategy_style
from crazyLogic import get_crazy_analysis
from savepicked import display_sidebar_picks, get_highlight_style, init_all_saved_data, save_to_sheets_by_type, save_recommended_picks

def generate_strategic_combinations(selected_df, ratio_filters, sum_range, skip_weights_df, fixed_nums, exclude_nums, target_digits, allowed_pairs, allowed_carry, last_win_nums, min_ac=7, allowed_hl=None, max_con=1, count=5):
    """
    selected_df: 사용자가 체크한 번호들의 데이터프레임
    ratio_filters: ['3:3', '2:4'] 형태의 홀짝 비율 리스트
    sum_range: (min, max) 형태의 총합 튜플
    skip_weights_df: 사용자 UI에서 설정한 [구간, 가중치] 정보가 담긴 데이터프레임
    fixed_nums: [1, 7] 형태의 고정수 리스트
    exclude_nums: [10, 45] 형태의 제외수 리스트
    count: 생성할 조합 개수
    
    고급 3대 필터(AC, 고저, 연번)가 통합된 전략 생성 엔진
    """
    
    """
    가중치 데이터가 없으면 실행을 중단하고 메시지를 반환함
    """
    # 1. [핵심] 가중치 데이터 유효성 검사 및 즉시 리턴 로직
    if skip_weights_df is None or (isinstance(skip_weights_df, pd.DataFrame) and skip_weights_df.empty):
        st.warning("⚠️ 주기별 가중치 데이터가 없습니다. 상단의 [주기 분석] 버튼을 먼저 클릭하여 가중치를 계산해 주세요.")
        return [] # 데이터가 없으므로 빈 리스트 리턴 후 함수 종료
    
    # 기초 풀(Pool) 구성: 선택된 번호에서 제외수 먼저 제거
    base_pool_df = selected_df[~selected_df['번호'].isin(exclude_nums)].copy()
    
    # 가중치 계산을 위한 맵 생성
    weight_map = dict(zip(skip_weights_df['구간'], skip_weights_df['가중치']))
    
    # 고정수가 선택된 번호에 없다면 강제로 추가 (사용자 의도 존중)
    selected_nums = base_pool_df['번호'].tolist()
    
    # 추출 대상에서 고정수 제외 (고정수는 나중에 합류)
    pool_for_sampling = [n for n in selected_nums if n not in fixed_nums]
    
    # 번호별 가중치 리스트 산출
    pool_weights = [get_weight_by_skip(n, weight_map) for n in pool_for_sampling]

    if len(pool_for_sampling) < (6 - len(fixed_nums)):
        return []
    
    final_combinations = []
    attempts = 0
    need_count = 6 - len(fixed_nums) # 고정수를 제외하고 더 뽑아야 할 개수
    
    # 2. 조합 생성 및 필터링 루프
    while len(final_combinations) < count and attempts < 50000:
        attempts += 1
        
        # 가중치 기반 비복원 추출
        sample_nums = []
        temp_pool = list(pool_for_sampling)
        temp_weights = list(pool_weights)
        
        try:
            # 1. 가중치 확률에 따라 부족한 개수만큼 추출
            for _ in range(need_count):
                if not temp_pool: break
                # random.choices로 가중치 적용 추출
                picked = random.choices(temp_pool, weights=temp_weights, k=1)[0]
                sample_nums.append(picked)
                
                # 비복원 추출을 위해 선택된 요소 제거
                idx = temp_pool.index(picked)
                temp_pool.pop(idx)
                temp_weights.pop(idx)
            
            # 2. 최종 번호 구성 (기존 just_nums 변수명 유지)
            just_nums = sorted(fixed_nums + sample_nums)
            
            # 3. 중복 조합 체크 (기존 로직 유지)
            if just_nums in [[n[0] for n in c] for c in final_combinations]:
                continue

            # 필터 1: 홀짝 비율 검증
            odd_count = len([n for n in just_nums if n % 2 != 0])
            even_count = 6 - odd_count
            curr_ratio = f"{odd_count}:{even_count}"
            if curr_ratio not in ratio_filters: continue
            
            # 필터 2: 총합 범위 검증
            curr_sum = sum(just_nums)
            if not (sum_range[0] <= curr_sum <= sum_range[1]): continue

            # [신규] 이월수 필터 적용
            if not check_carryover_filter(just_nums, last_win_nums, allowed_carry):
                continue
            
            # 2. 동끝수 필터 적용
            if not check_same_end_digit_filter(just_nums, allowed_pairs, target_digits):
                continue # 조건 미달 시 이번 번호는 버림
            
            # --- [신규 고급 필터 통합] ---
            # 필터 3: AC, 고저, 연번 통합 검증 함수 호출
            if not check_advanced_filters(just_nums, min_ac, allowed_hl, max_con):
                continue

            # --- [최종] 모든 관문 통과 시 결과 저장 ---
            # 사용자님의 새로운 주기 기준 적용 (get_group_v2 호출)
            full_combo = [[n, get_group_v2(n)] for n in just_nums]
            final_combinations.append(full_combo)
            
        except (ValueError, Exception):
            # 샘플링 풀이 부족할 경우 탈출
            break
            
    return final_combinations

def get_weight_by_skip(n, weight_map):
    """
    특정 번호(n)의 현재 스킵 주기를 확인하여 
    사용자가 설정한 구간 가중치(weight_map)를 반환하는 독립 함수
    """
    # 세션 상태에 저장된 번호별 현재 스킵 주기 딕셔너리 참조
    # 만약 skip_dict가 없다면 기본값 99주기로 처리
    skip = st.session_state.get('skip_dict', {}).get(n, 99)
    
    if skip == 0: label = "0주기"
    elif 1 <= skip <= 3: label = "1~3주기"
    elif 4 <= skip <= 6: label = "4~6주기"
    elif 7 <= skip <= 9: label = "7~9주기"
    elif 10 <= skip <= 14: label = "10~14주기"
    elif 15 <= skip <= 24: label = "15~24주기"
    else: label = "25주기 이상"
    
    return weight_map.get(label, 1.0)
    
def get_group_v2(n):
    """
    사용자 정의 주기 기준에 따른 그룹 판별:
    0주기: 이월수 / 1~3주기: HOT / 4~14주기: WARM / 15주기 이상: COLD
    """
    skip = st.session_state.get('skip_dict', {}).get(n, 99)
    
    if skip == 0:
        return '이월수'  # 전회차 당첨번호
    elif 1 <= skip <= 3:
        return 'HOT'
    elif 4 <= skip <= 14:
        return 'WARM'
    else:
        return 'COLD'

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

def check_advanced_filters(nums, min_ac=7, allowed_hl=None, max_consecutive=1):
    """
    v2.5 고급 필터링 시스템
    nums: 생성된 6개 번호 리스트
    """
    s_nums = sorted(nums)
    
    # 1. AC값 필터 (산술적 복잡도: 보통 7~10이 당첨권)
    diffs = set()
    for i in range(6):
        for j in range(i+1, 6):
            diffs.add(s_nums[j] - s_nums[i])
    ac = len(diffs) - 5
    if ac < min_ac:
        return False

    # 2. 고저 비율 필터 (Low: 1~22, High: 23~45)
    low_cnt = len([n for n in nums if n <= 22])
    hl_ratio = f"{low_cnt}:{6-low_cnt}"
    if allowed_hl and hl_ratio not in allowed_hl:
        return False

    # 3. 연번 필터 (연속된 숫자 쌍 개수 제한)
    con_cnt = 0
    for i in range(5):
        if s_nums[i+1] - s_nums[i] == 1:
            con_cnt += 1
    if con_cnt > max_consecutive:
        return False

    return True

def display_filter_setting(conn, sheet_url):
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        if 'fixed_nums' not in st.session_state:
            st.session_state.fixed_nums = []
        # 고정수 입력 UI
        st.multiselect(
            "📌 고정수 (FIX)", 
            options=range(1, 46), 
            default=st.session_state.fixed_nums,
            key="fixed_nums" # 키 추가
        )

        if st.button("💾 고정수 시트 갱신", key="btn_fix_save"):
            # 현재 선택된 fixed_nums를 시트에 덮어쓰기
            save_to_sheets_by_type(conn, sheet_url, st.session_state.fixed_nums, "FIX")
            # UI 강제 새로고침
            st.rerun()
                    
    with col_input2:
        if 'exclude_nums' not in st.session_state:
            st.session_state.exclude_nums = []
        # 제외수 입력 UI
        st.multiselect(
            "🚫 제외수 (EX)", 
            options=range(1, 46), 
            default=st.session_state.exclude_nums,
            key="exclude_nums" # 키 추가
        )
                
        if st.button("💾 제외수 시트 갱신", key="btn_ex_save"):
            #현재 선택된 exclude_nums를 시트에 덮어쓰기
            save_to_sheets_by_type(conn, sheet_url, st.session_state.exclude_nums, "EX")
            # UI 강제 새로고침
            st.rerun()
                    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        if 'sel_oe' not in st.session_state:
            st.session_state.sel_oe = ["3:3", "2:4"]
            
        st.write("**추가 필터 1: 홀짝 비율**")
        ratio_options = ["0:6", "1:5", "2:4", "3:3", "4:2", "5:1", "6:0"]
        st.multiselect(
            "허용 비율",    
            options=ratio_options, 
            default=st.session_state.sel_oe, 
            key='sel_oe'
        )
    with col_f2:
        if 'sum_range' not in st.session_state:
            st.session_state.sum_range = (100, 170)
            
        st.write("**추가 필터 2: 총합 범위**")
        st.slider(
            "총합 범위 설정", 
            min_value=80, 
            max_value=200, 
            value=st.session_state.sum_range, # 세션값이 있으면 사용, 없으면 기본값
            step=1,
            key='sum_range'
        )
    
    if st.session_state.enable_sakai == True:
        st.divider()
        with st.expander("후나츠 사카이 분류 설정", expanded=True):
            row_col1, row_col2 = st.columns(2)
            with row_col1:  #후나츠 사카이 분류 번호 포함 갯수 (1~6)
                if 'sakai_cnt' not in st.session_state or st.session_state.sakai_cnt not in [0,1,2,3,4,5]:
                    st.session_state.sakai_cnt = 3
                # index를 세션값에 맞춰 계산
                con_options = [0, 1, 2, 3, 4, 5]
                
                st.selectbox(
                    "포함할 번호 갯수", 
                    con_options, 
                    key = 'sakai_cnt'
                )
            with row_col2:  # 후나츠 사카이 분류 조합 비율 선택(3:2:1,2:3:1,...)
                if 'sakai_ratio' not in st.session_state:
                    st.session_state.sakai_ratio = ["3:3:3"]
                    
                ratio_options = ["6:0:0", "5:0:1", "4:0:2", "3:3:3"]
                st.multiselect(
                    "조합 비율",    
                    options=ratio_options, 
                    default=st.session_state.sakai_ratio, 
                    key='sakai_ratio'
                )
                            
    # --- 실전 필터 적용 섹션 ---
    st.divider()
    with st.expander("🚀 필터링 조건 설정 (생성 시 적용)", expanded=True):
        row1_col1, row1_col2, row3_col3 = st.columns(3)
        with row1_col1:
            if 'sel_ac' not in st.session_state:
                st.session_state.sel_ac = 7
            st.number_input(
                "최소 AC값", 
                min_value=0, 
                max_value=10, 
                value=st.session_state.sel_ac, # 로드된 값 사용
                key='sel_ac'
            )
        with row1_col2:
            if 'sel_hl' not in st.session_state:
                st.session_state.sel_hl = ["3:3", "2:4", "4:2"]
            st.multiselect(
                "허용 고저비율", 
                ["3:3", "2:4", "4:2", "1:5", "5:1", "0:6", "6:0"], # 0:6, 6:0 추가
                default=st.session_state.sel_hl, # 로드된 값 사용
                key = 'sel_hl'
            )
        with row3_col3:
            if 'sel_carry' not in st.session_state:
                st.session_state.sel_carry = [0, 1, 2]
            # 이월수(직전회차 번호) 개수 설정
            carry_options = [0, 1, 2, 3]
            st.multiselect(
                "허용 이월수 개수",
                carry_options,
                default=st.session_state.sel_carry,
                key = 'sel_carry',
                help="직전 회차 당첨번호 중 몇 개를 포함할지 결정합니다. (보통 0~2개 권장)"
            )        
                
        row1_col1, row1_col2, row2_col3 = st.columns(3)    
        with row1_col1:
            if 'sel_con' not in st.session_state or st.session_state.sel_con not in [0,1,2]:
                st.session_state.sel_con = 1
            # index를 세션값에 맞춰 계산
            con_options = [0, 1, 2]
            
            st.selectbox(
                "최대 연번허용", 
                con_options, 
                key = 'sel_con'
            )
        with row1_col2:
            if 'sel_end' not in st.session_state:
                st.session_state.sel_end = [1, 2]
            # [신규 추가] 동끝수 쌍 설정
            # 보통 1~2쌍이 가장 많이 나오므로 기본값을 [1, 2]로 추천
            pair_options = [0, 1, 2, 3]
            st.multiselect(
                "허용 동끝수 쌍",
                pair_options,
                default=st.session_state.sel_end, # 리스트 형태로 저장/로드
                key = 'sel_end',
                help="한 조합 내에 끝자리가 같은 숫자가 몇 쌍 있는지 설정합니다. (예: 12, 22는 1쌍)"
            )
        with row2_col3:
            # 특정 동끝수 지정 (선택사항)
            # 예: 7을 선택하면 (7, 17, 27, 37) 중 2개 이상이 포함된 조합을 우선시함
            digit_options = list(range(10)) # 0~9까지
                    
            if 'sel_target_end' not in st.session_state:
                st.session_state.sel_target_end = []
                     
            st.multiselect(
                "강제 지정 끝수 (선택)", 
                digit_options, 
                default=st.session_state.sel_target_end,
                key='sel_target_end',
                help="특정 끝수가 반드시 동끝수로 나오길 원할 때 선택하세요."
            )
                        
    if st.button("📌 필터 설정값 저장"):
        with st.spinner("모든 필터 설정을 저장 중..."):
            # 각 필터값을 리스트 형태로 변환하여 저장 함수 호출
            save_to_sheets_by_type(conn, sheet_url, st.session_state.sel_oe, 'F_OE')
            save_to_sheets_by_type(conn, sheet_url, [st.session_state.sel_ac], 'F_AC')
            save_to_sheets_by_type(conn, sheet_url, [st.session_state.sel_con], 'F_CON')
            save_to_sheets_by_type(conn, sheet_url, st.session_state.sel_hl, 'F_HL') # 리스트 그대로 전달
            save_to_sheets_by_type(conn, sheet_url, [st.session_state.sum_range[0], st.session_state.sum_range[1]], 'F_SUM')
            save_to_sheets_by_type(conn, sheet_url, st.session_state.sel_end, 'F_END') # 동끝수 필터값 저장
            save_to_sheets_by_type(conn, sheet_url, st.session_state.sel_target_end, 'F_TARGET_END')
            save_to_sheets_by_type(conn, sheet_url, st.session_state.sel_carry, 'F_CARRY')
            save_to_sheets_by_type(conn, sheet_url, [st.session_state.sakai_cnt], 'F_SAKAI_CNT')
            save_to_sheets_by_type(conn, sheet_url, st.session_state.sakai_ratio, 'F_SAKAI_RATIO')
                    
            # 고정수와 제외수도 함께 저장 (선택 사항)
            #save_to_sheets_by_type(conn, sheet_url, fixed_nums, 'FIX')
            #save_to_sheets_by_type(conn, sheet_url, exclude_nums, 'EX')
        
            st.success("🎉 모든 분석 전략이 SavedPicks 시트에 통합 저장되었습니다!")

def disp_recommended_nums_table(conn, sheet_url, df_raw, decision):
    
    # 1. 번호 필터링 및 우선순위 분석 데이터프레임 생성
    analysis_df = get_crazy_analysis(df_raw)
    filtered_df = analysis_df.copy()
        
    # --- 전체 번호 선택 / 자동 분류 로직 ---
    col_select_all, col_sakai_nums = st.columns(2)
    with col_select_all:
        select_all = st.checkbox("🔄 모든 번호 선택", value=False, key="all_nums_toggle")
    with col_sakai_nums:
        select_sakai_nums = st.checkbox("후나츠 사카이 분류", value=False, key='sakai_nums_toggle')
    
    st.session_state.enable_sakai = False
    
    # 체크박스 상태에 따른 '선택' 열 초기화 알고리즘
    if select_all:
        filtered_df['선택'] = True
    elif select_sakai_nums:
        latest_row = df_raw.iloc[0] # 데이터프레임의 첫 번째 행(iloc[0])이 최신 회차
    
        # 직전 회차 당첨번호 및 보너스 번호 정수 파싱
        last_winning_numbers = [int(latest_row[f'n{i}']) for i in range(1,7)]
        last_bonus_number = int(latest_row['bonus'])
        
        # 사카이 기법 특수 풀(Pool) 생성 후 포함 여부 매핑
        magic_pool = make_funatsu_sakai_pool(last_winning_numbers, last_bonus_number)
        filtered_df['선택'] = filtered_df['번호'].isin(magic_pool)
        
        st.session_state.enable_sakai = True
    else:
        # 아무것도 체크되지 않았다면 세션에 로드되어 있는 기존 PICK 데이터 복원
        filtered_df['선택'] = filtered_df['번호'].isin(st.session_state.get('my_saved_picks', []))
            
    # 2. UI 레이아웃 및 캡션 설정
    st.subheader("📊 전략 분석 테이블")
    st.info("🔵 **파란색**: 역사적 확률에 따른 **멸 확정** 구간 / 🟡 **노란색**: 멸 확률 40% 초과 **주의** 구간")
        
    # 데이터 에디터에 노출할 유효 컬럼 필터링
    cols = ['선택', '번호', '통합크레이지점수', '출현수', '출현율', '현재연속', '최대연속', '반등지수', '에너지지수', '탄성점수', '리듬점수', '박자상태']
    available_cols = [c for c in cols if c in filtered_df.columns]
    
    # 3. 대화형 데이터 에디터 렌더링 (전달받은 decision 인자로 스타일링 적용)    
    edited_df = st.data_editor(
        apply_strategy_style(filtered_df[available_cols], decision),
        hide_index=True,
        use_container_width=True,
        column_config={
            "선택": st.column_config.CheckboxColumn(required=True),
            "번호": st.column_config.NumberColumn(format="%d"),
            "통합크레이지점수": st.column_config.NumberColumn(format="%.1f")
        },
        disabled=[c for c in available_cols if c != '선택'] # 선택 컬럼만 수정 가능
    )

    # 4. 사용자가 최종 선택한 번호 리스트 추출
    selected_numbers = edited_df[edited_df['선택'] == True]['번호'].tolist()
        
    # 5. 저장 컨트롤러 및 세션/시트 데이터 동기화
    st.divider()
    if st.button("💾 선택 번호 저장", use_container_width=True):
        # 체크된 번호들 추출 및 정수형 변환
        new_picks = [int(n) for n in edited_df[edited_df['선택'] == True]['번호'].tolist()]
            
        # 구글 시트 백엔드 반영
        save_to_sheets_by_type(conn, sheet_url, new_picks, "PICK")
        # 세션 상태 즉시 갱신 (사이드바 즉시 반영)
        st.session_state.my_saved_picks = new_picks
            
        st.toast(f"🎯 {len(new_picks)}개 번호 저장 완료!")
        st.rerun()
        
    return selected_numbers
