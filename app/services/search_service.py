from fastapi import APIRouter, HTTPException
from typing import List, Optional
from ..models.schemas import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    RecipeSearchResult,
    IngredientSearchResult
)
from ..services.enhanced_search_service import EnhancedSearchService

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    """
    하이브리드 시맨틱 검색 API
    
    - 동의어 사전 + 벡터 검색 + 텍스트 검색 결합
    - 높은 정확도의 검색 결과 제공
    - 검색 결과는 관련성 점수로 정렬
    """
    try:
        search_service = EnhancedSearchService()
        results = await search_service.semantic_search(
            query=request.query,
            search_type=request.search_type,
            limit=request.limit
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/synonym-test/{ingredient}")
async def test_synonym_matching(ingredient: str):
    """동의어 매칭 테스트용 엔드포인트"""
    from ..utils.synonym_matcher import get_synonym_matcher
    
    matcher = get_synonym_matcher()
    
    # 표준명 찾기
    standard_match = matcher.find_standard_ingredient(ingredient)
    
    # 유사 재료 찾기
    similar_matches = matcher.find_similar_ingredients(ingredient)
    
    # 쿼리 확장
    expanded_queries = matcher.expand_ingredient_query(ingredient)
    
    return {
        "input": ingredient,
        "standard_match": standard_match,
        "similar_matches": similar_matches,
        "expanded_queries": expanded_queries
    }