import os
import pandas as pd
from datetime import datetime
import streamlit as st

def save_analysis_to_project(df, base_path="/data/data/com.termux/files/home/documents/lottoproject/v0.1"):
    """
    분석 결과를 프로젝트 내 data 폴더에 즉시 저장합니다.
    """
    try:
        # 1. 저장 경로 설정 (base_path 아래에 data 폴더 생성)
        # 만약 base_path 자체를 저장소로 쓰고 싶다면 이 부분을 조정하세요.
        save_dir = os.path.join(base_path, "data")
        
        # 폴더가 없으면 생성 (exist_ok=True로 중복 에러 방지)
        os.makedirs(save_dir, exist_ok=True)

        # 2. 파일명 생성 (날짜_시간 형식)
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
    # 버튼 디자인을 조금 더 강조했습니다.
    if st.button("💾 프로젝트 폴더에 즉시 저장 (Termux)", use_container_width=True):
        if df is None or df.empty:
            st.error("저장할 데이터가 없습니다.")
            return

        success, result = save_analysis_to_project(df)
        
        if success:
            st.success("✅ 저장 완료! (Acode 파일 트리에서 확인하세요)")
            st.code(f"저장 위치: {result}", language="text")
        else:
            st.error(f"❌ 저장 실패: {result}")
            st.info("💡 팁: Termux 환경에서 'termux-setup-storage' 권한을 확인해 보세요.")
