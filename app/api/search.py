from fastapi import APIRouter, HTTPException
from typing import List, Optional
from ..models.schemas import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    RecipeSearchResult,
    IngredientSearchResult
)
<<<<<<< HEAD
from ..services.search_service import SearchService
=======
from app.services.enhanced_search_service import EnhancedSearchService
>>>>>>> dev

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    """
    시맨틱 검색 API
    
    - 레시피와 식재료를 동시에 검색
    - 검색어의 의미를 이해하여 관련성 높은 결과 반환
    - 검색 결과는 관련성 점수로 정렬
    """
    try:
        search_service = SearchService()
        results = await search_service.semantic_search(
            query=request.query,
            search_type=request.search_type,
            limit=request.limit
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 