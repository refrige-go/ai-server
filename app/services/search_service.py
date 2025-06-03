<<<<<<< HEAD
from typing import List, Dict, Any
=======
from fastapi import APIRouter, HTTPException
from typing import List, Optional
>>>>>>> dev
from ..models.schemas import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    RecipeSearchResult,
    IngredientSearchResult
)
<<<<<<< HEAD
from ..clients.opensearch_client import OpenSearchClient
from ..clients.openai_client import OpenAIClient

class SearchService:
    def __init__(self):
        self.opensearch_client = OpenSearchClient()
        self.openai_client = OpenAIClient()

    async def semantic_search(
        self,
        query: str,
        search_type: str = "all",
        limit: int = 10
    ) -> SemanticSearchResponse:
        """
        시맨틱 검색 수행
        
        1. 검색어를 벡터로 변환
        2. OpenSearch에서 벡터 검색 수행
        3. 검색 결과 정렬 및 가공
        """
        # 검색어를 벡터로 변환
        query_vector = await self.openai_client.get_embedding(query)
        
        # 검색 타입에 따라 다른 인덱스 검색
        results = {}
        if search_type in ["all", "recipe"]:
            recipe_results = await self.opensearch_client.vector_search(
                index="recipes",
                vector=query_vector,
                limit=limit
            )
            results["recipes"] = self._process_recipe_results(recipe_results)
            
        if search_type in ["all", "ingredient"]:
            ingredient_results = await self.opensearch_client.vector_search(
                index="ingredients",
                vector=query_vector,
                limit=limit
            )
            results["ingredients"] = self._process_ingredient_results(ingredient_results)
        
        return SemanticSearchResponse(
            recipes=results.get("recipes", []),
            ingredients=results.get("ingredients", []),
            total_matches=len(results.get("recipes", [])) + len(results.get("ingredients", [])),
            processing_time=0.0  # TODO: 실제 처리 시간 측정
        )

    def _process_recipe_results(self, results: List[Dict[str, Any]]) -> List[RecipeSearchResult]:
        """레시피 검색 결과 가공"""
        processed_results = []
        for result in results:
            processed_results.append(RecipeSearchResult(
                rcp_seq=result["_source"]["rcp_seq"],
                rcp_nm=result["_source"]["rcp_nm"],
                rcp_category=result["_source"]["rcp_category"],
                rcp_way2=result["_source"]["rcp_way2"],
                score=result["_score"],
                match_reason=self._generate_match_reason(result),
                ingredients=self._extract_ingredients(result)
            ))
        return processed_results

    def _process_ingredient_results(self, results: List[Dict[str, Any]]) -> List[IngredientSearchResult]:
        """식재료 검색 결과 가공"""
        processed_results = []
        for result in results:
            processed_results.append(IngredientSearchResult(
                ingredient_id=result["_source"]["id"],
                name=result["_source"]["name"],
                category=result["_source"]["category"],
                score=result["_score"],
                match_reason=self._generate_match_reason(result)
            ))
        return processed_results

    def _generate_match_reason(self, result: Dict[str, Any]) -> str:
        """매칭 이유 생성 (OpenAI 활용)"""
        # TODO: OpenAI를 사용하여 매칭 이유 생성
        return "관련성 높은 검색 결과"

    def _extract_ingredients(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """레시피의 재료 정보 추출"""
        # TODO: recipe_ingredients 테이블에서 재료 정보 조회
        return [] 
=======
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
>>>>>>> dev
