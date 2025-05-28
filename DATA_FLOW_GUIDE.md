# 데이터 흐름 가이드

## 1. OCR 처리 흐름 (영수증 이미지 분석)

### 1.1 클라이언트 → 백엔드
```http
POST /api/v1/ocr/process
Content-Type: multipart/form-data

[이미지 파일]
```

### 1.2 백엔드 → AI 서버
```http
POST http://localhost:8000/ocr/process
Content-Type: multipart/form-data

[이미지 파일]
```

### 1.3 AI 서버 처리
1. 이미지 전처리 (크기 조정, 노이즈 제거 등)
2. Google Vision API로 텍스트 추출
3. 추출된 텍스트를 ingredients 테이블과 매칭
4. 매칭 결과 반환

### 1.4 AI 서버 → 백엔드 응답
```json
{
    "ingredients": [
        {
            "original_text": "우유 1팩",
            "ingredient_id": 123,
            "matched_name": "우유",
            "confidence": 0.95,
            "alternatives": ["저지방우유", "고칼슘우유"]
        }
    ],
    "confidence": 0.92,
    "processing_time": 1.5
}
```

### 1.5 백엔드 처리
1. OCR 결과를 user_ingredients 테이블에 저장
2. 기본 유통기한 설정 (ingredients 테이블의 default_expiry_days 사용)
3. 응답 데이터 가공

### 1.6 백엔드 → 클라이언트 응답
```json
{
    "ingredients": [
        {
            "id": 456,
            "ingredient_id": 123,
            "custom_name": "우유 1팩",
            "purchase_date": "2024-03-20",
            "expiry_date": "2024-03-27",
            "is_frozen": false
        }
    ],
    "message": "OCR 처리 완료"
}
```

## 2. 레시피 추천 흐름

### 2.1 클라이언트 → 백엔드
```http
POST /api/v1/recommendations
Content-Type: application/json

{
    "ingredients": ["우유", "계란", "밀가루"],
    "limit": 10,
    "user_id": "123"
}
```

### 2.2 백엔드 → AI 서버
```http
POST http://localhost:8000/recommendation
Content-Type: application/json

{
    "ingredients": ["우유", "계란", "밀가루"],
    "limit": 10,
    "user_id": "123"
}
```

### 2.3 AI 서버 처리
1. OpenSearch에서 레시피 검색
2. OpenAI로 레시피 매칭 점수 계산
3. 점수 기반으로 레시피 정렬
4. 매칭 이유 생성

### 2.4 AI 서버 → 백엔드 응답
```json
{
    "recipes": [
        {
            "rcp_seq": "1001",
            "rcp_nm": "팬케이크",
            "score": 0.95,
            "match_reason": "사용 가능한 재료로 만들 수 있는 간단한 디저트",
            "ingredients": [
                {
                    "ingredient_id": 123,
                    "name": "우유",
                    "is_main_ingredient": true
                }
            ],
            "rcp_way2": "굽기",
            "rcp_category": "디저트"
        }
    ],
    "total_matches": 15,
    "processing_time": 2.1
}
```

### 2.5 백엔드 처리
1. recipes 테이블에서 상세 정보 조회
2. recipe_ingredients 테이블에서 재료 정보 조회
3. 사용자 북마크 정보 조회 (recipe_bookmarks 테이블)

### 2.6 백엔드 → 클라이언트 응답
```json
{
    "recipes": [
        {
            "rcp_seq": "1001",
            "rcp_nm": "팬케이크",
            "ingredients": [
                {
                    "ingredient_id": 123,
                    "name": "우유",
                    "is_main_ingredient": true
                }
            ],
            "cooking_method": "굽기",
            "category": "디저트",
            "is_bookmarked": false
        }
    ],
    "total_matches": 15
}
```

## 3. 날씨 기반 추천 흐름

### 3.1 클라이언트 → 백엔드
```http
POST /api/v1/weather/recommendations
Content-Type: application/json

{
    "location": "서울",
    "user_id": "123",
    "limit": 10
}
```

### 3.2 백엔드 → AI 서버
```http
POST http://localhost:8000/weather/recommend
Content-Type: application/json

{
    "location": "서울",
    "user_id": "123",
    "limit": 10
}
```

### 3.3 AI 서버 처리
1. 날씨 API로 현재 날씨 정보 조회
2. 계절별 식재료 API로 제철 식재료 조회
3. OpenSearch에서 날씨/계절에 맞는 레시피 검색
4. OpenAI로 레시피 매칭 점수 계산

### 3.4 AI 서버 → 백엔드 응답
```json
{
    "weather": {
        "temperature": 25.5,
        "condition": "맑음",
        "humidity": 65.0,
        "feels_like": 27.0,
        "location": "서울",
        "timestamp": "2024-03-20T14:30:00"
    },
    "seasonal_ingredients": [
        {
            "ingredient_id": 456,
            "name": "딸기",
            "category": "과일",
            "season": "봄",
            "confidence": 0.95
        }
    ],
    "recipes": [
        {
            "rcp_seq": "2001",
            "rcp_nm": "딸기 샐러드",
            "score": 0.92,
            "match_reason": "제철 딸기를 활용한 상큼한 샐러드",
            "ingredients": [
                {
                    "ingredient_id": 456,
                    "name": "딸기",
                    "is_main_ingredient": true
                }
            ],
            "rcp_way2": "생식",
            "rcp_category": "샐러드"
        }
    ],
    "recommendation_reason": "오늘은 맑고 따뜻한 날씨에 딸기가 제철입니다.",
    "processing_time": 2.5
}
```

### 3.5 백엔드 처리
1. recipes 테이블에서 상세 정보 조회
2. recipe_ingredients 테이블에서 재료 정보 조회
3. 사용자 북마크 정보 조회

### 3.6 백엔드 → 클라이언트 응답
```json
{
    "weather": {
        "temperature": 25.5,
        "condition": "맑음",
        "humidity": 65.0,
        "feels_like": 27.0,
        "location": "서울"
    },
    "seasonal_ingredients": [
        {
            "id": 456,
            "name": "딸기",
            "category": "과일",
            "season": "봄"
        }
    ],
    "recipes": [
        {
            "rcp_seq": "2001",
            "rcp_nm": "딸기 샐러드",
            "ingredients": [
                {
                    "ingredient_id": 456,
                    "name": "딸기",
                    "is_main_ingredient": true
                }
            ],
            "cooking_method": "생식",
            "category": "샐러드",
            "is_bookmarked": false
        }
    ],
    "recommendation_reason": "오늘은 맑고 따뜻한 날씨에 딸기가 제철입니다."
}
```

## 주의사항

1. **에러 처리**
   - 각 단계별 적절한 에러 처리 필요
   - 타임아웃 설정
   - 재시도 로직 구현

2. **보안**
   - API 키 관리
   - 사용자 인증/인가
   - 데이터 검증

3. **성능**
   - 캐싱 전략
   - 비동기 처리
   - 연결 풀링

4. **모니터링**
   - API 호출 로깅
   - 성능 메트릭 수집
   - 에러 추적 