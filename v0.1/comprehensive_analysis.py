import streamlit as st
import pandas as pd

def get_detailed_status(target_idx, df_raw):
    """
    각 회차 당시의 주기별 번호 상태 계산
    0주기: 이월수 (직전 회차 출현)
    1~3주기: 핫넘버
    4~14주기: 미들넘버
    15주기 이상: 콜드넘버
    """
    # 해당 회차 시점의 번호별 현재 주기(Skip Count) 계산
    # target_idx 가 분석할 회차라면, 그 이전 데이터들을 뒤져서 각 번호가 마지막으로 언제 나왔는지 찾음
    status_map = {}
    skip_durations = {} # 콜드번호용 스킵 주기 저장
    
    all_possible = list(range(1, 46))
    
    for n in all_possible:
        # target_idx 이후(과거) 데이터에서 번호 n이 나타나는 인덱스 찾기
        found_indices = df_raw.iloc[target_idx + 1:].index[
            (df_raw.iloc[target_idx + 1:]['n1'] == n) | 
            (df_raw.iloc[target_idx + 1:]['n2'] == n) | 
            (df_raw.iloc[target_idx + 1:]['n3'] == n) | 
            (df_raw.iloc[target_idx + 1:]['n4'] == n) | 
            (df_raw.iloc[target_idx + 1:]['n5'] == n) | 
            (df_raw.iloc[target_idx + 1:]['n6'] == n)
        ].tolist()
        
        if not found_indices:
            curr_skip = 999 # 한 번도 안 나온 경우
        else:
            # 현재 분석 회차(target_idx)와 마지막 출현 회차 사이의 간격
            curr_skip = found_indices[0] - (target_idx + 1)
        
        # 기준 적용
        if curr_skip == 0:
            status = "CARRY" # 이월수 (0주기)
        elif 1 <= curr_skip <= 3:
            status = "HOT"   # 핫 (1~3주기)
        elif 4 <= curr_skip <= 14:
            status = "MIDDLE" # 미들 (4~14주기)
        else:
            status = "COLD"   # 콜드 (15주기 이상)
            skip_durations[n] = curr_skip
            
        status_map[n] = status

    return status_map, skip_durations

def render_comprehensive_analysis(df_raw, display_count=20):
    st.header("📊 회차별 종합 분석 (주기별 분류)")
    
    # 범례 표시
    st.markdown("""
    <div style="margin-bottom:15px;">
        <span style="background-color:#FFD700; color:black; padding:2px 8px; border-radius:10px; font-weight:bold;">이월(0)</span>
        <span style="background-color:#FF4B4B; color:white; padding:2px 8px; border-radius:10px; font-weight:bold;">핫(1~3)</span>
        <span style="background-color:#AAAAAA; color:white; padding:2px 8px; border-radius:10px; font-weight:bold;">미들(4~14)</span>
        <span style="background-color:#1E90FF; color:white; padding:2px 8px; border-radius:10px; font-weight:bold;">콜드(15+)</span>
    </div>
    """, unsafe_allow_html=True)

    analysis_data = []
    
    for i in range(display_count):
        if i >= len(df_raw): break
        
        row = df_raw.iloc[i]
        curr_nums = [int(row[f'n{j}']) for j in range(1, 7)]
        
        # 당시 성격 및 콜드 스킵 주기 계산
        status_map, skip_durations = get_detailed_status(i, df_raw)
        
        balls_html = ""
        cold_skips = []
        
        for n in curr_nums:
            status = status_map.get(n)
            
            # 색상 매핑
            if status == "CARRY": bg = "#FFD700"; color = "black" # 이월(금색)
            elif status == "HOT": bg = "#FF4B4B"; color = "white" # 핫(빨강)
            elif status == "MIDDLE": bg = "#AAAAAA"; color = "white" # 미들(회색)
            else: 
                bg = "#1E90FF"; color = "white" # 콜드(파랑)
                # 콜드번호인 경우 해당 번호의 당시 스킵 주기를 기록
                skip_val = skip_durations.get(n, 15)
                cold_skips.append(f"{n}({skip_val}회)")
            
            ball_style = f"background-color:{bg}; color:{color}; padding:2px 8px; margin:2px; border-radius:12px; border:1px solid #777777; font-weight:bold; display:inline-block; font-size:13px;"
            balls_html += f'<span style="{ball_style}">{n}</span>'

        analysis_data.append({
            "회차": f"<b>{int(row['round'])}회</b>",
            "당첨번호 분석 (주기별)": balls_html,
            "이월수갯수": len([n for n in curr_nums if status_map[n] == "CARRY"]),
            "콜드스킵주기": ", ".join(cold_skips) if cold_skips else "-"
        })

    # 결과 테이블 렌더링
    final_df = pd.DataFrame(analysis_data)
    st.markdown(final_df.to_html(escape=False, index=False), unsafe_allow_html=True)
