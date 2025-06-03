"""
레시피 추천 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import RecommendationRequest, RecommendationResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter()

@router.post("/recommend", response_model=RecommendationResponse)
async def get_recipe_recommendations(request: RecommendationRequest):
    """
    재료 기반 레시피 추천을 제공합니다.
    
    Args:
        request: 재료 목록과 사용자 정보를 포함한 요청
        
    Returns:
        RecommendationResponse: 추천 레시피 목록과 점수
    """
    try:
        recommendation_service = RecommendationService()
        result = await recommendation_service.get_recommendations(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/by-ingredients")
async def recommend_by_ingredients(request: dict):
    """
    재료 기반 레시피 추천 (간단한 형식)
    
    Args:
        request: {"ingredients": ["재료1", "재료2"], "limit": 10}
        
    Returns:
        추천 레시피 목록
    """
    try:
        ingredients = request.get("ingredients", [])
        limit = request.get("limit", 10)
        
        if not ingredients:
            raise HTTPException(status_code=400, detail="재료 목록이 필요합니다")
        
        # RecommendationRequest 형식으로 변환 (user_preferences 제거)
        recommendation_request = RecommendationRequest(
            ingredients=ingredients,
            limit=limit
        )
        
        recommendation_service = RecommendationService()
        result = await recommendation_service.get_recommendations(recommendation_request)
        
        # 올바른 속성명 사용
        return {
            "recipes": result.recipes,
            "total": len(result.recipes),
            "processing_time": result.processing_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))