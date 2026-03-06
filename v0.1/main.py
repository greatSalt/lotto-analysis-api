import streamlit as st
import pandas as pd
import random
import datetime

from streamlit_gsheets import GSheetsConnection
from into_lottoDB import save_to_gsheet  # 커스텀 모듈 임포트

# 설정 및 연결
st.set_page_config(page_title="로또 분석 프로 v0.1", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1q8P3SClxNSYsAXwBgk3__y44XxZwI_FTj-eE9uQeVHE/edit?gid=0#gid=0"

st.title("🎰 로또 당첨 패턴 분석기")
st.subheader("데이터 기반 번호 생성 시스템")

# 2. 사이드바 - 설정 메뉴
st.sidebar.header("🛠️ 분석 설정")
analysis_type = st.sidebar.radio(
    "분석 기법 선택",
    ("최근 빈도 분석", "홀짝 비율 최적화", "직전 회차 제외")
)

# 3. 로또 번호 생성 로직 (전문가 알고리즘 흉내)
def generate_lotto_numbers(strategy):
    # 실제로는 여기서 과거 데이터를 필터링하는 로직이 들어갑니다.
    # 지금은 기본 샘플로 구현합니다.
    base_numbers = list(range(1, 46))
    
    if strategy == "최근 빈도 분석":
        # 가상의 가중치 부여 (예: 최근 많이 나온 숫자에 확률 업)
        weights = [random.uniform(1, 2) for _ in range(45)]
        return sorted(random.choices(base_numbers, k=6)) # 중복 제거 로직 필요
    else:
        return sorted(random.sample(base_numbers, 6))

# 4. 메인 화면 구성
st.write(f"현재 선택된 전략: **{analysis_type}**")

# 사이드바 메뉴 만들기
st.sidebar.title("🎮 메뉴 선택")
menu = st.sidebar.radio("원하는 기능을 선택하세요", ["데이터 입력", "크레이지 번호 추출"])

# --- 1. 데이터 입력 화면 ---
if menu == "데이터 입력":
    st.title("📥 로또 데이터 입력")
    st.info("최신 회차의 당첨 번호를 입력하고 시트에 저장하세요.")
# 입력 UI 부분
    with st.form("lotto_input_form", clear_on_submit=True):
        col_drw = st.number_input("회차 입력", min_value=1, step=1)
        
        c = st.columns(6)
        n1 = c[0].number_input("No1", 1, 45)
        n2 = c[1].number_input("No2", 1, 45)
        n3 = c[2].number_input("No3", 1, 45)
        n4 = c[3].number_input("No4", 1, 45)
        n5 = c[4].number_input("No5", 1, 45)
        n6 = c[5].number_input("No6", 1, 45)
        # 보너스 번호 (한 줄 아래 별도로 배치)
        st.write("보너스 번호")
        bonus = st.number_input("Bonus", 1, 45)
        
        if st.form_submit_button("DB 저장하기"):
            # 데이터 묶기
            data_to_save = {
                "round": int(col_drw),
                "n1": n1, "n2": n2, "n3": n3,
                "n4": n4, "n5": n5, "n6": n6,
                "bonus": bonus  # 보너스 번호 추가!
            }
            
            # 모듈 함수 호출
            updated_df = save_to_gsheet(conn, SHEET_URL, data_to_save)
            
            st.success(f"{col_drw}회차 데이터가 최신순으로 저장되었습니다!")
            st.balloons()
            st.dataframe(updated_df.head(5)) # 상위 5개(최신순) 확인
# --- 2. 크레이지 번호 추출 화면 ---
elif menu == "크레이지 번호 추출":
    st.title("🔥 크레이지 번호 추출기")
    # 1. 분석 범위 선택 UI 추가 (사이드바 또는 메인화면)
    analyze_count = st.sidebar.number_input("분석할 최근 회차수 (0=전체)", min_value=0, value=10, step=5)
    
    # 2. 수정된 함수 호출 (입력받은 analyze_count 전달)
    df = get_recent_data(conn, SHEET_URL, count=analyze_count)
    
    if df.empty:
        st.warning("데이터가 없거나 불러오지 못했습니다.")
    else:
        label = f"최근 {len(df)}회차" if analyze_count > 0 else "전체 회차"
        st.write(f"📊 {label} 데이터를 바탕으로 분석 중입니다.")
        
        # 추출 로직 시작
        if st.button("🚀 크레이지 조합 생성"):

if st.button("✨ 분석 번호 추출하기"):
    with st.spinner('데이터 알고리즘 가동 중...'):
        result = generate_lotto_numbers(analysis_type)
        
        # 번호를 예쁜 원형 버튼 형태로 출력
        cols = st.columns(6)
        for i, num in enumerate(result):
            # 번호별 색상 지정 (로또 공식 색상 유사)
            color = "orange" if num <= 10 else "blue" if num <= 20 else "red" if num <= 30 else "gray" if num <= 40 else "green"
            cols[i].markdown(f"### :[{color}][{num}]")
            
    st.success(f"생성 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.balloons()

# 5. 데이터 시각화 (전문가 느낌 물씬)
st.divider()
st.write("📊 최근 5회차 당첨 번호 경향성 (샘플 데이터)")
chart_data = pd.DataFrame({
    '회차': ['1101회', '1102회', '1103회', '1104회', '1105회'],
    '평균값': [23, 19, 28, 21, 25]
})
st.line_chart(chart_data.set_index('회차'))

st.caption("본 프로그램은 통계적 재미를 위한 것이며, 당첨을 보장하지 않습니다.")

