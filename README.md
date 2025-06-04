# 🤖 AI Recipe Server

FastAPI 기반의 AI 레시피 추천 및 시맨틱 검색 서버입니다.

## 🚀 빠른 시작 (새 팀원용)

### 1. 저장소 클론
```bash
git clone <repository-url>
cd ai-server
```

### 2. 환경 설정
```bash
# 1. 가상환경 생성
python -m venv venv

# 2. 가상환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. 자동 설치 실행
python setup.py
```

### 3. API 키 설정
`.env.local` 파일에서 OpenAI API 키를 설정하세요:
```env
OPENAI_API_KEY=sk-proj-your_actual_api_key_here
```

### 4. 서버 실행
```bash
uvicorn app.main:app --reload
```

서버 접속: http://localhost:8000  
API 문서: http://localhost:8000/docs

## ⚡ 주요 기능

- **🔍 시맨틱 검색**: OpenAI 임베딩 기반 의미 검색
- **🤖 AI 추천**: 검색 결과 관련성 AI 재평가
- **📱 OCR 지원**: 이미지에서 재료 추출
- **🌤️ 날씨 연동**: 날씨에 따른 레시피 추천
- **🥬 제철 재료**: 계절별 재료 추천

## 🔧 주요 API 엔드포인트

### 헬스체크
```bash
GET /health
```

### 레시피 검색
```bash
# 텍스트 검색
GET /api/search/recipes?query=볶음&limit=10

# 벡터 검색
POST /api/search/vector
{
  "query": "건강한 아침식사",
  "limit": 10
}

# 시맨틱 검색
POST /api/search/semantic
{
  "query": "따뜻한 국물 요리",
  "search_type": "all",
  "limit": 10
}
```

### 재료 검색
```bash
GET /api/search/ingredients?query=양파&limit=10
```

## 🏗️ 프로젝트 구조

```
ai-server/
├── app/
│   ├── main.py              # FastAPI 앱 엔트리포인트
│   ├── api/                 # API 라우터들
│   │   ├── search.py        # 검색 API
│   │   ├── recommendation.py # 추천 API
│   │   ├── integration.py   # 통합 API
│   │   └── ocr.py          # OCR API
│   ├── clients/             # 외부 서비스 클라이언트
│   │   ├── opensearch_client.py
│   │   ├── openai_client.py
│   │   └── google_vision_client.py
│   ├── services/            # 비즈니스 로직
│   │   ├── enhanced_search_service_script.py
│   │   ├── recommendation_service.py
│   │   └── ocr_service.py
│   ├── utils/               # 유틸리티
│   │   ├── openai_relevance_scorer.py
│   │   ├── score_normalizer.py
│   │   ├── synonym_matcher.py
│   │   └── text_processor.py
│   ├── models/              # 데이터 모델
│   │   └── schemas.py
│   └── config/              # 설정
│       └── settings.py
├── data/                    # 데이터 파일
│   └── synonym_dictionary.json
├── requirements.txt         # Python 패키지 목록
├── setup.py                # 자동 설치 스크립트
├── .env.example            # 환경변수 예시
└── README.md               # 이 파일
```

## 🔗 연동 시스템

### recipe-ai-project (OpenSearch)
- OpenSearch 검색 엔진: http://localhost:9200
- 레시피 및 재료 임베딩 데이터 제공

### 백엔드 (Java Spring Boot)
- AI 서버 API 호출하여 검색 결과 활용
- 사용자 요청을 AI 서버로 프록시

### 프론트엔드 (React)
- 백엔드를 통해 AI 서버 기능 사용
- 검색, 추천, OCR 기능 UI 제공

## ⚙️ 환경변수 설정

### 필수 설정
```env
# OpenSearch 연결 (recipe-ai-project)
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200

# OpenAI API (시맨틱 검색용)
OPENAI_API_KEY=sk-proj-your_key_here
```

### 선택적 설정
```env
# Google Cloud Vision (OCR용)
GOOGLE_APPLICATION_CREDENTIALS=certificates/service-account.json

# 날씨 API (날씨 기반 추천용)
WEATHER_API_KEY=your_weather_api_key

# 제철 재료 API
SEASONAL_API_KEY=your_seasonal_api_key
```

## 🧪 테스트

### 연결 테스트
```bash
python setup.py --check
```

### API 테스트
```bash
python setup.py --test-api
```

### 수동 테스트
```bash
# 헬스체크
curl http://localhost:8000/health

# 레시피 검색
curl "http://localhost:8000/api/search/recipes?query=볶음&limit=3"

# 재료 검색
curl "http://localhost:8000/api/search/ingredients?query=양파&limit=3"
```

## 🐛 문제 해결

### OpenSearch 연결 오류
```bash
# recipe-ai-project에서 OpenSearch 실행
cd ../recipe-ai-project
python setup.py
```

### 패키지 설치 오류
```bash
# pip 업그레이드
pip install --upgrade pip

# requirements.txt 재설치
pip install -r requirements.txt
```

### API 키 오류
1. `.env.local` 파일에서 `OPENAI_API_KEY` 확인
2. OpenAI 계정에서 API 키 발급 확인
3. API 키 잔액 확인

## 📚 개발 가이드

### 새로운 API 엔드포인트 추가
1. `app/api/` 디렉토리에 라우터 파일 생성
2. `app/main.py`에서 라우터 등록
3. `app/models/schemas.py`에 데이터 모델 정의

### 새로운 검색 기능 추가
1. `app/services/` 디렉토리에 서비스 클래스 생성
2. OpenSearch 클라이언트 또는 OpenAI 클라이언트 활용
3. 점수 정규화 적용

### 코드 스타일
- PEP 8 파이썬 코딩 스타일 준수
- Type hints 사용 권장
- 비동기 함수 (`async/await`) 사용

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 지원

문제가 있으시면 GitHub Issues에 문의하거나 팀 Slack 채널을 이용해주세요.
