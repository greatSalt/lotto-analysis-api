import os
import pandas as pd
from datetime import datetime
import streamlit as st

def save_analysis_to_project(df, project_root="/data/data/com.termux/files/home/documents/lottoproject/v0.1"):
    """
    분석 결과를 프로젝트 내 data 폴더에 즉시 저장합니다.
    """
    try:
        # 1. 저장 경로 설정 (data 폴더가 없으면 생성)
        save_dir = os.path.join(project_root, "data")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 2. 파일명 생성 (회차 정보가 있다면 넣고, 없으면 타임스탬프 사용)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crazy_analysis_{timestamp}.csv"
        file_path = os.path.join(save_dir, filename)

        # 3. CSV 저장 (한글 깨짐 방지를 위해 utf-8-sig 사용)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return True, file_path
    except Exception as e:
        return False, str(e)

def render_save_button(df):
    """
    스트림릿 UI에 저장 버튼을 렌더링합니다.
    """
    if st.button("💾 프로젝트 폴더에 즉시 저장 (Termux)"):
        if df.empty:
            st.error("저장할 데이터가 없습니다.")
            return

        success, result = save_analysis_to_project(df)
        
        if success:
            st.success(f"✅ 저장 완료! (Acode에서 확인 가능)")
            st.info(f"📍 경로: {result}")
        else:
            st.error(f"❌ 저장 실패: {result}")
