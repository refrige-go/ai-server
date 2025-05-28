# AI Recipe Recommendation Server

이 프로젝트는 영수증 OCR과 날씨 기반 레시피 추천을 제공하는 AI 서버입니다.

## 시스템 아키텍처

### 전체 시스템 구성
```
[Next.js Frontend] <-> [Java Backend] <-> [AI Server (Python)]
```

### 데이터 흐름

1. **영수증 OCR 처리**
   ```
   Frontend -> Java Backend -> AI Server
   - Frontend: 영수증 이미지 업로드
   - Java Backend: POST /api/v1/ocr/process
   - AI Server: 
     - 이미지 전처리
     - Google Vision API로 OCR 처리
     - 식재료 매칭
     - 응답: {ingredients: [], confidence: float, processing_time: float}
   ```

2. **레시피 추천**
   ```
   Frontend -> Java Backend -> AI Server
   - Frontend: 재료 목록 전송
   - Java Backend: POST /api/v1/recipes/recommend
   - AI Server:
     - 재료 임베딩 생성 (OpenAI)
     - OpenSearch로 레시피 검색
     - 점수 계산 및 정렬
     - 응답: {recipes: [], total_matches: int, processing_time: float}
   ```

3. **날씨 기반 추천**
   ```
   Frontend -> Java Backend -> AI Server
   - Frontend: 위치 정보 전송
   - Java Backend: POST /api/v1/recipes/weather-recommend
   - AI Server:
     - 날씨 정보 조회
     - 계절 식재료 조회
     - 레시피 추천
     - 응답: {weather: {}, seasonal_ingredients: [], recipes: [], recommendation_reason: str}
   ```

## API 엔드포인트

### OCR API
- `POST /ocr/process`: 영수증 이미지 처리
- Request: `multipart/form-data` (image file)
- Response: `OCRResponse`

### 추천 API
- `POST /recommendation`: 재료 기반 레시피 추천
- Request: `RecommendationRequest`
- Response: `RecommendationResponse`

### 외부 API
- `POST /weather/recommend`: 날씨 기반 레시피 추천
- `GET /weather/{location}`: 날씨 정보 조회
- `GET /seasonal/{location}`: 계절 식재료 조회

## 로컬 개발 환경 설정

### 1. Python 환경 설정
```bash
# Python 3.9 이상 설치
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정
1. `.env.example` 파일을 `.env`로 복사
```bash
cp .env.example .env
```

2. `.env` 파일에 필요한 API 키 설정
```bash
# OpenSearch
OPENSEARCH_HOST=your_opensearch_host
OPENSEARCH_USER=your_username
OPENSEARCH_PASSWORD=your_password

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Google Cloud Vision
GOOGLE_CLOUD_CREDENTIALS=path_to_credentials.json

# Weather API
WEATHER_API_KEY=your_weather_api_key

# Seasonal Ingredients API
SEASONAL_API_KEY=your_seasonal_api_key

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### 3. Google Cloud Vision 설정
1. Google Cloud Console에서 프로젝트 생성
2. Vision API 활성화
3. 서비스 계정 생성 및 키 다운로드
4. 다운로드한 키 파일을 프로젝트 루트에 저장
5. `.env` 파일의 `GOOGLE_CLOUD_CREDENTIALS` 경로 설정

### 4. 서버 실행
```bash
# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 프로젝트 구조
```
ai-server/
├── app/
│   ├── api/              # API 엔드포인트
│   ├── services/         # 비즈니스 로직
│   ├── clients/          # 외부 API 클라이언트
│   ├── models/           # 데이터 모델
│   ├── utils/            # 유틸리티 함수
│   └── config/           # 설정
├── data/                 # 데이터 파일
├── tests/                # 테스트 코드
├── .env                  # 환경 변수
├── .env.example          # 환경 변수 예시
├── requirements.txt      # 의존성
└── README.md            # 문서
```

## 개발 가이드

### 1. 코드 스타일
- PEP 8 스타일 가이드 준수
- 타입 힌트 사용
- 문서화 주석 작성

### 2. 테스트
```bash
# 테스트 실행
pytest

# 커버리지 리포트 생성
pytest --cov=app tests/
```

### 3. 로깅
- `logging` 모듈 사용
- 로그 레벨: DEBUG, INFO, WARNING, ERROR, CRITICAL
- 로그 포맷: 시간, 레벨, 모듈, 메시지

### 4. 에러 처리
- 커스텀 예외 클래스 사용
- 적절한 에러 메시지와 상태 코드 반환
- 로깅 및 모니터링

## 배포

### Docker
```bash
# 이미지 빌드
docker build -t ai-recipe-server .

# 컨테이너 실행
docker run -p 8000:8000 --env-file .env ai-recipe-server
```

### Kubernetes
- `k8s/` 디렉토리의 매니페스트 파일 사용
- 환경 변수는 Kubernetes Secret으로 관리