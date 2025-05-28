# 백엔드-AI 서버 연동 가이드

## 1. API 엔드포인트

AI 서버는 다음과 같은 API 엔드포인트를 제공합니다:

### 1.1 OCR API
- **엔드포인트**: `/api/ocr/process`
- **메서드**: POST
- **요청**: 
  - Content-Type: multipart/form-data
  - Body: image (파일)
- **응답**: OCRResponse
  ```json
  {
    "ingredients": [
      {
        "name": "string",
        "confidence": "float"
      }
    ]
  }
  ```

### 1.2 시맨틱 검색 API
- **엔드포인트**: `/api/search/semantic`
- **메서드**: POST
- **요청**: 
  ```json
  {
    "query": "string",
    "search_type": "recipe|ingredient",
    "limit": "integer"
  }
  ```
- **응답**: SemanticSearchResponse
  ```json
  {
    "recipes": [
      {
        "recipe_id": "string",
        "name": "string",
        "score": "float",
        "match_reason": "string"
      }
    ],
    "ingredients": [
      {
        "ingredient_id": "string",
        "name": "string",
        "score": "float",
        "match_reason": "string"
      }
    ]
  }
  ```

### 1.3 날씨 기반 추천 API
- **엔드포인트**: `/api/weather/recommend`
- **메서드**: POST
- **요청**: 
  ```json
  {
    "location": "string",
    "user_id": "string"
  }
  ```
- **응답**: WeatherRecommendationResponse
  ```json
  {
    "weather": {
      "temperature": "float",
      "condition": "string"
    },
    "seasonal_ingredients": [
      {
        "name": "string",
        "season": "string"
      }
    ],
    "recommended_recipes": [
      {
        "recipe_id": "string",
        "name": "string",
        "match_reason": "string"
      }
    ]
  }
  ```

## 2. 연동 설정

### 2.1 환경 변수 설정
`application.yml`에 다음 설정을 추가:
```yaml
ai:
  server:
    base-url: ${AI_SERVER_URL:http://localhost:8000}
    api-key: ${AI_SERVER_API_KEY:your-api-key-here}
```

### 2.2 AIServerConfig 설정
`AIServerConfig` 클래스가 이미 구현되어 있으므로 추가 설정 불필요.

### 2.3 AIServerClient 사용
`AIServerClient`를 주입받아 사용:
```java
@Autowired
private AIServerClient aiServerClient;
```

## 3. 컨트롤러 구현

### 3.1 OCR 컨트롤러
```java
@PostMapping("/ocr")
public ResponseEntity<Map<String, Object>> processOCR(@RequestParam("image") MultipartFile image) {
    try {
        Map<String, Object> result = aiServerClient.processOCR(image);
        return ResponseEntity.ok(result);
    } catch (IOException e) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
    }
}
```

### 3.2 검색 컨트롤러
```java
@PostMapping("/search")
public ResponseEntity<Map<String, Object>> search(@RequestBody Map<String, String> request) {
    Map<String, Object> result = aiServerClient.semanticSearch(
        request.get("query"),
        request.get("searchType")
    );
    return ResponseEntity.ok(result);
}
```

### 3.3 추천 컨트롤러
```java
@PostMapping("/recommendation")
public ResponseEntity<Map<String, Object>> getRecommendation(@RequestBody Map<String, Object> request) {
    String userId = SecurityContextHolder.getContext().getAuthentication().getName();
    Map<String, Object> result = aiServerClient.getRecommendation(
        userId,
        request.get("preferences")
    );
    return ResponseEntity.ok(result);
}
```

## 4. 에러 처리

### 4.1 공통 에러 응답
```java
@ExceptionHandler(Exception.class)
public ResponseEntity<ErrorResponse> handleException(Exception e) {
    ErrorResponse error = new ErrorResponse(
        HttpStatus.INTERNAL_SERVER_ERROR.value(),
        "AI 서버 연동 중 오류가 발생했습니다: " + e.getMessage()
    );
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
}
```

### 4.2 타임아웃 설정
```java
@Bean
public RestTemplate aiServerRestTemplate() {
    RestTemplate restTemplate = new RestTemplate();
    restTemplate.setRequestFactory(new SimpleClientHttpRequestFactory());
    ((SimpleClientHttpRequestFactory) restTemplate.getRequestFactory()).setConnectTimeout(5000);
    ((SimpleClientHttpRequestFactory) restTemplate.getRequestFactory()).setReadTimeout(5000);
    return restTemplate;
}
```

## 5. 테스트

### 5.1 단위 테스트
- AIServerClient 테스트
- 컨트롤러 테스트
- 에러 처리 테스트

### 5.2 통합 테스트
- AI 서버 연동 테스트
- 엔드투엔드 테스트

## 6. 모니터링

### 6.1 로깅
```java
@Slf4j
public class AIServerClient {
    public Map<String, Object> processOCR(MultipartFile image) throws IOException {
        log.info("OCR 처리 요청: {}", image.getOriginalFilename());
        // ... 처리 로직
        log.info("OCR 처리 완료: {} 개의 식재료 인식", result.size());
        return result;
    }
}
```

### 6.2 메트릭
- API 응답 시간
- 에러율
- 처리량

## 7. 보안

### 7.1 API 키 관리
- 환경 변수로 관리
- 정기적인 키 로테이션

### 7.2 요청 검증
- 입력값 검증
- 파일 크기 제한
- 파일 형식 검증

## 8. 성능 최적화

### 8.1 캐싱
- 검색 결과 캐싱
- 날씨 정보 캐싱

### 8.2 비동기 처리
- 대용량 이미지 처리
- 배치 처리

## 9. 배포 고려사항

### 9.1 환경별 설정
- 개발/스테이징/운영 환경 분리
- 환경별 API 키 관리

### 9.2 헬스 체크
- AI 서버 상태 확인
- 장애 감지 및 알림 