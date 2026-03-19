#!/bin/bash

# 1. 변경된 모든 파일 스테이징
git add .

# 2. 커밋 메시지 입력 (입력 안 하고 엔터 치면 기본 메시지 사용)
echo "📝 커밋 메시지를 입력하세요 (기본값: 'Minor updates and optimization'):"
read msg

if [ -z "$msg" ]; then
    msg="Update: $(date +'%Y-%m-%d %H:%M:%S')"
fi

# 3. 커밋 실행
git commit -m "$msg"

# 4. 현재 브랜치 확인 및 푸시 (보통 main 또는 master)
current_branch=$(git branch --show-current)
echo "🚀 '$current_branch' 브랜치로 푸시 중..."
git push origin "$current_branch"

echo "✅ 작업 완료! 16, 18, 23, 24, 31, 41 번호의 분석 데이터가 안전하게 저장되었습니다."
