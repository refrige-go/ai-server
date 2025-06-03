#!/bin/bash

echo "🚀 AI 서버 자동 설치 스크립트"
echo "================================"

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3이 설치되어 있지 않습니다."
    echo "💡 시스템 패키지 매니저를 사용해 Python 3.8+ 을 설치하세요."
    exit 1
fi

echo "✅ Python3 설치 확인됨"

# 가상환경 생성
echo ""
echo "📦 가상환경 생성 중..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 가상환경 생성 완료"
else
    echo "✅ 가상환경이 이미 존재합니다"
fi

# 가상환경 활성화
echo ""
echo "🔄 가상환경 활성화..."
source venv/bin/activate

# 의존성 설치
echo ""
echo "📥 의존성 설치 중..."
pip install -r requirements.txt

# 환경변수 파일 생성
echo ""
echo "⚙️ 환경 설정..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ .env 파일 생성 완료"
    echo ""
    echo "⚠️ 중요: .env 파일을 편집하여 다음 값들을 설정하세요:"
    echo "   - OPENAI_API_KEY: OpenAI API 키"
    echo "   - GOOGLE_APPLICATION_CREDENTIALS: Google Vision 인증서 경로"
else
    echo "✅ .env 파일이 이미 존재합니다"
fi

# 스크립트 실행 권한 부여
chmod +x scripts/test_connection.py

# 연결 테스트
echo ""
echo "🧪 연결 테스트..."
python scripts/test_connection.py

# 완료 메시지
echo ""
echo "================================"
echo "🎉 설치 완료!"
echo ""
echo "💡 다음 단계:"
echo "   1. .env 파일에서 API 키들을 설정하세요"
echo "   2. recipe-ai-project OpenSearch를 실행하세요"
echo "   3. 서버 시작: uvicorn app.main:app --reload"
echo ""
echo "📚 문서: http://localhost:8000/docs"
echo "================================"
