from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# OCR 관련 스키마
class RecognizedIngredient(BaseModel):
    original_text: str
    ingredient_id: Optional[int] = None
    matched_name: str
    confidence: float
    alternatives: List[str] = []

class OCRResponse(BaseModel):
    ingredients: List[RecognizedIngredient]
    confidence: float
    processing_time: float

# 레시피 추천 관련 스키마
class RecommendationRequest(BaseModel):
    ingredients: List[str]
    limit: int = Field(default=10, ge=1, le=50)
    user_id: Optional[str]

class RecipeIngredient(BaseModel):
    ingredient_id: int  # ingredients 테이블의 id와 매핑
    name: str
    is_main_ingredient: bool = False

class RecipeScore(BaseModel):
    rcp_seq: str  # recipes 테이블의 rcp_seq와 매핑
    rcp_nm: str   # recipes 테이블의 rcp_nm과 매핑
    score: float
    match_reason: str
    ingredients: List[RecipeIngredient]
    rcp_way2: str  # recipes 테이블의 rcp_way2와 매핑
    rcp_category: str  # recipes 테이블의 rcp_category와 매핑

class RecommendationResponse(BaseModel):
    recipes: List[RecipeScore]
    total_matches: int
    processing_time: float

# 날씨 기반 추천 관련 스키마
class WeatherData(BaseModel):
    temperature: float
    condition: str
    humidity: float
    feels_like: float
    location: str
    timestamp: datetime

class SeasonalIngredient(BaseModel):
    ingredient_id: int  # ingredients 테이블의 id와 매핑
    name: str
    category: str  # IngredientCategory enum과 매핑
    season: str
    confidence: float

class WeatherRecommendationRequest(BaseModel):
    location: str
    user_id: Optional[str]
    limit: int = Field(default=10, ge=1, le=50)

class WeatherRecommendationResponse(BaseModel):
    weather: WeatherData
    seasonal_ingredients: List[SeasonalIngredient]
    recipes: List[RecipeScore]
    recommendation_reason: str
    processing_time: float

# 에러 응답 스키마
class ErrorResponse(BaseModel):
    message: str
    detail: Optional[str] = None
    error_code: Optional[str] = None

# 시맨틱 검색 관련 스키마
class SemanticSearchRequest(BaseModel):
    query: str
    search_type: Literal["all", "recipe", "ingredient"] = "all"
    limit: int = Field(default=10, ge=1, le=50)

class RecipeSearchResult(BaseModel):
    rcp_seq: str
    rcp_nm: str
    rcp_category: str
    rcp_way2: str
    score: float
    match_reason: str
    ingredients: List[RecipeIngredient]

class IngredientSearchResult(BaseModel):
    ingredient_id: int
    name: str
    category: str
    score: float
    match_reason: str

class SemanticSearchResponse(BaseModel):
    recipes: List[RecipeSearchResult]
    ingredients: List[IngredientSearchResult]
    total_matches: int
    processing_time: float 