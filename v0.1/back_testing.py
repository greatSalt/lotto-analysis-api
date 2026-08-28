import streamlit as st
import pandas as pd
from collections import Counter

from comprehensive_analysis import get_detailed_status
from into_lottoDB import render_ball_ui, get_recent_data
from empty_zone_engine import get_empty_finder
from combination_engine import get_group_v2

def bt_main_func(conn, sheet_url, df_raw):
    selection_menu = bt_sel_func()
    
    if selection_menu == "이월수 예측":
        st.subheader("🧪 이월수 예측 백테스팅")
        # run_carryover_backtest() 호출
        pass
    elif selection_menu == "멸구간 예측":
        st.subheader("🧪 멸구간 예측 백테스팅")
        run_empty_zone_backtest(df_raw, count=25) 
    elif selection_menu == "보너스 번호의 이월확률":
        run_bonus_carry_backtest(df_raw, count=50)
    elif selection_menu == "조합 시험":
        run_combination_backtest(conn, sheet_url)
    else:
        pass
    
def bt_sel_func():
    col1, _ = st.columns(2)
    with col1: 
        func_options = ["선택 안 함", "이월수 예측",  "멸구간 예측", "보너스 번호의 이월확률", "조합 시험"]
        
        # 1. 세션 스테이트 초기화 (존재하지 않을 때만)
        if 'f_opt' not in st.session_state:
            st.session_state.f_opt = "선택 안 함"
        
        # 2. 안전한 인덱스 계산 (데이터 검증 포함)
        current_val = st.session_state.f_opt
        # 현재 값이 리스트에 없으면 기본값(0) 사용
        target_index = func_options.index(current_val) if current_val in func_options else 0
        
        # 3. 위젯 설정
        st.selectbox(
            "Back Testing",    
            options=func_options,
            index=target_index,
            key='f_opt'
        )
                    
    st.divider()
    return st.session_state.f_opt
    
def run_empty_zone_backtest(df_raw, count=50):
    
    # 멸구간 정의 및 컬럼 설정
    zones = {
        "단번대": lambda n: 1 <= n <= 9,
        "10번대": lambda n: 10 <= n <= 19,
        "20번대": lambda n: 20 <= n <= 29,
        "30번대": lambda n: 30 <= n <= 39,
        "40번대": lambda n: 40 <= n <= 45
    }
    #num_cols = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']
    
    results = []
    #all_detected_empty_zones = [] # 통계용 리스트
    empty_patterns = [] # 회차별 멸구간 조합(패턴)을 담을 리스트
    
    if not df_raw.empty:
        target_rows = df_raw.head(count).astype(int)
        for idx in range(len(target_rows)):
            row = target_rows.iloc[idx]
            round_num = row['round']
            picked_nums = [row[f'n{i}'] for i in range(1, 7)]
            
            # 👇 [추가] 보너스 번호 가져오기 (컬럼명이 다르면 수정하세요)
            bonus_num = int(row['bonus']) 
            
            # 👇 [수정] 보너스 번호가 포함된 구간은 멸구간에서 제외되도록 합쳐서 검사
            check_nums = picked_nums + [bonus_num]
            
            emptyzones = get_empty_finder(check_nums, zones)   # 멸구간 찾기

            # 👇 멸구간 조합 패턴을 튜플로 저장 (순서 상관없이 비교하기 위해 정렬)
            pattern_tuple = tuple(sorted(emptyzones))
            empty_patterns.append(pattern_tuple)
            # 👇 [추가] 이번 회차 멸구간들을 통계용 리스트에 누적
            #all_detected_empty_zones.extend(emptyzones)
            
            status_map, _ = get_detailed_status(idx, df_raw)
            ball_html = render_ball_ui(picked_nums, status_map, size=20)

            # 보너스 번호 공 색상 판별 로직 (로또 번호 색상 규칙 적용)
            if bonus_num <= 10: b_bg = "#fbc400"; b_color = "#000"
            elif bonus_num <= 20: b_bg = "#69c2ff"; b_color = "#000"
            elif bonus_num <= 30: b_bg = "#ff7272"; b_color = "#fff"
            elif bonus_num <= 40: b_bg = "#aaaaaa"; b_color = "#fff"
            else: b_bg = "#b0d840"; b_color = "#000"

            # 동그란 로또 공 모양 HTML 생성 (보너스 표시용)
            bonus_ball_html = f'<span style="display:inline-block; width:22px; height:22px; line-height:22px; text-align:center; border-radius:50%; background-color:{b_bg}; color:{b_color}; font-weight:bold; font-size:11px; margin-left:6px; box-shadow: inset -1px -1px 2px rgba(0,0,0,0.3);">{bonus_num}</span>'
            
            # 당첨 번호 공들 뒤에 깔끔하게 보너스 공 추가 (+ '보너스:' 글자 생략하고 직관적으로 배치)
            ball_html += f" &nbsp;|&nbsp; <span style='font-size:11px; color:#555;'>보너스:</span> {bonus_ball_html}"
            
            results.append({
                "회차": row['round'],
                "당첨 번호 구성": ball_html, # 여기에 공 UI 삽입
                "멸구간": ", ".join(emptyzones) if emptyzones else "없음"
            })
    
        df_result = pd.DataFrame(results)

        # --- 5. 멸구간 조합(쌍, 단독 등)별 확률 및 빈도 계산 ---
        total_cnt = len(target_rows)
        pattern_counts = Counter(empty_patterns)
        
        stats_rows = []
        # 빈도가 높은 순서대로 정렬하여 통계 생성
        for pattern, freq in pattern_counts.most_common():
            pattern_name = ", ".join(pattern) if pattern else "멸구간 없음 (완벽 분산)"
            probability = (freq / total_cnt) * 100 if total_cnt > 0 else 0
            
            stats_rows.append({
                "멸구간 조합 패턴": pattern_name,
                "발생 횟수": f"{freq}회",
                "출현 확률": f"{probability:.1f}%"
            })
            
        df_stats = pd.DataFrame(stats_rows)

        # --- 6. Streamlit 출력 ---
        st.subheader(f"📊 최근 {total_cnt}회차 멸구간 백테스트 결과")
        st.write(df_result.to_html(escape=False, index=False), unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("📈 멸구간 조합(단독/쌍)별 발생 확률 통계")
        st.dataframe(df_stats, use_container_width=True)
        
def run_bonus_carry_backtest(df_raw, count=25):
    
    results = []
    if not df_raw.empty:
        target_rows = df_raw.head(count).astype(int)
        for idx in range(len(target_rows)):
            row = target_rows.iloc[idx]
            round_num = row['round']
            picked_nums = [row[f'n{i}'] for i in range(1, 7)]
            status_map, _ = get_detailed_status(idx, df_raw)
            ball_html = render_ball_ui(picked_nums, status_map, size=20)
            
            bonus_num = [row['bonus']]
            bonus_ball_html = render_ball_ui(bonus_num, status_map, size=20)
            
            # 이월 확인 로직
            carry_text = "-"
            if idx + 1 < len(df_raw):
                # target_rows 대신 전체 df_raw에서 참조하는 것이 안전
                pre_bonus_num = int(df_raw.iloc[idx + 1]['bonus']) #이전 회차의 보너스 번호
                is_carry = pre_bonus_num in picked_nums
                
                # 시각적 강조를 위한 HTML 적용
                if is_carry:
                    carry_text = '<span style="color:#FF4B4B; font-weight:bold;">✅ 이월</span>'
                else:
                    carry_text = '<span style="color:#CCCCCC;">❌ </span>'
                
            devitation_table = run_bonus_devitation_table(idx, df_raw)
            stat = devitation_table[0]
                            
            results.append({
                "회차": row['round'],
                "당첨 번호 구성": ball_html, # 여기에 공 UI 삽입
                "보너스번호": bonus_ball_html,
                "보너스번호 이월": carry_text,
                "25주 확률": stat['25주 확률'],
                "4주 확률": stat['4주 확률'],
                "확률 편차": stat['확률 편차']
            })
    
        #df_table = pd.DataFrame(devitation_table)
        df_result = pd.DataFrame(results)
        
        # Streamlit에서 HTML 표 출력 (unsafe_allow_html=True 필수)
        #st.write(df_table.to_html(escape=False, index=False), unsafe_allow_html=True)
        st.write(df_result.to_html(escape=False, index=False), unsafe_allow_html=True)
    
def run_bonus_devitation_table(idx, df_raw):
    
    df_25 = df_raw[idx:idx+25].astype(int)
    
    sum_4 = sum_25 = 0
    devitation_table = []
    # 분모는 실제 루프가 돈 횟수(데이터 길이 - 1) 기준
    n_count = len(df_25) - 1
    
    for n in range(n_count):
        row = df_25.iloc[n]
        picked_nums = [row[f'n{i}'] for i in range(1, 7)]
        pre_bonus_num = int(df_25.iloc[n + 1]['bonus']) #이전 회차의 보너스 번호
        is_carry = pre_bonus_num in picked_nums
        
        if is_carry:
            if n < 4: sum_4 += 1
            sum_25 += 1
            
    devitation_25 = sum_25 / n_count * 100
    devitation_4 = sum_4 / 4.0 * 100
    devitation_res = devitation_25 - devitation_4
    
    devitation_table.append({
        "25주 확률" : f"{devitation_25:.1f}%",
        "4주 확률" : f"{devitation_4:.1f}%",
        "확률 편차" : f"{devitation_res:.1f}%"
    })     
    
    return devitation_table

def run_combination_backtest(conn, sheet_url):
    # 비교할 당첨번호 google sheet에서 불러오기
    df_raw = get_recent_data(conn, sheet_url, 'UserPickNums', count=1)
    if not df_raw.empty:
        latest_row = df_raw.iloc[0]
        try:
            picked_nums = [int(float(latest_row[f'n{i}'])) for i in range(1, 7)]
        except (KeyError, ValueError, TypeError):
            picked_nums = [1, 2, 3, 4, 5, 6] # 데이터 파싱 중 에러 발생 시 기본값
    else:
        picked_nums = [1,2,3,4,5,6]
        
    # 비교할 당첨번호 입력 및 비교 시작 버튼
    col_drw = st.number_input("회차", min_value=1, step=1)
    c = st.columns(6)
    n1 = c[0].number_input("No1", 1, 45, value=picked_nums[0])
    n2 = c[1].number_input("No2", 1, 45, value=picked_nums[1])
    n3 = c[2].number_input("No3", 1, 45, value=picked_nums[2])
    n4 = c[3].number_input("No4", 1, 45, value=picked_nums[3])
    n5 = c[4].number_input("No5", 1, 45, value=picked_nums[4])
    n6 = c[5].number_input("No6", 1, 45, value=picked_nums[5])
    
    winning_nums = set([n1, n2, n3, n4, n5, n6])
    
    # 버튼 및 전체선택 토글 배치 
    btn_col1, btn_col2 = st.columns([0.3, 0.7])
    compare_btn = btn_col1.button("당첨확인", use_container_width=True)
    
    # 100개 조합 데이터가 존재할 때만 실행
    if 'backtest_target_results' in st.session_state and st.session_state.backtest_target_results:
        target_100_combos = st.session_state.backtest_target_results
        
        # [신규 기능] 전체 선택/해제 토글 스위치 (세션 스테이트로 상태 유지)
        if 'select_all_backtest' not in st.session_state:
            st.session_state.select_all_backtest = False
            
        select_all = st.checkbox("☑ 전체 선택 / 해제", value=st.session_state.select_all_backtest, key="select_all_toggle")
        if select_all != st.session_state.select_all_backtest:
            st.session_state.select_all_backtest = select_all
            st.rerun() # 전체 선택 상태 변경 시 즉시 반영

        st.write(f"현재 백테스팅 대상: 총 {len(target_100_combos)}개 조합")
        st.divider()        
        
        to_save_MyPickNums = []  
        match_stats = {3: 0, 4: 0, 5: 0, 6: 0, "낙첨": 0} # 통계용
                            
        for i, combo_data in enumerate(target_100_combos):
            combo_nums = sorted([n for n, group in combo_data])
            combo_set = set(combo_nums)
            
            # 당첨 번호와 비교 (맞춘 개수 확인)
            matched = combo_set.intersection(winning_nums)
            match_count = len(matched)
            
            # 당첨/낙첨 텍스트 및 스타일 결정 (문자열 깨짐 방지 구조)
            if match_count >= 3:
                color_code = "#FF4B4B"
                status_label = "당첨"
                icon = "🎉"
                if match_count in match_stats: 
                    match_stats[match_count] += 1
            else:
                color_code = "#888888"
                status_label = "낙첨"
                icon = "❌"
                match_stats["낙첨"] += 1

            # HTML 태그를 깔끔하게 조립
            result_text = f"<span style='color:{color_code}; font-weight:bold;'>{icon} {match_count}개 일치 ({status_label})</span>"

            col_chk, col_label, col_balls, col_result = st.columns([0.08, 0.12, 0.55, 0.25])
            
            # 1. 체크박스: 전체 선택 상태와 개별 상태 연동
            with col_chk:
                # 전체선택이 체크되어 있으면 기본값을 True로 설정
                chk_key = f"chk_backtest_{i}"
                if select_all and chk_key not in st.session_state:
                    st.session_state[chk_key] = True
                
                is_checked = st.checkbox("", key=chk_key)
                if is_checked:
                    to_save_MyPickNums.append((combo_nums, match_count))
                            
            with col_label:
                st.markdown(f"**SET {i+1}**")
                                    
            # 2. 번호별 색상 배지 (공 UI)
            with col_balls:
                ball_html = "<div style='display: flex; gap: 4px; flex-wrap: wrap;'>"
                for n, group in combo_data:
                    if group == '이월수': color = "white"   # ⬜ 이월수 (흰색 배경 + 검정 글자)
                    elif group == 'HOT': color = "red"      # 🟥 핫 (빨간색)
                    elif group == 'WARM': color = "yellow"  # 🟨 웜 (노란색/골드)
                    elif group == 'COLD': color = "blue"    # 🟦 콜드 (파란색)
                    else: color = "lightgrey"               # 데이터 오류 시 회색
                                    
                    ball_html += f"<img src='https://img.shields.io/badge/-{n}-{color}?style=flat-square&border_radius=50' style='margin-bottom:4px;'>"
                ball_html += "</div>"
                st.markdown(ball_html, unsafe_allow_html=True)
                
            # 3. 당첨 결과 출력
            with col_result:
                st.markdown(result_text, unsafe_allow_html=True)
                            
        st.divider()
        
        # [신규 기능] 하단 저장 버튼 및 요약 통계
        save_col1, save_col2 = st.columns([0.4, 0.6])
        with save_col1:
            save_btn = st.button("💾 체크된 조합 MyPickNums 저장", use_container_width=True)
            
        with save_col2:
            st.markdown(f"📊 **결과 요약**: 3개 맞춤: {match_stats[3]}개 | 4개 맞춤: {match_stats[4]}개 | 5개 맞춤: {match_stats[5]}개 | 6개 맞춤: {match_stats[6]}개")

        # 당첨 확인 버튼 동작 (필요시 알림이나 추가 요약용)
        if compare_btn:
            st.success(f"🔍 {col_drw}회차 기준 당첨 확인이 완료되었습니다! (위 결과를 확인하세요)")

        # 체크된 조합번호를 MyPickNums 시트에 저장하는 로직
        if save_btn:
            if not to_save_MyPickNums:
                st.warning("⚠️ 저장할 조합이 선택되지 않았습니다. 체크박스를 선택해주세요.")
            else:
                try:
                    # 1. 기존 'MyPickNums' 시트 데이터를 읽어옴
                    try:
                        existing_df = conn.read(spreadsheet=sheet_url, worksheet="MyPickNums", ttl=0)
                    except:
                        existing_df = pd.DataFrame()

                    # 2. 기존 데이터에 '일치개수' 컬럼이 없다면 안전하게 추가
                    if not existing_df.empty:
                        if "일치개수" not in existing_df.columns:
                            existing_df["일치개수"] = "" # 기존 데이터는 빈칸으로 채움

                    # 3. 새로 추가할 데이터들을 리스트 형태로 만듦
                    new_rows = []
                    for combo, m_cnt in to_save_MyPickNums:
                        new_rows.append({
                            "round": int(col_drw), 
                            "n1": combo[0], 
                            "n2": combo[1], 
                            "n3": combo[2], 
                            "n4": combo[3], 
                            "n5": combo[4], 
                            "n6": combo[5], 
                            "일치개수": f"{m_cnt}개 일치"
                        })
                    
                    new_df = pd.DataFrame(new_rows)

                    # 5. conn.update로 시트에 통째로 덮어쓰기
                    conn.update(
                        spreadsheet=sheet_url,
                        worksheet="MyPickNums",
                        data=new_df
                    )
                    
                    # 6. 캐시 비우기 및 완료 메시지
                    st.cache_data.clear()
                    st.success(f"✅ 총 {len(new_rows)}개의 조합이 'MyPickNums' 시트에 안전하게 추가되었습니다!")
                    
                except Exception as e:
                    st.error(f"❌ 구글 시트 저장 중 오류 발생: {e}")

        # 100개 조합 출력 하단에 빈도 분석 함수 호출
        render_combination_frequency_table(target_100_combos, winning_nums)
    else:
        st.info("먼저 조합 생성 메뉴에서 '100개 조합 생성' 버튼을 눌러주세요.")

def loaded_combination_data_to_gsheet(conn, SHEET_URL):
    # --- 앱 최초 실행 시 구글 시트 'MyPickNums'의 2행부터 저장된 조합 불러오기 ---
    if 'backtest_target_results' not in st.session_state:
        try:
            # MyPickNums 시트 읽기
            df_mypick = conn.read(spreadsheet=SHEET_URL, worksheet="MyPickNums", ttl=0)
            
            if not df_mypick.empty and all(col in df_mypick.columns for col in ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']):
                loaded_combos = []
                
                # 2행부터 끝까지(100개 조합) 안전하게 순회합니다.
                for _, row in df_mypick.iloc[0:].iterrows():
                    # n1 값이 숫자인지 확인 (NaN이거나 공백이면 데이터가 없는 것으로 간주)
                    try:
                        just_nums = [
                            int(float(row['n1'])), int(float(row['n2'])), int(float(row['n3'])), 
                            int(float(row['n4'])), int(float(row['n5'])), int(float(row['n6']))
                        ]
                    except (ValueError, TypeError):
                        continue # 숫자가 아니면 다음 행으로 패스
                    
                    # 그룹 함수로 재조립하여 리스트에 담기
                    full_combo = [[n, get_group_v2(n)] for n in just_nums]
                    loaded_combos.append(full_combo)
                
                st.session_state.backtest_target_results = loaded_combos
            else:
                st.session_state.backtest_target_results = []
        except Exception as e:
            st.session_state.backtest_target_results = []

def render_combination_frequency_table(target_100_combos, winning_nums=None):
    """
    100개 조합 내 번호별 출현 빈도를 분석하여 표로 출력하고, 
    비교할 번호(winning_nums)가 포함된 행은 하이라이트 처리합니다.
    """
    if not target_100_combos:
        st.info("분석할 조합 데이터가 없습니다.")
        return

    # 1. 모든 조합에 포함된 번호들을 하나의 리스트로 추출
    all_extracted_nums = []
    for combo_data in target_100_combos:
        for item in combo_data:
            n = item[0] if isinstance(item, list) else item
            all_extracted_nums.append(int(n))
            
    # 2. 번호별 개수 카운트
    num_counts = Counter(all_extracted_nums)
    
    # 3. 1부터 45번까지 누락 없이 데이터프레임 구성
    freq_data = []
    for num in range(1, 46):
        freq_data.append({
            "번호": num, 
            "출현 횟수": num_counts.get(num, 0)
        })
        
    df_freq = pd.DataFrame(freq_data)
    
    # 4. 출현 횟수 기준 내림차순 정렬 (횟수가 같으면 번호 오름차순)
    df_freq = df_freq.sort_values(by=['출현 횟수', '번호'], ascending=[False, True]).reset_index(drop=True)
    
    # 5. 하이라이트 스타일 적용 함수
    if winning_nums is None:
        winning_nums = set()

    def highlight_winning_row(row):
        # '번호' 컬럼 값이 비교 번호 세트에 포함되어 있다면 배경색 강조 (예: 연한 노란색/주황색)
        if int(row['번호']) in winning_nums:
            return ['background-color: #FFF2CC; font-weight: bold; color: #D9534F;'] * len(row)
        return [''] * len(row)

    # 6. UI 출력
    st.divider()
    st.subheader("🔥 100개 조합 번호별 출현 빈도 TOP 45")
    st.caption("현재 생성된 100개의 조합 안에서 각 번호가 사용된 총 횟수입니다. (비교 번호는 색상으로 강조됩니다)")
    
    # Styler를 적용하여 데이터프레임 출력
    styled_df = df_freq.style.apply(highlight_winning_row, axis=1)
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
