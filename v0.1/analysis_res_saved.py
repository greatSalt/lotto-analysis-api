import os
import pandas as pd
from datetime import datetime
import streamlit as st

def save_analysis_to_project(df):
    try:
        # 1. 홈 디렉토리 확인
        home_path = os.path.expanduser("~")
        
        # 2. 경로 설정 (대소문자 주의: Documents vs documents)
        # 사용자님의 실제 폴더명이 대문자 'Documents'라면 아래를 "Documents"로 수정하세요.
        target_dir = os.path.join(home_path, "documents/lottoproject/V0.1/resource")
        
        # 3. 폴더 생성
        os.makedirs(target_dir, exist_ok=True)

        # 4. 파일명 및 경로 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crazy_res_{timestamp}.csv"
        file_path = os.path.join(target_dir, filename)

        # 5. CSV 저장
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        # [추가] 저장 직후 물리적 존재 여부 체크
        if os.path.exists(file_path):
            return True, file_path
        else:
            return False, f"파일 생성 실패 (경로: {file_path})"
            
    except Exception as e:
        return False, str(e)

def render_save_button(df):
    if st.button("💾 분석 결과 Resource 폴더에 저장", use_container_width=True):
        if df is None or df.empty:
            st.warning("저장할 데이터가 없습니다.")
            return

        success, result = save_analysis_to_project(df)
        
        if success:
            st.success("✅ [코드 로직] 저장 성공 메시지 발송")
            
            # --- [물리적 검증 섹션] ---
            if os.path.isfile(result):
                st.balloons()
                st.info(f"📂 [물리적 확인] 파일이 실제 존재함 확인 완료!")
                st.code(f"ls -l {result}", language="bash")
            else:
                st.error("❗ [비상] 저장 성공 메시지는 떴으나, 파일이 실제로는 없습니다!")
                st.warning("원인 추정: Termux 가상 파일 시스템의 쓰기 지연 또는 권한 우회 오류")
        else:
            st.error(f"❌ 저장 실패: {result}")
