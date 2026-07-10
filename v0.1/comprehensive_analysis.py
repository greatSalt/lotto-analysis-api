import streamlit as st
import pandas as pd

def get_detailed_status(target_idx, df_raw):
    """주기별 상태 계산 (0:이월, 1-3:핫, 4-14:미들, 15+:콜드)"""
    status_map = {}
    skip_durations = {}
    all_possible = list(range(1, 46))
    
    for n in all_possible:
        # 과거 데이터에서 번호 n의 마지막 출현 위치 찾기
        found_indices = df_raw.iloc[target_idx + 1:].index[
            (df_raw.iloc[target_idx + 1:][['n1','n2','n3','n4','n5','n6']] == n).any(axis=1)
        ].tolist()
        
        if not found_indices:
            curr_skip = 999
        else:
            curr_skip = found_indices[0] - (target_idx + 1)
        
        if curr_skip == 0: status = "이월수"
        elif 1 <= curr_skip <= 3: status = "HOT"
        elif 4 <= curr_skip <= 14: status = "WARM"
        else:
            status = "COLD"
            skip_durations[n] = curr_skip
        status_map[n] = status
    return status_map, skip_durations

def calculate_lotto_stats(nums, last_nums):
    """각종 통계 지표 계산"""
    # 홀짝
    odds = len([n for n in nums if n % 2 != 0])
    evens = 6 - odds
    # 총합
    total_sum = sum(nums)
    # AC값
    diffs = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            diffs.add(abs(nums[i] - nums[j]))
    ac = len(diffs) - (6 - 1)
    # 고저 (1~22:저, 23~45:고)
    highs = len([n for n in nums if n >= 23])
    lows = 6 - highs
    # 연번 갯수
    consecutive = 0
    for i in range(len(nums)-1):
        if nums[i+1] - nums[i] == 1:
            consecutive += 1
    # 동끝수 갯수 (쌍의 수)
    ends = [n % 10 for n in nums]
    end_counts = {x: ends.count(x) for x in set(ends)}
    same_ends = sum(1 for count in end_counts.values() if count >= 2)
    # 이월수 갯수
    carry_count = len(set(nums) & set(last_nums)) if last_nums else 0
    
    return f"{odds}:{evens}", total_sum, ac, f"{highs}:{lows}", consecutive, same_ends, carry_count

def render_comprehensive_analysis(df_raw, display_count=20):
    st.header("📊 회차별 종합 상세 분석")
    
    # 범례 표시 (변경사항 반영)
    st.markdown("""
    <div style="margin-bottom:15px;">
        <span style="background-color:#FFFFFF; color:black; border:2px solid #333; padding:2px 8px; border-radius:10px; font-weight:bold;">이월(흰색)</span>
        <span style="background-color:#FF4B4B; color:white; padding:2px 8px; border-radius:10px; font-weight:bold;">핫(빨강)</span>
        <span style="background-color:#FFD700; color:black; padding:2px 8px; border-radius:10px; font-weight:bold;">미들(노랑)</span>
        <span style="background-color:#1E90FF; color:white; padding:2px 8px; border-radius:10px; font-weight:bold;">콜드(파랑)</span>
    </div>
    """, unsafe_allow_html=True)

    analysis_data = []
    for i in range(display_count):
        if i >= len(df_raw): break
        row = df_raw.iloc[i]
        curr_nums = sorted([int(row[f'n{j}']) for j in range(1, 7)])
        
        # 이전 회차 데이터 준비
        last_nums = []
        if i + 1 < len(df_raw):
            last_nums = [int(df_raw.iloc[i+1][f'n{j}']) for j in range(1, 7)]
        
        status_map, skip_durations = get_detailed_status(i, df_raw)
        oe, t_sum, ac, hl, con, send, carry = calculate_lotto_stats(curr_nums, last_nums)
        
        balls_html = ""
        cold_skips = []
        for n in curr_nums:
            status = status_map.get(n)
            if status == "이월수": bg, color, border = "#FFFFFF", "black", "2px solid #333"
            elif status == "HOT": bg, color, border = "#FF4B4B", "white", "1px solid #777"
            elif status == "WARM": bg, color, border = "#FFD700", "black", "1px solid #777"
            else: 
                bg, color, border = "#1E90FF", "white", "1px solid #777"
                cold_skips.append(f"{n}({skip_durations.get(n, 15)})")
            
            ball_style = f"background-color:{bg}; color:{color}; padding:2px 8px; margin:1px; border-radius:12px; border:{border}; font-weight:bold; display:inline-block; font-size:12px;"
            balls_html += f'<span style="{ball_style}">{n}</span>'

        analysis_data.append({
            "회차": f"<b>{int(row['round'])}</b>",
            "당첨번호 분석": balls_html,
            "콜드스킵주기": ", ".join(cold_skips) if cold_skips else "-",
            "홀짝": oe,
            "총합": t_sum,
            "AC": ac,
            "고저": hl,
            "연번": con,
            "동끝": send,
            "이월": carry
        })

    final_df = pd.DataFrame(analysis_data)
    st.markdown(final_df.to_html(escape=False, index=False), unsafe_allow_html=True)
