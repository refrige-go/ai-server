# Refrige-Go AI Server

한국어 음식 레시피 AI 추천 시스템의 AI 서버입니다.

## 🎯 주요 기능

- **🔍 시맨틱 검색**: OpenAI 임베딩 기반 유사도 검색
- **🔧 오타 교정**: 한글 자모 분리 오타 자동 교정 (`ㄹㅏ면` → `라면`)
- **🤖 AI 추천**: OpenAI GPT 기반 레시피 추천
- **🌤️ 날씨 기반 추천**: 날씨에 따른 음식 추천
- **📱 OCR 인식**: Google Vision API 기반 이미지 텍스트 인식
- **🔄 동의어 매칭**: 피망↔파프리카 등 동의어 지원

## 📁 프로젝트 구조

```
ai-server/
├── app/                           # 메인 애플리케이션
│   ├── main.py                   # FastAPI 애플리케이션 진입점
│   ├── api/                      # API 라우터들
│   │   ├── search.py            # 시맨틱 검색 API
│   │   ├── spell_check.py       # 오타 교정 API
│   │   ├── recommendation.py    # AI 추천 API
│   │   ├── integration.py       # 통합 API
│   │   ├── external.py          # 외부 API 연동
│   │   └── ocr.py              # OCR 인식 API
│   ├── clients/                  # 외부 서비스 클라이언트
│   │   ├── opensearch_client.py # OpenSearch 연결
│   │   ├── openai_client.py     # OpenAI API 클라이언트
│   │   ├── google_vision_client.py # Google Vision API
│   │   ├── weather_api_client.py   # 날씨 API
│   │   └── seasonal_api_client.py  # 계절 API
│   ├── services/                 # 비즈니스 로직
│   │   ├── final_strict_semantic_search_service.py # 최종 시맨틱 검색
│   │   ├── recommendation_service.py # 추천 서비스
│   │   ├── ocr_service.py       # OCR 처리 서비스
│   │   ├── weather_service.py   # 날씨 서비스
│   │   └── search_service.py    # 기본 검색 서비스
│   ├── utils/                    # 유틸리티 함수들
│   │   ├── korean_spell_checker.py    # 한글 오타 교정
│   │   ├── score_normalizer.py        # 점수 정규화
│   │   ├── synonym_matcher.py         # 동의어 매칭
│   │   ├── text_processor.py          # 텍스트 전처리
│   │   ├── image_preprocessor.py      # 이미지 전처리
│   │   └── openai_relevance_verifier.py # 관련성 검증
│   ├── models/                   # 데이터 모델
│   │   └── schemas.py           # Pydantic 스키마
│   └── config/                   # 설정
│       └── settings.py          # 환경 설정
├── data/                         # 데이터 파일
│   └── synonym_dictionary.json  # 동의어 사전
├── docs/                         # 문서
│   └── API.md                   # API 문서
├── scripts/                      # 유틸리티 스크립트
│   └── test_connection.py       # 연결 테스트
├── docker-compose.yml           # Docker 구성
├── Dockerfile                   # Docker 이미지
├── requirements.txt             # 파이썬 의존성
├── .env.example                # 환경변수 예시
└── README.md                   # 프로젝트 문서
```

## 🚀 빠른 시작

### 1. 프로젝트 클론

```bash
git clone <repository-url>
cd ai-server
```

### 2. 가상환경 생성 및 활성화

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정

```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일을 편집하여 API 키 설정
# OPENAI_API_KEY=your_openai_api_key
# OPENSEARCH_HOST=localhost
# OPENSEARCH_PORT=9200
```

### 5. 서버 실행

```bash
python -m app.main
```

또는

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔧 필수 환경 설정

### OpenSearch 설정
- **호스트**: localhost:9200 (기본값)
- **인덱스**: `recipes`, `ingredients`
- **벡터 필드**: 임베딩된 레시피/재료 데이터 필요

### API 키 설정
- **OpenAI API**: GPT 및 임베딩용
- **Google Vision API**: OCR 인식용 (선택사항)
- **날씨 API**: 날씨 기반 추천용 (선택사항)

## 📊 API 엔드포인트

### 시맨틱 검색
- `POST /api/search/semantic` - 오타 교정 포함 시맨틱 검색
- `GET /api/search/recipes` - 레시피 텍스트 검색
- `GET /api/search/ingredients` - 재료 검색

### 오타 교정
- `POST /api/spell/spell-check` - 단일 오타 교정
- `POST /api/spell/spell-check-batch` - 일괄 오타 교정
- `GET /api/spell/test-spell-check` - 오타 교정 테스트

### AI 추천
- `POST /api/recommend/recipes` - AI 레시피 추천
- `POST /api/recommend/weather-based` - 날씨 기반 추천

### OCR 인식
- `POST /api/ocr/recognize` - 이미지에서 텍스트 추출

### 시스템
- `GET /` - 서버 정보
- `GET /health` - 헬스체크
- `GET /docs` - API 문서 (Swagger)

## 🧪 테스트

### 연결 테스트
```bash
python scripts/test_connection.py
```

### API 테스트
```bash
# 오타 교정 테스트
curl -X GET "http://localhost:8000/api/spell/test-spell-check"

# 시맨틱 검색 테스트
curl -X POST "http://localhost:8000/api/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{"query": "ㄹㅏ면", "limit": 5}'
```

## 🐳 Docker 실행

```bash
# Docker Compose로 실행
docker-compose up -d

# 개별 빌드 및 실행
docker build -t ai-server .
docker run -p 8000:8000 ai-server
```

## 📈 성능 최적화

- **벡터 검색**: OpenSearch KNN 플러그인 활용
- **오타 교정**: 한글 자모 분해/조합 알고리즘
- **동의어 매칭**: 실시간 동의어 확장
- **관련성 필터링**: AI 기반 결과 품질 검증

## 🔍 주요 특징

### 오타 교정 시스템
- 자모 분리 오타: `ㄹㅏ면` → `라면`
- 키보드 오타: 인접 키 기반 교정
- OpenSearch 퍼지 매칭 활용

### 동의어 지원
- 피망 ↔ 파프리카
- 양배추 ↔ 배추 ↔ 캐비지
- 대파 ↔ 파 ↔ 쪽파

### 하이브리드 검색
1. 텍스트 검색 (정확한 매칭)
2. 벡터 검색 (의미적 유사도)
3. AI 관련성 검증
4. 최종 점수 통합

## 🚨 문제 해결

### OpenSearch 연결 실패
```bash
# OpenSearch 실행 확인
curl -X GET "localhost:9200"

# 인덱스 존재 확인
curl -X GET "localhost:9200/recipes,ingredients"
```

### 오타 교정 동작 안함
- OpenSearch 연결 상태 확인
- 레시피/재료 데이터 존재 확인
- 벡터 임베딩 데이터 확인

### 의존성 설치 오류
```bash
# 최신 pip 업그레이드
pip install --upgrade pip

# 캐시 클리어 후 재설치
pip cache purge
pip install -r requirements.txt
```

## 🤝 기여하기

1. 이 저장소를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📞 연락처

문제가 있거나 질문이 있으시면 이슈를 생성해주세요.

---

**Refrige-Go Team** - 냉장고 재료로 AI가 추천하는 맞춤 레시피 🥘
