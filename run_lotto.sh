#!/bin/bash

# 1. 프로젝트 폴더로 이동
PROJECT_DIR="$HOME/storage/documents/lottoproject"
cd $PROJECT_DIR

echo "------------------------------------------"
echo "📂 [Step 1] 구글 시트 -> 로컬 CSV 백업 중..."
# 프로그램 실행 전, 최신 상태를 CSV로 한 번 저장해둡니다.
python3 sync_gsheet.py

if [ $? -eq 0 ]; then
    echo "💾 백업 완료: lotto_data.csv"
else
    echo "⚠️ 백업 실패: 네트워크 연결을 확인하세요."
fi

echo "------------------------------------------"
echo "🖥️ [Step 2] 실시간 분석기(Streamlit) 가동..."
if [ -d "./venv" ]; then
    source ./venv/bin/activate
fi

# 메인 실행 (내부에서 gspread를 통해 실시간으로 시트 조회)
streamlit run main.py

# 종료 후 가상환경 해제
deactivate
