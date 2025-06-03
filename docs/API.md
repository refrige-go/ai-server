# AI Recipe Search Server API

## 🔍 검색 API

### 1. 시멘틱 검색 (추천)
**하이브리드 검색 (텍스트 + 벡터)**

```http
POST /api/search/semantic
Content-Type: application/json

{
  "query": "김치찌개",
  "search_type": "all",  // "all", "recipe", "ingredient"
  "limit": 10
}
```

**응답:**
```json
{
  "recipes": [
    {
      "rcp_seq": "1001",
      "rcp_nm": "완자김치찌개",
      "rcp_category": "한식",
      "rcp_way2": "끓이기",
      "score": 0.95,
      "match_reason": "벡터 유사도 + 텍스트 매칭",
      "ingredients": [
        {
          "ingredient_id": 1,
          "name": "김치",
          "is_main_ingredient": true
        }
      ]
    }
  ],
  "ingredients": [...],
  "total_matches": 15,
  "processing_time": 0.8
}
```

### 2. 벡터 검색
**OpenAI 임베딩 기반 의미 검색**

```http
POST /api/search/vector
Content-Type: application/json

{
  "query": "김치찌개",
  "limit": 5
}
```

### 3. 레시피 텍스트 검색

```http
GET /api/search/recipes?query=김치찌개&limit=10
```

### 4. 재료 텍스트 검색

```http
GET /api/search/ingredients?query=김치&limit=10
```

## 🏥 헬스체크 API

### 서버 상태 확인
```http
GET /health
```

**응답:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-03T12:00:00Z",
  "version": "1.0.0"
}
```

### OpenSearch 연결 테스트
```http
GET /api/search/test
```

**응답:**
```json
{
  "status": "success",
  "recipe_count": 1132,
  "ingredient_count": 548,
  "sample_recipes": [...],
  "sample_ingredients": [...]
}
```

## 🔧 디버그 API

### 인덱스 정보 확인
```http
GET /api/search/debug/recipes
GET /api/search/debug/ingredients
```

### 벡터 검색 테스트
```http
GET /api/search/test-vector
```

## 📝 응답 형식

### 레시피 결과 (RecipeSearchResultDTO 호환)
```json
{
  "rcp_seq": "레시피 ID",
  "rcp_nm": "레시피명",
  "rcp_category": "카테고리", 
  "rcp_way2": "조리방법",
  "score": 0.95,
  "match_reason": "매칭 방식",
  "ingredients": [
    {
      "ingredient_id": 1,
      "name": "재료명",
      "is_main_ingredient": true
    }
  ]
}
```

### 재료 결과 (IngredientSearchResultDTO 호환)
```json
{
  "ingredient_id": 1,
  "name": "재료명",
  "category": "카테고리",
  "score": 0.9,
  "match_reason": "매칭 방식"
}
```

## 🚨 오류 응답

```json
{
  "detail": "오류 메시지",
  "status_code": 400
}
```

## 📊 검색 타입별 특징

| 검색 타입 | 장점 | 용도 |
|-----------|------|------|
| **시멘틱** | 가장 정확, 하이브리드 | 메인 검색 |
| **벡터** | 의미 기반, 유사도 | 추천 시스템 |
| **텍스트** | 빠름, 정확한 키워드 | 필터링 |