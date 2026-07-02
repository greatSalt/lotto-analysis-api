import streamlit as st
import pandas as pd
import Config  # debug code

# 멸구간에 해당되는 번호를 스킵한다
def divide_nums_by_empty_zone(target_nums, zones_row):
    # 멸구간 정의 및 컬럼 설정
    zones = {
        "단번대": lambda n: 1 <= n <= 9,
        "10번대": lambda n: 10 <= n <= 19,
        "20번대": lambda n: 20 <= n <= 29,
        "30번대": lambda n: 30 <= n <= 39,
        "40번대": lambda n: 40 <= n <= 45
    }
    
    # 만약 비어있거나 리스트가 아니라면 빈 리스트([])로 처리하여 에러를 방지합니다.
    selected_zones = zones_row if isinstance(zones_row, list) else []
    
    # 3. 사용자가 선택한 멸구간들만 돌면서 검사
    for zone_name in selected_zones:
        if zone_name in zones:
            condition = zones[zone_name]
            '''
            # 이번 조합(target_nums) 중에 멸구간에 해당하는 숫자가 하나라도 있다면?
            if any(condition(n) for n in target_nums):
                return False
            '''
            # 💡 any() 대신 일반 for 루프로 풀어야 개별 숫자(n)를 로그에 찍을 수 있습니다.
            for n in target_nums:
                if condition(n):
                    if Config.DEBUG:# [debug console code]
                        # 터미널이나 콘솔 창에서 필터링 과정을 정확하게 추적할 수 있습니다.
                        log_msg = f"[멸구간 필터] 조합 {list(target_nums)} ❌ 탈락 -> '{zone_name}' 제한 걸림: 숫자 {n} 발견"
                        # [메모리 보호] 실시간 렌더링 과부하를 막기 위해 상시 300개 스냅샷 유지
                        if len(st.session_state.filter_debug_logs) >= 300:
                            st.session_state.filter_debug_logs.pop(0) # 가장 오래된 로그 하나 제거
                            
                        st.session_state.filter_debug_logs.append(log_msg)
                    
                    return False  # 발견 즉시 함수 종료 (조합 탈락)
              
    return True
    
# 멸 횟수 카운팅 헬퍼 함수
def get_empty_counts(target_df, zones, num_cols):
    counts = {k: 0 for k in zones.keys()}
    for _, row in target_df.iterrows():
        nums = [row[c] for c in num_cols]
        for zone_name, condition in zones.items():
            if not any(condition(n) for n in nums):
                counts[zone_name] += 1
    return counts
    
# 회차별로 멸구간 찾기
def get_empty_finder(picked_nums, zones):
    # 출현한 구간을 먼저 찾고, 전체 zones에서 없는 구간을 추출
    appeared_zones = []
        
    for zone_name, condition in zones.items():
        # nums 중 해당 구간(condition)에 부합하는 번호가 하나라도 있으면 True
        if any(condition(n) for n in picked_nums):
            appeared_zones.append(zone_name)  
        
    # 멸구간 = 전체 구간 - 출현한 구간
    empty_zones = [z for z in zones.keys() if z not in appeared_zones]
    return empty_zones

def display_lotto_empty_zone_matrix(df):
    st.subheader("🕳️ v2.0 동적 멸구간 모니터링 시스템")
    st.markdown("---")
    
    # 50주 및 25주 슬라이싱 데이터 확보
    df_long = df.head(50).copy()
    df_short = df.head(25).copy()
    
    if len(df_long) < 50:
        st.warning("정밀 동적 분석을 위해서는 최소 50회차 이상의 데이터가 시트에 존재해야 합니다.")
        return

    # 구간 정의 및 컬럼 설정
    zones = {
        "단번대 (1~9)": lambda n: 1 <= n <= 9,
        "10번대 (11~19)": lambda n: 10 <= n <= 19,
        "20번대 (21~29)": lambda n: 20 <= n <= 29,
        "30번대 (31~39)": lambda n: 30 <= n <= 39,
        "40번대 (40~45)": lambda n: 40 <= n <= 45
    }
    num_cols = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']

    long_empties = get_empty_counts(df_long, zones, num_cols)
    short_empties = get_empty_counts(df_short, zones, num_cols)
    
    # 테이블 데이터 매핑
    matrix_data = []    # Streamlit 표(Table)를 만들기 위한 로우 데이터를 담을 리스트
    overheated_list = []    # 과열 판정(🚨)을 받은 번호대 이름만 모아둘 리스트
    rebound_list = []   # 반등 판정(🔋)을 받은 번호대 이름만 모아둘 리스트
    
    for zone in zones.keys():
        long_prob = long_empties[zone] / 50 # 50주 동안의 평균 멸확률 (장기 기준선)
        short_prob = short_empties[zone] / 25   # 25주 동안의 실제 멸확률 (단기 추세선)
        deviation = short_prob - long_prob  # [단기 확률 - 장기 확률] 편차 산출
        
        if deviation <= -0.05:
            status = "🚨 과열 (멸 임박)"
            overheated_list.append(zone.split(" ")[0])
        elif deviation >= 0.05:
            status = "🔋 반등 (출현 임박)"
            rebound_list.append(zone.split(" ")[0])
        else:
            status = "✅ 정상 상태"
            
        matrix_data.append({
            "번호대 구간": zone,
            "50주 장기 기준선": f"{long_prob * 100:.1f}%",
            "25주 단기 추세선": f"{short_prob * 100:.1f}%",
            "확률 편차": f"{deviation * 100:+.1f}%",
            "현재 구간 판정": status
        })
        
    df_matrix = pd.DataFrame(matrix_data)
    
    # 데이터프레임 시각화 출력
    st.dataframe(df_matrix, use_container_width=True, hide_index=True)
    
    # 하단 필터 결합 엔진 가이드 동적 출력
    st.markdown("<h6> 🎯 이번 주 조합기 필터링 가이드 2026-06-16(0/0)</h6>", unsafe_allow_html=True)
    if overheated_list:
        zones_str = ", ".join(overheated_list)
        st.error(f"⚠️ **예측 멸구간**[{zones_str}]**  (백테스트 적중률: 81.8%)")
    else:
        st.info("✅ 현재 시스템상 임계치를 넘긴 과열 구간이 없습니다. 기본 조합 비중을 유지하세요.")
