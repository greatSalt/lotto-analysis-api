import os
import pandas as pd
from datetime import datetime
import streamlit as st

def save_analysis_to_project(df):
    """
    분석 결과를 프로젝트 내 resource 폴더에 즉시 저장합니다.
    (기존 data 폴더에서 resource로 명칭 변경 반영)
    """
    try:
        # 1. Termux 홈 디렉토리 경로 자동 인식 (~/)
        home_path = os.path.expanduser("~")
        
        # 2. 최종 목적지 경로 설정 (data -> resource)
        # 사용자님의 경로: Documents/lottoproject/v0.1/resource
        target_dir = os.path.join(home_path, "documents/lottoproject/v0.1/resource")
        
        # 3. 폴더가 없으면 생성 (중복 에러 방지)
        os.makedirs(target_dir, exist_ok=True)

        # 4. 파일명 생성 (구분을 위해 crazy_res_ 시작)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crazy_res_{timestamp}.csv"
        file_path = os.path.join(target_dir, filename)

        # 5. CSV 저장
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return True, file_path
    except Exception as e:
        return False, str(e)

def render_save_button(df):
    """
    스트림릿 UI 저장 버튼 렌더링
    """
    if st.button("💾 분석 결과 Resource 폴더에 저장", use_container_width=True):
        if df is None or df.empty:
            st.warning("저장할 데이터가 없습니다.")
            return

        success, result = save_analysis_to_project(df)
        
        if success:
            st.success("✅ Resource 저장 성공! Acode에서 확인하세요.")
            st.code(f"📍 위치: {result}", language="text")
        else:
            st.error(f"❌ 저장 실패: {result}")
            st.info("💡 Tip: 폴더명 대소문자(documents vs Documents)를 확인해 보세요.")
