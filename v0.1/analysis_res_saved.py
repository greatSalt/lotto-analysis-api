import os
import pandas as pd
from datetime import datetime
import streamlit as st

def save_analysis_to_project(df):
    """
    현재 파일의 위치를 기준으로 resource 폴더에 저장합니다.
    """
    try:
        # 1. 현재 이 파이썬 파일(analysis_res_saved.py)이 있는 실제 디렉토리 추출
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        
        # 2. 현재 디렉토리 바로 아래의 'resource' 폴더 지정
        # 예: /.../v0.1/resource
        target_dir = os.path.join(current_dir, "resource")
        
        # 3. 폴더가 없으면 생성
        os.makedirs(target_dir, exist_ok=True)

        # 4. 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crazy_res_{timestamp}.csv"
        file_path = os.path.join(target_dir, filename)

        # 5. CSV 저장
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return True, file_path
    except Exception as e:
        return False, str(e)

def render_save_button(df):
    if st.button("💾 현재 프로젝트 resource 폴더에 저장", use_container_width=True):
        if df is None or df.empty:
            st.warning("저장할 데이터가 없습니다.")
            return

        success, result = save_analysis_to_project(df)
        
        if success:
            st.success("✅ 저장 성공!")
            # 사용자님이 터미널에서 확인할 수 있도록 실제 물리적 경로를 출력합니다.
            st.info("📍 아래 경로를 복사해서 터미널에 'ls' 해보세요:")
            st.code(result, language="text")
        else:
            st.error(f"❌ 저장 실패: {result}")
