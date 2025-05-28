from typing import List, Dict, Any
from ..models.schemas import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    RecipeSearchResult,
    IngredientSearchResult
)
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