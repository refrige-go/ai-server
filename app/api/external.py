"""
외부 API 엔드포인트

이 파일은 날씨 및 계절 식재료 API 엔드포인트를 정의합니다.
주요 기능:
1. 날씨 기반 레시피 추천
2. 계절 식재료 조회
3. 날씨 정보 조회

구현 시 고려사항:
- API 응답 캐싱
- 에러 처리
- 응답 포맷 통일
- 비동기 처리
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    WeatherRecommendationRequest,
    WeatherRecommendationResponse,
    WeatherData,
    SeasonalIngredient
)
from app.services.weather_service import WeatherService
from typing import List

router = APIRouter()
weather_service = WeatherService()

@router.post("/weather/recommend", response_model=WeatherRecommendationResponse)
async def get_weather_recommendations(request: WeatherRecommendationRequest):
    """
    날씨 기반 레시피 추천을 제공합니다.
    
    Args:
        request: 위치 정보와 사용자 ID를 포함한 요청
        
    Returns:
        WeatherRecommendationResponse: 날씨 정보, 계절 식재료, 추천 레시피를 포함한 응답
    """
    # TODO: 구현 필요
    # 1. 날씨 정보 조회
    # 2. 계절 식재료 조회
    # 3. 레시피 추천
    # 4. 응답 포맷팅
    pass

@router.get("/weather/{location}", response_model=WeatherData)
async def get_weather(location: str):
    """
    특정 위치의 날씨 정보를 조회합니다.
    
    Args:
        location: 위치 정보 (도시명 또는 좌표)
        
    Returns:
        WeatherData: 날씨 정보
    """
    # TODO: 구현 필요
    pass

@router.get("/seasonal/{location}", response_model=List[SeasonalIngredient])
async def get_seasonal_ingredients(location: str):
    """
    특정 위치의 계절 식재료 정보를 조회합니다.
    
    Args:
        location: 위치 정보 (도시명 또는 좌표)
        
    Returns:
        List[SeasonalIngredient]: 계절 식재료 목록
    """
    # TODO: 구현 필요
    pass 