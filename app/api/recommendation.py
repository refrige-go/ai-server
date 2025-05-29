"""
레시피 추천 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException
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