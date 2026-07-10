import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from crazyLogic import get_crazy_analysis
from coldNum import get_cold_analysis
#from comprehensive_analysis import get_detailed_status
from combination_engine import get_group_v2

def data_input_func(conn, sheet_url, df, analyze_range):
    col_drw = st.number_input("회차", min_value=1, step=1)
    c = st.columns(6)
    n1 = c[0].number_input("No1", 1, 45, value=1)
    n2 = c[1].number_input("No2", 1, 45, value=2)
    n3 = c[2].number_input("No3", 1, 45, value=3)
    n4 = c[3].number_input("No4", 1, 45, value=4)
    n5 = c[4].number_input("No5", 1, 45, value=5)
    n6 = c[5].number_input("No6", 1, 45, value=6)
    bonus = st.number_input("Bonus", 1, 45, value=45)
        
    # [수정] 분석 엔진과 무결성을 위해 입력받은 번호를 즉시 오름차순 정렬
    current_nums = sorted([n1, n2, n3, n4, n5, n6])
    
    # 버튼 배치 (일반 버튼 st.button으로 변경)
    btn_col1, btn_col2 = st.columns(2)
    save_btn = btn_col1.button("💾 DB 저장하기", use_container_width=True)
    analyze_btn = btn_col2.button("🔍 조합 분석하기", use_container_width=True)
    
    if save_btn:
        data_to_save = {
            "round": int(col_drw), 
            "n1": current_nums[0], 
            "n2": current_nums[1], 
            "n3": current_nums[2], 
            "n4": current_nums[3], 
            "n5": current_nums[4], 
            "n6": current_nums[5], 
            "bonus": bonus
        }
        save_to_gsheet(conn, sheet_url, '시트1', data_to_save)
        # 기존에 캐싱된 로또 raw 데이터(df_raw 등)를 메모리에서 강제 삭제
        # (이렇게 해야 앱이 다시 켜질 때 구글 시트에서 최신 데이터를 처음부터 새로 긁어옵니다.)
        st.cache_data.clear()
        st.success(f"{col_drw}회차 데이터 저장 완료!")
        # 저장 직후 앱을 강제로 처음(상단)부터 다시 실행시켜 UI와 사이드바를 즉시 동기화
        st.rerun()
            
    if analyze_btn:
        st.divider()
        df_analysis, metrics = analyze_combination(current_nums, df, analyze_range)
                
        # 1. 개별 번호 상태 테이블(Crazy + Cold 엔진 결과)
        st.subheader("📊 번호별 정밀 지표")
        st.dataframe(df_analysis, use_container_width=True, hide_index=True)
                
        # 2. 조합 필터 (메트릭)
        st.subheader("⚙️ 조합 필터 검증")
        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        m_col1.metric("홀짝", metrics["홀짝"])
        m_col2.metric("총합", metrics["총합"])
        m_col3.metric("AC", metrics["AC"])
        m_col4.metric("고저(저:고)", metrics["고저"])
        m_col5.metric("연번", metrics["연번"])
    
        # 로우 데이터 컬럼 (한 줄 표시)
        st.code(f"분석 조합: {current_nums}")
        
        col_drw = 1     # 입력한 번호는 인덱스1번에만 저장
        data_to_save = {
            "round": int(col_drw), 
            "n1": current_nums[0], 
            "n2": current_nums[1], 
            "n3": current_nums[2], 
            "n4": current_nums[3], 
            "n5": current_nums[4], 
            "n6": current_nums[5], 
        }
        save_to_gsheet(conn, sheet_url, 'MyPickNums', data_to_save)
        # 기존에 캐싱된 로또 raw 데이터(df_raw 등)를 메모리에서 강제 삭제
        # (이렇게 해야 앱이 다시 켜질 때 구글 시트에서 최신 데이터를 처음부터 새로 긁어옵니다.)
        st.cache_data.clear()
        st.success("최종 예측 번호 조합 저장 완료!")
        # 저장 직후 앱을 강제로 처음(상단)부터 다시 실행시켜 UI와 사이드바를 즉시 동기화
        #st.rerun()
        
    df_raw = get_recent_data(conn, sheet_url, 'MyPickNums', count=1)
    if not df_raw.empty:
        latest_row = df_raw.iloc[0]
        picked_nums = [latest_row[f'n{i}'] for i in range(1, 7)]
        #status_map, _ = get_detailed_status(0, df)
        #balls_html = render_ball_ui(picked_nums, status_map, size=45)
        balls_html = render_ball_ui(picked_nums, size=45)
        st.markdown(balls_html, unsafe_allow_html=True)

def save_to_gsheet(conn, sheet_url, worksheet, new_data):
    """
    new_data: {'drwNo': 1110, 'num1': 3, ...} 형태의 딕셔너리
    """
    try:
        # 1. 기존 데이터 불러오기
        df = conn.read(spreadsheet=sheet_url, worksheet=worksheet, ttl=0)
    except Exception as e:
        st.warning(f"기존 데이터를 읽지 못했습니다: {e}")
        # 시트가 비어있을 경우 대비
        df = pd.DataFrame()

    if worksheet == 'MyPickNums':
        if df.empty or new_data['round'] == 1:
            new_data['round'] = 1   # 첫 데이터라면 1회차부터 시작
        else:
            last_round = df.iloc[0]['round']
            new_data['round'] = last_round + 1
            
    # 2. 새로운 데이터를 데이터프레임으로 변환
    new_df = pd.DataFrame([new_data])
    if not df.empty:
        # 기존 df가 있다면 컬럼 순서 맞추기
        new_df = new_df.reindex(columns=df.columns)
        
    # 3. 기존 데이터와 합치기 (중복 회차 제거 포함)
    if not df.empty:
        df = pd.concat([df, new_df], ignore_index=True)
        # 회차(drwNo)가 중복되면 마지막에 입력한 것으로 유지
        df = df.drop_duplicates(['round'], keep='last')
    else:
        df = new_df

    # 4. 회차(round) 기준 내림차순 정렬 (최신순)
    df = df.sort_values(by='round', ascending=False)
    
    # 5. 구글 시트 업데이트
    conn.update(spreadsheet=sheet_url, worksheet=worksheet, data=df)
    
    return df

@st.cache_data # 이 함수는 500개의 데이터를 한 번 가져오면 메모리에 저장해둡니다. 슬라이더를 움직여도 구글 시트에 다시 접속하지 않고 메모리에서 꺼내옵니다.
def get_recent_data(_conn, sheet_url, worksheet, count=0): # conn -> _conn 으로 변경
    """
    인자 앞에 '_'를 붙이면 Streamlit은 이 인자의 변화를 
    캐시 체크용 해시 계산에서 제외합니다.
    """
    # 함수 내부 로직...
    # (내부에서도 conn 대신 _conn을 사용하세요)
    # 예: sheet = _conn.open_by_url(url)
    try:
        # 1. 데이터 읽기
        df = _conn.read(spreadsheet=sheet_url, worksheet=worksheet, ttl=0)
        
        if df.empty:
            return pd.DataFrame()

        # 2. 회차순으로 정렬 (최신이 위로 오게)
        if 'round' in df.columns:
            df = df.sort_values(by='round', ascending=False)
        
        # 3. 인자(count)에 따라 데이터 자르기
        if count > 0:
            if worksheet == 'MyPickNums':
                df = df.tail(count)
            else:
                df = df.head(count) # 최근 count개만 가져옴
            
        # 숫자형 컬럼만 선택하여 정수로 변환
        # 로또 번호나 회차처럼 정수여야 하는 컬럼명을 리스트로 지정합니다.
        cols_to_int = ['round', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6']
        for col in cols_to_int:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(int)
                
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()
        
def analyze_combination(input_nums, df, analyze_range):
    """
    Crazy 엔진의 기술 지표와 Cold 엔진의 미출현 지표를 통합 분석
    """
    input_nums = sorted(input_nums)
    df_target = df.head(analyze_range).copy()
    
    # 1. 각 엔진 실행
    df_crazy = get_crazy_analysis(df_target) # 기술 지표용
    df_cold = get_cold_analysis(df_target)   # 콜드 지수용
    
    # 2. 데이터 타입 동기화 및 병합 (번호 컬럼 타입 일치 필수)
    df_crazy['번호'] = df_crazy['번호'].astype(int)
    df_cold['번호'] = df_cold['번호'].astype(int)
    df_total = pd.merge(df_crazy, df_cold, on="번호")
    
    # 3. 영문 컬럼명을 출력용 한글명으로 변경 (엔진 내부 컬럼명 기준)
    # get_crazy_analysis 결과에 맞춰 매핑
    rename_map = {
        'rebound_index': '반등지수',
        'energy_index': '에너지지수',
        'current_skip': '현재스킵',
        'avg_skip': '평균스킵',
        'last_skip': '직전스킵',
        'max_gap_record': '최대스킵', # 엔진에 max_skip이 없을 경우를 대비해 체크 필요
        'curr_streak': '현재연속',
        'max_streak': '최대연속',
        'streak_part': '연속점수'
    }
    df_total = df_total.rename(columns=rename_map)
    
    # 4. 입력된 6개 번호만 추출
    analysis_df = df_total[df_total['번호'].isin(input_nums)].copy()
    
    # 5. 이월수 여부 체크
    prev_nums = [df.iloc[0][f'n{i}'] for i in range(1, 7)]
    analysis_df['이월수'] = analysis_df['번호'].apply(lambda x: "✅" if x in prev_nums else "X")
    
    # 6. 최종 노출 컬럼 리스트 (KeyError 방지를 위해 실제 존재하는 것만 필터링)
    desired_cols = [
        '번호', '이월수', '반등지수', '에너지지수', '콜드지수',
        '평균스킵', '직전스킵', '현재스킵', '최대스킵', 
        '현재연속', '최대연속', '연속점수'
    ]
    # 실제 존재하는 컬럼만 선택
    available_cols = [c for c in desired_cols if c in analysis_df.columns]
    analysis_df = analysis_df[available_cols]

    # 7. 조합 전체 필터 지표 (홀짝, 총합, AC, 고저, 연번)
    total_sum = sum(input_nums)
    odd_cnt = len([n for n in input_nums if n % 2 != 0])
    high_cnt = len([n for n in input_nums if n >= 23])
    
    # AC 계산
    diffs = set()
    for i in range(len(input_nums)):
        for j in range(i + 1, len(input_nums)):
            diffs.add(abs(input_nums[i] - input_nums[j]))
    ac_value = len(diffs) - 5
    
    # 연번 계산
    consecutive = 0
    for i in range(5):
        if input_nums[i+1] - input_nums[i] == 1:
            consecutive += 1
            
    metrics = {
        "홀짝": f"{odd_cnt}:{6-odd_cnt}",
        "총합": total_sum,
        "AC": ac_value,
        "고저": f"{6-high_cnt}:{high_cnt}", # 저:고
        "연번": consecutive
    }
    
    return analysis_df, metrics

def render_ball_ui(nums, size):
    # 디자인 스타일 정의 (유지보수 용이)
    #size = 45 # 전체 크기 결정 (이 숫자만 바꾸면 공이 커지거나 작아짐)

    base_style = (
        f"width: {size}px; "
        f"height: {size}px; "
        f"line-height: {size}px; "
        "padding: 0; "
        f"margin: {size/9}px; "              # 공 사이 간격 
        "border-radius: 50%; "        # 50%는 항상 완벽한 원
        "text-align: center; "
        "display: inline-block; "
        "font-size: 16px; "           # 공 크기에 맞춰 글자 크기 조정
        "font-weight: bold; "
        "border: 2px solid #555; "    # 테두리
    )
    
    balls_html = '<div style="margin-top:15px; margin-bottom:15px;">'
    for n in nums:
        #status = status_map.get(n, "COLD")
        status = get_group_v2(n)
        # 상태별 컬러 매핑
        colors = {
            "이월수": ("#FFFFFF", "black", "2px solid #333"),
            "HOT": ("#FF4B4B", "white", "1px solid #777"),
            "MIDDLE": ("#FFD700", "black", "1px solid #777"),
            "COLD": ("#1E90FF", "white", "1px solid #777")
        }
        bg, color, border = colors.get(status, colors["UNKNOWN"])
        
        balls_html += f'<span style="{base_style} background-color:{bg}; color:{color}; border:{border};">{n}</span>'
    balls_html += '</div>'
    
    return balls_html
