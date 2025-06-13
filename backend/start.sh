#!/bin/bash
# 전체 서버(백엔드+프론트엔드) 실행 자동화 스크립트
# 사용법: ./start.sh

cd "$(dirname "$0")"

# 백엔드 가상환경 활성화
source venv/bin/activate

# macOS에서 3000번 포트 사용 중인 프로세스 종료
PID=$(lsof -ti tcp:3000)
if [ -n "$PID" ]; then
  kill -9 $PID
fi

# 프론트엔드 서버 실행 (백그라운드)
cd ../frontend
npm start &
FRONT_PID=$!
cd ../backend

# Flask 서버 실행 (현재 쉘)
python app.py

# 종료 시 프론트엔드 서버도 종료
kill $FRONT_PID