import streamlit as st
import pandas as pd

def init_all_saved_data(conn, sheet_url):
    """앱 시작 시 구글 시트에서 PICK, FIX, EX 번호들을 모두 로드"""
    # 세션 상태가 하나라도 없으면 로드 시도
    if 'my_saved_picks' not in st.session_state or 'fixed_nums' not in st.session_state:
        try:
            # ttl=0으로 설정하여 항상 최신 데이터를 읽어옴
            df = conn.read(spreadsheet=sheet_url, worksheet="SavedPicks", ttl=0)
            set_default_session_values()
            
            if not df.empty:
                # 1. '유형' 컬럼이 아예 없는 기존 시트인 경우 대응
                if '유형' not in df.columns:
                    # 모든 기존 번호를 일단 'PICK'(일반 저장)으로 간주
                    st.session_state.my_saved_picks = df['번호'].tolist()
                else:
                    # 1. 개별 선택 번호 (PICK) -> 단일 리스트로 저장
                    st.session_state.my_saved_picks = df[df['유형'] == 'PICK']['번호'].tolist()
                    
                    # 2. 추천 조합 번호 (COMBI) -> 6개씩 묶어서 '리스트의 리스트'로 저장
                    combi_raw = df[df['유형'] == 'COMBI']['번호'].tolist()
                    
                    st.session_state.my_combi_sets = [combi_raw[i:i+6] for i in range(0, len(combi_raw), 6) if len(combi_raw[i:i+6]) == 6]
                    # 3. 고정수 (FIX)
                    st.session_state.fixed_nums = get_list_by_type(df, 'FIX')
                    # 4. 제외수 (EX)
                    st.session_state.exclude_nums = get_list_by_type(df, 'EX')
                    # 5. 신규 필터 설정값 로드
                    #[홀짝]
                    # [홀짝 비율 리스트]
                    oe_rows = df[df['유형'] == 'F_OE']
                    st.session_state.sel_oe = oe_rows['번호'].tolist() if not oe_rows.empty else ["3:3", "2:4", "4:2"]
                    
                    # [AC값]
                    st.session_state.sel_ac = get_safe_int(df, 'F_AC', 7)
                        
                    # [최대 연번]
                    st.session_state.sel_con = get_safe_int(df, 'F_CON', 1)
                        
                    # [고저 비율 리스트]
                    hl_rows = df[df['유형'] == 'F_HL']
                    st.session_state.sel_hl = hl_rows['번호'].tolist() if not hl_rows.empty else ["3:3", "2:4", "4:2"]
                    
                    # [동끝수 쌍 개수 리스트]
                    end_rows = df[df['유형'] == 'F_END']
                    st.session_state.sel_end = [int(float(x)) for x in end_rows['번호'].tolist()] if not end_rows.empty else [1, 2]
                    
                    # [지정 특정 끝수 리스트]
                    target_end_rows = df[df['유형'] == 'F_TARGET_END']
                    st.session_state.sel_target_end = [int(float(x)) for x in target_end_rows['번호'].tolist()] if not target_end_rows.empty else []
                                            
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
    st.session_state.sel_oe = ["3:3", "2:4", "4:2"]
    st.session_state.sel_ac = 7
    st.session_state.sel_con = 1
    st.session_state.sel_hl = ["3:3", "2:4", "4:2"]
    st.session_state.sum_range = (100, 175)
    st.session_state.sel_end = [1, 2] # 보통 1~2쌍이 가장 흔함
    st.session_state.sel_target_end = [] # 지정 끝수는 기본적으로 없음

def save_recommended_picks(conn, sheet_url, selected_picks):
    """체크된 추천 조합들을 'COMBI' 유형으로 구글 시트에 저장"""
    for pick in selected_picks:
        # 기존 저장 함수 활용, 유형(Type)만 'COMBI'로 전달
        save_to_sheets_by_type(conn, sheet_url, pick, 'COMBI')
    
    # 세션 상태 갱신 플래그
    st.session_state.needs_reload = True

def save_to_sheets_by_type(conn, sheet_url, new_nums, type_code):
    """
    type_code: 'PICK', 'FIX', 'EX' 중 하나
    해당 유형의 번호들을 시트에 업데이트
    """
    try:
        # 기존 전체 데이터 읽기
        try:
            full_df = conn.read(spreadsheet=sheet_url, worksheet="SavedPicks", ttl=0)
        except Exception:
            full_df = pd.DataFrame(columns=["번호", "유형"])
        # [중요] '유형' 컬럼이 없는 기존 시트라면 강제로 생성
        if '유형' not in full_df.columns:
            full_df['유형'] = 'PICK' # 기존 데이터는 모두 일반 저장으로 간주
            
        # --- [추가/수정] 삭제 로직: new_nums가 비어있는 경우 ---
        if not new_nums:
            # 해당 유형이 아닌 것들만 남겨서 저장 (즉, 해당 유형 전체 삭제)
            final_df = full_df[full_df["유형"] != type_code]
            conn.update(spreadsheet=sheet_url, worksheet="SavedPicks", data=final_df)
            
            # 세션 상태도 함께 비워줌
            if type_code == 'COMBI': st.session_state.my_combi_sets = []
            elif type_code == 'PICK': st.session_state.my_saved_picks = []
            # (필요에 따라 FIX, EX 등도 추가)
            
            st.toast(f"🗑️ {type_code} 데이터가 삭제되었습니다.")
            return # 삭제 후 함수 종료
        
        # --- 데이터 병합 로직 ---
        if type_code == 'COMBI':
            # [추가형] 기존 데이터 유지 + 새로운 6개 번호 추가
            new_type_df = pd.DataFrame({"번호": new_nums, "유형": type_code})
            final_df = pd.concat([full_df, new_type_df], ignore_index=True)
            # [세션 업데이트] 추천 조합 리스트(my_combi_sets)에 6개 세트 추가
            if 'my_combi_sets' not in st.session_state:
                st.session_state.my_combi_sets = []
            st.session_state.my_combi_sets.append(sorted(new_nums))
        else:
            # [덮어쓰기형] 해당 유형만 제거 후 교체
            other_types_df = full_df[full_df["유형"] != type_code]
            new_type_df = pd.DataFrame({"번호": new_nums, "유형": type_code})
            # 3. 합치기 및 중복 제거
            final_df = pd.concat([other_types_df, new_type_df], ignore_index=True)
            
            # [세션 동기화] 단일 리스트/값 교체
            if type_code == 'PICK': st.session_state.my_saved_picks = sorted(new_nums)
            elif type_code == 'FIX': st.session_state.fixed_nums = sorted(new_nums)
            elif type_code == 'EX': st.session_state.exclude_nums = sorted(new_nums)
             # 신규 필터 설정 동기화
            # [추가] 홀짝(Odd-Even) 설정이 필요하다면 별도 코드로 관리 (예: F_OE)
            elif type_code == 'F_OE': st.session_state.sel_oe = new_nums
            elif type_code == 'F_AC': st.session_state.sel_ac = int(new_nums[0])
            elif type_code == 'F_CON': st.session_state.sel_con = int(new_nums[0])
            elif type_code == 'F_HL': st.session_state.sel_hl = new_nums # ['3:3', '4:2'] 형태
            elif type_code == 'F_SUM': st.session_state.sum_range = (int(new_nums[0]), int(new_nums[1]))
            elif type_code == 'F_END': st.session_state.sel_end = [int(float(x)) for x in new_nums]
            elif type_code == 'F_TARGET_END': st.session_state.sel_target_end = [int(float(x)) for x in new_nums]
            # PICK, FIX 등 단일 번호 관리 유형은 번호 중복을 제거
            final_df = final_df.drop_duplicates(subset=['번호', '유형'], keep='last')

        # 4. 시트 업데이트
        conn.update(spreadsheet=sheet_url, worksheet="SavedPicks", data=final_df)
        
        st.toast(f"✅ {type_code} 설정이 저장되었습니다.")
        #st.rerun() # UI 즉시 갱신
        
    except Exception as e:
        st.error(f"저장 중 오류 발생: {e}")
        
def display_sidebar_picks(conn, sheet_url):
    """사이드바에서 저장된 조합(PICK/COMBI) 표시 및 관리"""
    with st.sidebar:
        st.divider()
        
        # --- [섹션 1] AI 추천 조합 (COMBI) ---
        st.markdown("### 🤖 추천 조합 (COMBI)")
        combi_sets = st.session_state.get('my_combi_sets', [])
        
        if combi_sets:
            for i, nums in enumerate(combi_sets):
                # 필터 설정값이 섞여 들어오는 것 방지 (리스트 길이가 6인 것만)
                if len(nums) == 6:
                    with st.expander(f"추천 조합 Set {i+1}", expanded=True):
                        ball_html = "".join([
                            f"![{n}](https://img.shields.io/badge/-{n}-blueviolet?style=flat-square&border_radius=50) " 
                            for n in sorted(nums)
                        ])
                        st.markdown(ball_html, unsafe_allow_html=True)
            # [추가] 추천 조합 전용 삭제 버튼
            if st.button("🗑️ 추천 조합만 삭제", use_container_width=True, key="del_combi"):
                # 빈 리스트를 보내서 해당 유형(COMBI)만 시트에서 제거
                save_to_sheets_by_type(conn, sheet_url, [], 'COMBI')
                st.session_state.my_combi_sets = []
                st.rerun()
        else:
            st.caption("저장된 추천 조합이 없습니다.")
            
        st.divider()
        
        # --- [섹션 2] 관심 번호 (PICK) ---
        st.markdown("### 👤 관심 번호 (PICK)")
        picks = st.session_state.get('my_saved_picks', [])
        # 필터 설정값(F_AC 등)이 리스트에 섞여 있을 수 있으므로 숫자만 골라냄
        # 보통 관심 번호는 1~45 사이의 숫자임
        valid_picks = [p for p in picks if isinstance(p, (int, float)) and 1 <= p <= 45]
        
        if valid_picks:
            # 개별 번호는 리스트 형태로 한눈에 표시
            pick_html = "".join([
                f"![{n}](https://img.shields.io/badge/-{n}-lightgrey?style=flat-square&border_radius=50) " 
                for n in sorted(picks)
            ])
            st.markdown(pick_html, unsafe_allow_html=True)
            
            # [추가] 관심 번호 전용 삭제 버튼
            if st.button("🗑️ 관심 번호만 삭제", use_container_width=True, key="del_pick"):
                # 빈 리스트를 보내서 해당 유형(PICK)만 시트에서 제거
                save_to_sheets_by_type(conn, sheet_url, [], 'PICK')
                st.session_state.my_saved_picks = []
                st.rerun()
        else:
            st.caption("선택된 관심 번호가 없습니다.")


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
            
    if 'sel_target_end' in st.session_state:
        if row['번호'] % 10 in st.session_state.sel_target_end:
            # 내가 지정한 끝수 번호들에 연한 보라색 테두리 추가
            base_style += ' border: 1.5px dashed #9370DB;'
    
    return [base_style] * len(row)
