import os
import pandas as pd
from datetime import datetime
import streamlit as st

def save_analysis_to_project(df):
    try:
        # [핵심 수정] 현재 파일(analysis_res_saved.py)이 위치한 폴더 경로를 가져옵니다.
        # 사용자님이 터미널에서 보고 계신 그 'V0.1' 폴더가 됩니다.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 해당 폴더 바로 아래의 'resource' 폴더 지정
        target_dir = os.path.join(current_dir, "resource")
        
        # 폴더 생성 (없으면 생성)
        os.makedirs(target_dir, exist_ok=True)

        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crazy_res_{timestamp}.csv"
        file_path = os.path.join(target_dir, filename)

        # CSV 저장
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        # 물리적 존재 확인
        if os.path.exists(file_path):
            return True, file_path
        else:
            return False, "파일 쓰기 실패"
            
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
            st.code(f"📍 저장된 절대 경로:\n{result}", language="text")
            st.info("💡 위 경로를 복사해서 터미널에서 'ls -l [경로]'를 입력해보세요.")
        else:
            st.error(f"❌ 저장 실패: {result}")
