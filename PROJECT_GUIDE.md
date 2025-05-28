# 레시피 AI 서버 프로젝트 가이드

## 1. 프로젝트 개요

이 프로젝트는 레시피 검색과 추천을 위한 AI 서버입니다. 주요 기능은 다음과 같습니다:

- OCR을 통한 영수증 식재료 인식
- 시맨틱 검색을 통한 레시피/식재료 검색
- 날씨 기반 레시피 추천
- 사용자 맞춤형 레시피 추천

## 2. 프로젝트 구조

```
ai-server/
├── app/                    # AI 서버 메인 코드
│   ├── api/               # API 엔드포인트
│   ├── clients/           # 외부 서비스 클라이언트
│   ├── models/            # 데이터 모델
│   ├── services/          # 비즈니스 로직
│   └── utils/             # 유틸리티 함수
├── data/                  # 데이터 파일
│   ├── recipe_embeddings.json
│   ├── ingredient_embeddings.json
│   └── synonym_dictionary.json
├── scripts/               # 유틸리티 스크립트
│   ├── upload_to_opensearch.py
│   └── test_search.py
└── recipe-ai-project/     # 임베딩 생성 프로젝트
```

## 3. 설치 및 설정

### 3.1 필수 요구사항

- Python 3.10 이상
- Java 17 이상
- OpenSearch 2.x
- OpenAI API 키
- Google Cloud Vision API 키

### 3.2 환경 설정

1. Python 가상환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Python 패키지 설치:
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정 (.env 파일):
```env
# OpenAI 설정
OPENAI_API_KEY=your_api_key

# OpenSearch 설정
OPENSEARCH_HOST=your_host
OPENSEARCH_USER=your_username
OPENSEARCH_PASSWORD=your_password

# Google Cloud Vision 설정
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

## 4. 데이터 준비

### 4.1 임베딩 데이터 생성

1. recipe-ai-project 디렉토리로 이동:
```bash
cd recipe-ai-project
```

2. 데이터 추출:
```bash
python scripts/export_recipe_embedding_input.py
python scripts/export_ingredient_embedding_input.py
```

3. 임베딩 생성:
```bash
python embedding/generate_recipe_embeddings.py
python embedding/generate_ingredient_embeddings.py
```

### 4.2 OpenSearch 데이터 업로드

1. OpenSearch 인덱스 생성 및 데이터 업로드:
```bash
python scripts/upload_to_opensearch.py
```

2. 검색 테스트:
```bash
python scripts/test_search.py
```

## 5. 서버 실행

### 5.1 AI 서버 실행

```bash
uvicorn app.main:app --reload
```

### 5.2 백엔드 서버 실행

```bash
cd backend
./gradlew bootRun
```

## 6. API 엔드포인트

### 6.1 OCR API
- POST `/api/ocr`
  - 영수증 이미지를 분석하여 식재료 추출
  - 요청: 이미지 파일
  - 응답: 인식된 식재료 목록

### 6.2 검색 API
- POST `/api/search/semantic`
  - 시맨틱 검색 수행
  - 요청: 검색어, 검색 타입(recipe/ingredient)
  - 응답: 검색 결과 목록

### 6.3 추천 API
- POST `/api/recommendation`
  - 사용자 맞춤형 레시피 추천
  - 요청: 사용자 ID, 선호도 정보
  - 응답: 추천 레시피 목록

## 7. 데이터 흐름

1. **OCR 처리 흐름**:
   - 클라이언트 → 백엔드 → AI 서버 → Google Vision API
   - AI 서버 → 백엔드 → 클라이언트

2. **검색 흐름**:
   - 클라이언트 → 백엔드 → AI 서버 → OpenSearch
   - AI 서버 → 백엔드 → 클라이언트

3. **추천 흐름**:
   - 클라이언트 → 백엔드 → AI 서버 → OpenSearch/OpenAI
   - AI 서버 → 백엔드 → 클라이언트

## 8. 주요 기능 설명

### 8.1 시맨틱 검색
- OpenSearch의 KNN 벡터 검색 사용
- 한국어 Nori 분석기로 텍스트 검색
- 오타 및 띄어쓰기 오류 대응

### 8.2 OCR 처리
- Google Cloud Vision API 사용
- 이미지 전처리 및 품질 개선
- 식재료 매칭 및 신뢰도 계산

### 8.3 레시피 추천
- 사용자 선호도 기반 추천
- 날씨 정보 기반 추천
- 계절 식재료 고려

## 9. 문제 해결

### 9.1 일반적인 문제
1. OpenSearch 연결 오류
   - 호스트 및 인증 정보 확인
   - SSL 설정 확인

2. OCR 인식률 저하
   - 이미지 품질 확인
   - 전처리 설정 조정

3. 검색 결과 부정확
   - 임베딩 데이터 재생성
   - 검색 파라미터 조정

### 9.2 성능 최적화
1. 검색 성능
   - 인덱스 설정 최적화
   - 캐시 활용

2. OCR 성능
   - 이미지 크기 최적화
   - 배치 처리

## 10. 모니터링

### 10.1 로깅
- FastAPI 로깅 설정
- OpenSearch 로그 모니터링
- 에러 추적

### 10.2 성능 모니터링
- API 응답 시간
- 검색 성능
- OCR 처리 시간

## 11. 보안

### 11.1 API 보안
- API 키 관리
- 요청 제한
- 입력 검증

### 11.2 데이터 보안
- 민감 정보 암호화
- 접근 제어
- 백업 정책

## 12. 추가 개발 가이드

### 12.1 새로운 기능 추가
1. API 엔드포인트 추가
2. 서비스 로직 구현
3. 클라이언트 연동

### 12.2 테스트
1. 단위 테스트 작성
2. 통합 테스트 수행
3. 성능 테스트

## 13. 참고 자료

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [OpenSearch 문서](https://opensearch.org/docs/)
- [Google Cloud Vision API 문서](https://cloud.google.com/vision/docs)
- [OpenAI API 문서](https://platform.openai.com/docs/api-reference)

## 담당자별 작업 파일

### 가은 (날씨/제철 API 담당)
- `app/clients/seasonal_api_client.py`: 계절별 식재료 API 클라이언트
- `app/clients/weather_api_client.py`: 날씨 API 클라이언트
- `app/api/weather.py`: 날씨 기반 레시피 추천 API
- `app/services/weather_service.py`: 날씨 기반 추천 서비스
- `app/services/seasonal_service.py`: 제철 식재료 기반 추천 서비스

### 원준 (OCR 담당)
- `app/clients/vision_api_client.py`: Google Cloud Vision API 클라이언트
- `app/api/ocr.py`: OCR 처리 API
- `app/services/ocr_service.py`: OCR 처리 서비스
- `app/utils/image_processor.py`: 이미지 전처리 유틸리티

### 유진 (나머지 전체 담당)
- `app/main.py`: 메인 애플리케이션
- `app/api/search.py`: 시맨틱 검색 API
- `app/api/recommendation.py`: 일반 추천 API
- `app/clients/opensearch_client.py`: OpenSearch 클라이언트
- `app/clients/openai_client.py`: OpenAI API 클라이언트
- `app/services/search_service.py`: 검색 서비스
- `app/services/recommendation_service.py`: 추천 서비스
- `app/models/`: 모든 데이터 모델
- `app/config/`: 설정 파일들
- `app/utils/`: 유틸리티 함수들
- `scripts/`: 유틸리티 스크립트들 