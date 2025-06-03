# 🤖 Refrige-Go AI Server

식재료 기반 레시피 추천을 위한 AI 서버입니다. OpenSearch와 OpenAI 임베딩을 활용한 시맨틱 검색과 레시피 추천 기능을 제공합니다.

## 📋 목차
- [기능 소개](#기능-소개)
- [시스템 요구사항](#시스템-요구사항)
- [설치 및 실행](#설치-및-실행)
- [API 문서](#api-문서)
- [Java 백엔드 연동](#java-백엔드-연동)
- [프로젝트 구조](#프로젝트-구조)
- [개발 가이드](#개발-가이드)

## 🚀 기능 소개

### 핵심 기능
- **재료 기반 레시피 추천**: 보유 재료로 만들 수 있는 레시피 추천
- **시맨틱 검색**: AI 임베딩을 활용한 의미 기반 검색
- **텍스트 검색**: 키워드 기반 레시피/재료 검색
- **벡터 검색**: OpenAI 임베딩 기반 유사도 검색

### AI 매칭 시스템
```
1. Exact Match (정확 매칭)
   - 파프리카 = 파프리카

2. Synonym Match (동의어 매칭) 🤖
   - 파프리카 ↔ 피망
   - 양배추 ↔ 배추

3. Similar Match (유사 재료) 🤖
   - 소고기 → 돼지고기 (같은 육류)
   - 양파 → 대파 (같은 파 계열)

4. Substitute Match (대체 재료) 🤖
   - 우유 → 두유
   - 설탕 → 꿀
```

## 🛠 시스템 요구사항

### 필수 요구사항
- **Python 3.8+**
- **Docker & Docker Compose**
- **OpenSearch** (recipe-ai-project 연동)
- **OpenAI API Key**

### 선택적 요구사항
- Google Cloud Vision API (OCR 기능용)
- Weather API Key (날씨 기반 추천용)

## 🚀 설치 및 실행

### 1. 프로젝트 클론
```bash
git clone [your-repo-url]
cd ai-server
```

### 2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv recipe-ai
recipe-ai\Scripts\activate

# macOS/Linux
python -m venv recipe-ai
source recipe-ai/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일 편집 (필수 설정)
OPENAI_API_KEY=your_openai_api_key
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9201
```

### 5. OpenSearch 실행 (recipe-ai-project)
```bash
# recipe-ai-project 디렉토리에서
cd ../recipe-ai-project
docker-compose up -d

# OpenSearch가 완전히 시작될 때까지 대기 (약 1-2분)
```

### 6. AI 서버 실행
```bash
# ai-server 디렉토리에서
uvicorn app.main:app --reload --port 8000
```

### 7. 서버 확인
- API 문서: http://localhost:8000/docs
- 헬스체크: http://localhost:8000/health

## 📖 API 문서

### 주요 엔드포인트

#### 1. 레시피 추천 (권장)
```http
POST /api/recommend/by-ingredients
Content-Type: application/json

{
  "ingredients": ["양파", "당근", "소고기"],
  "limit": 10
}
```

**응답 예시:**
```json
{
  "recipes": [
    {
      "rcp_seq": "1045",
      "rcp_nm": "차가운 당근 수프",
      "score": 1.214,
      "match_reason": "차가운 당근 수프은(는) 요청하신 재료 대부분을 사용합니다 (매칭도: 100.0%)",
      "rcp_way2": "끓이기",
      "rcp_category": "양식",
      "ingredients": [...]
    }
  ],
  "total": 1,
  "processing_time": 0.95
}
```

#### 2. 벡터 기반 추천 (AI 추천)
```http
POST /api/integration/recipes/recommend/vector
Content-Type: application/json

{
  "ingredients": ["양파", "당근"],
  "limit": 10
}
```

#### 3. 텍스트 검색
```http
GET /api/integration/recipes/search/text?q=볶음&limit=10
GET /api/integration/ingredients/search/text?q=고기&limit=10
```

#### 4. 헬스체크
```http
GET /health
```

## ☕ Java 백엔드 연동

### RestTemplate 설정 예시
```java
@Service
public class AIServerService {
    
    private final RestTemplate restTemplate;
    private final String AI_SERVER_URL = "http://localhost:8000";
    
    @Autowired
    public AIServerService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }
    
    public RecipeRecommendationResponse getRecommendations(List<String> ingredients) {
        String url = AI_SERVER_URL + "/api/recommend/by-ingredients";
        
        Map<String, Object> request = new HashMap<>();
        request.put("ingredients", ingredients);
        request.put("limit", 10);
        
        return restTemplate.postForObject(url, request, RecipeRecommendationResponse.class);
    }
}
```

### WebClient 설정 예시 (Spring WebFlux)
```java
@Service
public class AIServerWebClientService {
    
    private final WebClient webClient;
    
    public AIServerWebClientService() {
        this.webClient = WebClient.builder()
            .baseUrl("http://localhost:8000")
            .build();
    }
    
    public Mono<RecipeRecommendationResponse> getRecommendations(List<String> ingredients) {
        Map<String, Object> request = new HashMap<>();
        request.put("ingredients", ingredients);
        request.put("limit", 10);
        
        return webClient.post()
            .uri("/api/recommend/by-ingredients")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(RecipeRecommendationResponse.class);
    }
}
```

## 📁 프로젝트 구조

```
ai-server/
├── app/
│   ├── api/                    # API 라우터
│   │   ├── recommendation.py   # 레시피 추천 API
│   │   ├── search.py          # 검색 API
│   │   └── integration.py     # 통합 API
│   ├── clients/               # 외부 서비스 클라이언트
│   │   ├── opensearch_client.py
│   │   └── openai_client.py
│   ├── config/                # 설정
│   │   └── settings.py
│   ├── models/                # 데이터 모델
│   │   └── schemas.py
│   ├── services/              # 비즈니스 로직
│   │   └── recommendation_service.py
│   ├── utils/                 # 유틸리티
│   └── main.py               # FastAPI 앱 진입점
├── scripts/                   # 설정 및 유틸 스크립트
├── docs/                     # 문서
├── requirements.txt          # Python 의존성
├── docker-compose.yml        # Docker 설정
├── Dockerfile               # Docker 이미지 빌드
├── .env.example            # 환경변수 예시
└── README.md              # 프로젝트 문서
```

## 🔧 개발 가이드

### 개발 환경 설정
1. 코드 변경 시 자동 재시작: `uvicorn app.main:app --reload`
2. API 문서 확인: http://localhost:8000/docs
3. 로그 레벨 설정: `.env`에서 `LOG_LEVEL=DEBUG`

### 테스트 실행
```bash
# 기본 연결 테스트 (개발용 스크립트는 .gitignore에 포함)
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"
```

### 환경변수 설정 가이드

#### 필수 설정
```bash
# OpenAI API (필수)
OPENAI_API_KEY=sk-proj-...

# OpenSearch 연결 (필수)
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9201
```

#### 선택적 설정
```bash
# Google Cloud Vision (OCR 기능용)
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# 날씨 API (날씨 기반 추천용)
WEATHER_API_KEY=your_weather_api_key

# 서버 설정
HOST=0.0.0.0
PORT=8000
DEBUG=True
ENVIRONMENT=development
```

## 🤝 기여 가이드

1. 새로운 기능 개발 시 feature 브랜치 생성
2. 코드 변경 후 API 문서 업데이트
3. 테스트 실행 후 Pull Request 생성

## 📞 지원

- API 문서: http://localhost:8000/docs
- 이슈 리포트: GitHub Issues
- 개발팀 문의: [팀 연락처]

---

**⚠️ 주의사항**
- `.env` 파일은 절대 커밋하지 마세요 (민감한 정보 포함)
- OpenSearch(recipe-ai-project)가 실행 중이어야 AI 서버가 정상 작동합니다
- OpenAI API Key가 없으면 벡터 검색 기능이 제한됩니다
