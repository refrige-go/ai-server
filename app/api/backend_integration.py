"""
백엔드 통합 API 엔드포인트
백엔드에서 호출할 수 있는 레시피 추천 API를 제공합니다.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
from app.services.recommendation_service import RecommendationService
from app.models.schemas import RecommendationRequest
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# 백엔드 호환 요청 스키마
class BackendRecipeRecommendationRequest(BaseModel):
    """백엔드에서 전달하는 레시피 추천 요청"""
    userId: Optional[str] = None
    selectedIngredients: List[str] = Field(..., min_items=1, description="선택된 재료 목록")
    limit: Optional[int] = Field(default=10, ge=1, le=50, description="추천 개수 제한")

# 백엔드 호환 응답 스키마
class BackendRecommendedRecipe(BaseModel):
    """백엔드로 반환할 추천 레시피 정보"""
    recipeId: str
    recipeName: str
    ingredients: str
    cookingMethod1: Optional[str] = ""
    cookingMethod2: Optional[str] = ""
    imageUrl: Optional[str] = None
    matchedIngredientCount: int
    matchedIngredients: List[str] = []
    isFavorite: bool = False
    matchScore: float

class BackendRecipeRecommendationResponse(BaseModel):
    """백엔드로 반환할 레시피 추천 응답"""
    recommendedRecipes: List[BackendRecommendedRecipe]
    totalCount: int
    selectedIngredients: List[str]
    processingTime: float

@router.post("/recipes", response_model=BackendRecipeRecommendationResponse)
async def recommend_recipes_for_backend(request: BackendRecipeRecommendationRequest):
    """
    백엔드에서 호출하는 레시피 추천 API
    
    Args:
        request: 백엔드에서 전달하는 추천 요청
        
    Returns:
        BackendRecipeRecommendationResponse: 백엔드 호환 형식의 추천 응답
    """
    start_time = time.time()
    
    try:
        logger.info(f"백엔드 레시피 추천 요청 - 사용자: {request.userId}, 재료: {request.selectedIngredients}")
        
        # 입력 검증
        if not request.selectedIngredients:
            raise HTTPException(status_code=400, detail="선택된 재료가 없습니다.")
        
        # AI 서버의 내부 추천 서비스 호출
        recommendation_request = RecommendationRequest(
            ingredients=request.selectedIngredients,
            limit=request.limit or 10,
            user_id=request.userId
        )
        
        recommendation_service = RecommendationService()
        ai_response = await recommendation_service.get_recommendations(recommendation_request)
        
        # AI 서버 응답을 백엔드 호환 형식으로 변환
        backend_recipes = []
        for recipe in ai_response.recipes:
            # 재료 리스트를 문자열로 변환
            ingredient_names = [ing.name for ing in recipe.ingredients]
            ingredients_text = ", ".join(ingredient_names) if ingredient_names else ""
            
            backend_recipe = BackendRecommendedRecipe(
                recipeId=recipe.rcp_seq,
                recipeName=recipe.rcp_nm,
                ingredients=ingredients_text,
                cookingMethod1="",  # AI 서버에는 상세 조리법이 없으므로 빈 값
                cookingMethod2="",
                imageUrl=None,  # AI 서버에는 이미지 URL이 없으므로 None
                matchedIngredientCount=len([ing for ing in recipe.ingredients if ing.is_main_ingredient]),
                matchedIngredients=ingredient_names,
                isFavorite=False,  # 북마크 정보는 백엔드에서 처리
                matchScore=recipe.score
            )
            backend_recipes.append(backend_recipe)
        
        processing_time = time.time() - start_time
        
        response = BackendRecipeRecommendationResponse(
            recommendedRecipes=backend_recipes,
            totalCount=len(backend_recipes),
            selectedIngredients=request.selectedIngredients,
            processingTime=processing_time
        )
        
        logger.info(f"백엔드 레시피 추천 완료 - {len(backend_recipes)}개 추천, 처리시간: {processing_time:.2f}초")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"백엔드 레시피 추천 중 오류: {str(e)}")
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"레시피 추천 중 오류가 발생했습니다: {str(e)}")

@router.get("/health")
async def backend_health_check():
    """백엔드용 헬스체크"""
    try:
        # OpenSearch 연결 테스트
        recommendation_service = RecommendationService()
        connection_ok = await recommendation_service.opensearch_client.test_connection()
        
        return {
            "status": "healthy" if connection_ok else "degraded",
            "ai_server": "running",
            "opensearch": "connected" if connection_ok else "disconnected",
            "services": {
                "recommendation": True,
                "semantic_search": connection_ok,
                "vector_search": connection_ok
            }
        }
    except Exception as e:
        logger.error(f"백엔드 헬스체크 실패: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
