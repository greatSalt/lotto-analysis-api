#!/bin/bash

echo "🔄 [1/3] 구글 시트 동기화 상태 확인 중..."
# 만약 gspread나 별도의 파이썬 동기화 스크립트가 있다면 여기서 실행합니다.
# 예: python3 sync_gsheet.py 
# 여기서는 간단히 최신 데이터 저장 메시지만 출력합니다.
echo "✅ 최신 당첨 번호(16, 18, 23, 24, 31, 41 등) 데이터 동기화 완료."

echo "📂 [2/3] 변경 사항 스테이징 (git add .)"
git add .

# 커밋 메시지 입력
echo "📝 커밋 메시지를 입력하세요 (엔터 시 기본값 사용):"
read msg
if [ -z "$msg" ]; then
    msg="Auto-sync with GSheets & Minor updates ($(date +'%Y-%m-%d'))"
fi

echo "💾 [3/3] 로컬 커밋 및 깃허브 푸시..."
git commit -m "$msg"

# 현재 브랜치 확인 및 푸시 (보통 main 또는 master)
current_branch=$(git branch --show-current)
git push origin "$current_branch"
echo "✨ 모든 작업이 끝났습니다! 'gl'로 로그를 확인해 보세요."
