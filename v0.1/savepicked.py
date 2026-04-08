import streamlit as st
import pandas as pd

def init_all_saved_data(conn, sheet_url):
    """앱 시작 시 구글 시트에서 PICK, FIX, EX 번호들을 모두 로드"""
    # 세션 상태가 하나라도 없으면 로드 시도
    if 'my_saved_picks' not in st.session_state or 'fixed_nums' not in st.session_state:
        try:
            # ttl=0으로 설정하여 항상 최신 데이터를 읽어옴
            df = conn.read(spreadsheet=sheet_url, worksheet="SavedPicks", ttl=0)
            
            if not df.empty:
                # 1. '유형' 컬럼이 아예 없는 기존 시트인 경우 대응
                if '유형' not in df.columns:
                    set_default_session_values()
                    # 모든 기존 번호를 일단 'PICK'(일반 저장)으로 간주
                    st.session_state.my_saved_picks = df['번호'].tolist()
                else:
                    # 2. '유형' 컬럼이 있는 경우 정상 분류
                    # 1. 일반 저장 번호 (PICK)
                    st.session_state.my_saved_picks = get_list_by_type(df, 'PICK')
                    # 2. 고정수 (FIX)
                    st.session_state.fixed_nums = get_list_by_type(df, 'FIX')
                    # 3. 제외수 (EX)
                    st.session_state.exclude_nums = get_list_by_type(df, 'EX')
                    # 2. 신규 필터 설정값 로드
                    # [AC값]
                    st.session_state.sel_ac = get_safe_int(df, 'F_AC', 7)
                    
                    # [최대 연번]
                    st.session_state.sel_con = get_safe_int(df, 'F_CON', 1)
                    
                    # [고저 비율 리스트]
                    hl_rows = df[df['유형'] == 'F_HL']
                    st.session_state.sel_hl = hl_rows['번호'].tolist() if not hl_rows.empty else ["3:3", "2:4", "4:2"]
                    
                    # [총합 범위]
                    sum_rows = df[df['유형'] == 'F_SUM']
                    if not sum_rows.empty:
                        try:
                            sums = [int(float(x)) for x in sum_rows['번호'].tolist()]
                            # 슬라이더 범위(80~200)를 벗어나지 않도록 보정
                            s_min = max(80, sums[0])
                            s_max = min(200, sums[1])
                            st.session_state.sum_range = (s_min, s_max)
                        except:
                            st.session_state.sum_range = (100, 175)
                    else:
                        st.session_state.sum_range = (100, 175)
            else:
                # 시트가 비어있을 때
                set_default_session_values()
                
        except Exception:
            # 시트가 없거나 오류 발생 시 빈 리스트로 안전하게 초기화
            set_default_session_values()

def get_safe_int(df, type_code, default_val):
    """구글 시트 데이터프레임에서 특정 유형의 정수값을 안전하게 추출"""
    row = df[df['유형'] == type_code]
    if not row.empty:
        try:
            # "7.0" 같은 문자열 대응을 위해 float -> int 변환
            return int(float(row['번호'].iloc[0]))
        except:
            return default_val
    return default_val

def get_list_by_type(df, t_code):
    """특정 유형의 번호들을 리스트로 추출 (정수형 변환 포함)"""
    selected = df[df['유형'] == t_code]['번호'].tolist()
    try:
        # 숫자로 변환 가능한 것만 정수로 바꿔서 리스트 생성
        return [int(float(x)) for x in selected if x and str(x).replace('.','').isdigit()]
    except:
        return selected

def set_default_session_values():
    """기본값 초기화 헬퍼 함수"""
    st.session_state.my_saved_picks = []
    st.session_state.fixed_nums = []
    st.session_state.exclude_nums = []
    st.session_state.sel_ac = 7
    st.session_state.sel_con = 1
    st.session_state.sel_hl = ["3:3", "2:4", "4:2"]
    st.session_state.sum_range = (100, 175)

'''
def init_saved_picks(conn, sheet_url):
    """앱 시작 시 구글 시트에서 저장된 번호를 불러오기"""
    if 'my_saved_picks' not in st.session_state:
        try:
            df = conn.read(spreadsheet=sheet_url, worksheet="SavedPicks", ttl=0)
            if not df.empty:
                st.session_state.my_saved_picks = df['번호'].tolist()
            else:
                st.session_state.my_saved_picks = []
        except Exception:
            st.session_state.my_saved_picks = []
'''
'''
def save_special_picks(conn, sheet_url, new_picks, type_code="PICK"):
    """
    유형별(PICK, FIX, EX)로 번호를 구글 시트에 저장
    type_code: 'PICK'(일반), 'FIX'(고정), 'EX'(제외)
    """
    try:
        # 1. 기존 데이터 전체 읽기
        try:
            existing_df = conn.read(spreadsheet=sheet_url, worksheet="SavedPicks")
        except:
            existing_df = pd.DataFrame(columns=["번호", "유형"])

        # 2. 해당 유형의 기존 데이터 삭제 후 새로운 데이터로 교체 (유형별 업데이트)
        other_types_df = existing_df[existing_df["유형"] != type_code]
        new_type_df = pd.DataFrame({"번호": new_picks, "유형": type_code})
        
        updated_df = pd.concat([other_types_df, new_type_df]).drop_duplicates().sort_values(["유형", "번호"])

        # 3. 시트 업데이트
        conn.update(spreadsheet=sheet_url, worksheet="SavedPicks", data=updated_df)
        st.toast(f"✅ {type_code} 번호가 시트에 저장되었습니다!")
        
    except Exception as e:
        st.error(f"저장 실패: {e}")
'''
'''
def save_picks_to_sheets(conn, sheet_url, new_picks):
    """기존 번호를 유지하며 구글 시트에 누적 저장"""
    try:
        # 1. 기존에 저장된 데이터 읽기 시도
        try:
            existing_df = conn.read(spreadsheet=sheet_url, worksheet="SavedPicks")
            existing_picks = existing_df["번호"].tolist()
        except:
            # 시트가 비어있거나 오류가 나면 빈 리스트로 시작
            existing_picks = []

        # 2. 기존 번호 + 새로운 번호 합치기 (set을 사용하여 중복 제거)
        updated_picks = list(set(existing_picks + new_picks))
        updated_picks.sort() # 보기 좋게 정렬
        
        # 3. 데이터프레임 생성 및 업데이트
        df = pd.DataFrame({"번호": updated_picks})
    
        conn.update(spreadsheet=sheet_url, worksheet="SavedPicks", data=df)
        st.session_state.my_saved_picks = updated_picks
        st.toast("✅ 기존 번호와 합쳐져 안전하게 저장되었습니다!")
        
        return True
        
    except Exception as e:
        st.error(f"저장 실패: {e}")
        return False
'''
def save_to_sheets_by_type(conn, sheet_url, new_nums, type_code):
    """
    type_code: 'PICK', 'FIX', 'EX' 중 하나
    해당 유형의 번호들을 시트에 업데이트
    """
    try:
        # 기존 전체 데이터 읽기
        try:
            full_df = conn.read(spreadsheet=sheet_url, worksheet="SavedPicks", ttl=0)
        except:
            full_df = pd.DataFrame(columns=["번호", "유형"])
        # [중요] '유형' 컬럼이 없는 기존 시트라면 강제로 생성
        if '유형' not in full_df.columns:
            full_df['유형'] = 'PICK' # 기존 데이터는 모두 일반 저장으로 간주
            
        # 1. 다른 유형의 데이터는 그대로 유지
        other_types_df = full_df[full_df["유형"] != type_code]
        
        # 2. 현재 요청된 유형의 데이터 새로 생성
        new_type_df = pd.DataFrame({"번호": new_nums, "유형": type_code})
        
        # 3. 합치기 및 중복 제거
        final_df = pd.concat([other_types_df, new_type_df]).drop_duplicates().sort_values(["유형", "번호"])

        # 4. 시트 업데이트
        conn.update(spreadsheet=sheet_url, worksheet="SavedPicks", data=final_df)
        
        # 5. 세션 상태도 즉시 동기화
        if type_code == 'PICK': st.session_state.my_saved_picks = new_nums
        elif type_code == 'FIX': st.session_state.fixed_nums = new_nums
        elif type_code == 'EX': st.session_state.exclude_nums = new_nums
         # 신규 필터 설정 동기화
        elif type_code == 'F_AC': st.session_state.sel_ac = int(new_nums[0])
        elif type_code == 'F_CON': st.session_state.sel_con = int(new_nums[0])
        elif type_code == 'F_HL': st.session_state.sel_hl = new_nums # ['3:3', '4:2'] 형태
        elif type_code == 'F_SUM': st.session_state.sum_range = (int(new_nums[0]), int(new_nums[1]))
        
        st.toast(f"✅ {type_code} 설정이 저장되었습니다.")
        #st.rerun() # UI 즉시 갱신
        
    except Exception as e:
        st.error(f"저장 중 오류 발생: {e}")

def display_sidebar_picks(conn, sheet_url):
    """사이드바 표시 및 관리"""
    with st.sidebar:
        st.divider()
        st.markdown("### 🎯 My Lucky Picks")
        
        if st.session_state.my_saved_picks:
            picks = sorted(st.session_state.my_saved_picks)
            cols = st.columns(3)
            for i, num in enumerate(picks):
                cols[i % 3].info(f"**{num}**")
            
            # 리셋 시에도 시트와 동기화되도록 sheet_url 전달
            if st.button("🔄 Reset & Sync", use_container_width=True):
                save_picks_to_sheets(conn, sheet_url, []) 
                st.rerun()
        else:
            st.caption("저장된 번호가 없습니다.")
        st.divider()

def get_highlight_style(row):
    """표의 스타일 결정 (노란색 임계점 우선 적용)"""
    base_style = ''
    
    try:
        # 1. 우선순위 1: 노란색 (임계점 도달) - 가장 중요함
        if '직전스킵' in row and '평균스킵' in row:
            skip_diff = abs(row['직전스킵'] - row['평균스킵'])
            if skip_diff <= 1:
                base_style = 'background-color: #FFD700; color: #000000;' # 노랑
            
            # 2. 우선순위 2: 빨간색 (에너지 응축) - 노란색이 아닐 때만 적용
            elif row['직전스킵'] > row['평균스킵']:
                base_style = 'background-color: #FF4B4B; color: #FFFFFF;' # 빨강

        # 3. 우선순위 3: 파란색 (방금 출현) - 노랑/빨강이 모두 아닐 때만 적용
        # 이렇게 else/elif 구조를 타야 노란색이 파란색에 먹히지 않습니다.
        if base_style == '' and '현재연속' in row and row['현재연속'] == 0:
            base_style = 'background-color: #1E90FF; color: #FFFFFF;' # 파랑
            
    except Exception:
        pass

    # 4. [핵심] 내 번호 강조 (어떤 배경색 위에서도 굵게 표시)
    if 'my_saved_picks' in st.session_state:
        if row['번호'] in st.session_state.my_saved_picks:
            # !important를 추가하여 테두리가 다른 스타일에 밀리지 않게 강조
            base_style += ' font-weight: 900; font-size: 1.15em; border: 2.5px solid #000000 !important;'
    
    return [base_style] * len(row)
