"""
강화된 검색 서비스 - script_score 벡터 검색 전용

test_vector_search_fixed.py와 동일한 방식 사용
"""

from typing import List, Dict, Any
import time
from ..models.schemas import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    RecipeSearchResult,
    IngredientSearchResult,
    RecipeIngredient
)
from ..clients.opensearch_client import OpenSearchClient
from ..clients.openai_client import OpenAIClient
from ..utils.synonym_matcher import get_synonym_matcher

class EnhancedSearchService:
    def __init__(self):
        self.opensearch_client = OpenSearchClient()
        self.openai_client = OpenAIClient()
        self.synonym_matcher = get_synonym_matcher()

    async def semantic_search(
        self,
        query: str,
        search_type: str = "all",
        limit: int = 10
    ) -> SemanticSearchResponse:
        """
        하이브리드 시맨틱 검색 수행 - script_score 벡터 검색 사용
        """
        start_time = time.time()
        
        results = {}
        
        try:
            if search_type in ["all", "ingredient"]:
                ingredient_results = await self._search_ingredients_script_score(query, limit)
                results["ingredients"] = ingredient_results
                
            if search_type in ["all", "recipe"]:
                recipe_results = await self._search_recipes_script_score(query, limit)
                results["recipes"] = recipe_results
        except Exception as e:
            print(f"검색 중 오류: {e}")
            import traceback
            print(f"오류 상세: {traceback.format_exc()}")
            # 빈 결과 반환
            results = {"recipes": [], "ingredients": []}
        
        processing_time = time.time() - start_time
        
        return SemanticSearchResponse(
            recipes=results.get("recipes", []),
            ingredients=results.get("ingredients", []),
            total_matches=len(results.get("recipes", [])) + len(results.get("ingredients", [])),
            processing_time=processing_time
        )

    async def _search_ingredients_script_score(self, query: str, limit: int) -> List[IngredientSearchResult]:
        """script_score를 사용한 재료 검색"""
        try:
            # 1. OpenAI 임베딩 생성
            query_vector = await self.openai_client.get_embedding(query)
            
            # 2. script_score 방식으로 벡터 검색 (test_vector_search_fixed.py 방식)
            vector_results = await self.opensearch_client.vector_search_ingredients(
                query_vector, limit
            )
            
            # 3. 텍스트 검색과 결합
            text_results = await self._text_search_ingredients(query, limit)
            
            # 4. 결과 통합
            combined_results = self._combine_ingredient_results_script(vector_results, text_results)
            
            return sorted(combined_results, key=lambda x: x.score, reverse=True)[:limit]
            
        except Exception as e:
            print(f"재료 검색 오류: {e}")
            # 벡터 검색 실패 시 텍스트 검색만 사용
            return await self._text_search_ingredients_only(query, limit)

    async def _search_recipes_script_score(self, query: str, limit: int) -> List[RecipeSearchResult]:
        """script_score를 사용한 레시피 검색"""
        try:
            # 1. OpenAI 임베딩 생성
            query_vector = await self.openai_client.get_embedding(query)
            
            # 2. script_score 방식으로 벡터 검색 (test_vector_search_fixed.py 방식)
            vector_results = await self.opensearch_client.search_recipes_by_ingredients(
                [query_vector], limit
            )
            
            # 3. 텍스트 검색
            text_results = await self._text_search_recipes(query, limit)
            
            # 4. 결과 통합
            combined_results = self._combine_recipe_results_script(vector_results, text_results)
            
            return sorted(combined_results, key=lambda x: x.score, reverse=True)[:limit]
            
        except Exception as e:
            print(f"레시피 검색 오류: {e}")
            # 벡터 검색 실패 시 텍스트 검색만 사용
            return await self._text_search_recipes_only(query, limit)

    async def _text_search_ingredients(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """재료 텍스트 검색"""
        try:
            return await self.opensearch_client.search_ingredients_by_text(query, limit)
        except Exception as e:
            print(f"재료 텍스트 검색 오류: {e}")
            return []

    async def _text_search_recipes(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """레시피 텍스트 검색"""
        try:
            return await self.opensearch_client.search_recipes_by_text(query, limit)
        except Exception as e:
            print(f"레시피 텍스트 검색 오류: {e}")
            return []

    async def _text_search_ingredients_only(self, query: str, limit: int) -> List[IngredientSearchResult]:
        """텍스트 검색만 사용하는 재료 검색"""
        try:
            text_results = await self.opensearch_client.search_ingredients_by_text(query, limit)
            
            results = []
            for result in text_results:
                source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", {})
                
                results.append(IngredientSearchResult(
                    ingredient_id=source.get("ingredient_id", 0),
                    name=source.get("name", ""),
                    category=source.get("category", ""),
                    score=result.get("score", result.get("_score", 0)),
                    match_reason="텍스트 매칭"
                ))
            
            return results
            
        except Exception as e:
            print(f"재료 텍스트 전용 검색 오류: {e}")
            return []

    async def _text_search_recipes_only(self, query: str, limit: int) -> List[RecipeSearchResult]:
        """텍스트 검색만 사용하는 레시피 검색"""
        try:
            text_results = await self.opensearch_client.search_recipes_by_text(query, limit)
            
            results = []
            for result in text_results:
                source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", {})
                
                results.append(RecipeSearchResult(
                    rcp_seq=str(source.get("recipe_id", "")),
                    rcp_nm=source.get("name", ""),
                    rcp_category=source.get("category", ""),
                    rcp_way2=source.get("cooking_method", ""),
                    score=result.get("score", result.get("_score", 0)),
                    match_reason="텍스트 매칭",
                    ingredients=self._extract_recipe_ingredients_safe(source)
                ))
            
            return results
            
        except Exception as e:
            print(f"레시피 텍스트 전용 검색 오류: {e}")
            return []

    def _combine_ingredient_results_script(
        self,
        vector_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]]
    ) -> List[IngredientSearchResult]:
        """script_score 벡터 결과와 텍스트 결과 통합"""
        combined = {}
        
        # 벡터 결과 추가 (높은 가중치)
        for result in vector_results:
            source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", result)
            name = source.get("name", "")
            key = name.lower()
            
            if name and key not in combined:
                combined[key] = IngredientSearchResult(
                    ingredient_id=source.get("ingredient_id", 0),
                    name=name,
                    category=source.get("category", ""),
                    score=result.get("score", result.get("_score", 0)) * 1.2,  # 벡터 점수 부스트
                    match_reason="벡터 유사도"
                )
        
        # 텍스트 결과 추가
        for result in text_results:
            source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", result)
            name = source.get("name", "")
            key = name.lower()
            
            if name:
                text_score = result.get("score", result.get("_score", 0))
                
                if key in combined:
                    # 기존 벡터 결과와 점수 결합
                    combined[key].score = max(combined[key].score, text_score)
                    combined[key].match_reason += " + 텍스트 매칭"
                else:
                    combined[key] = IngredientSearchResult(
                        ingredient_id=source.get("ingredient_id", 0),
                        name=name,
                        category=source.get("category", ""),
                        score=text_score,
                        match_reason="텍스트 매칭"
                    )
        
        return list(combined.values())

    def _combine_recipe_results_script(
        self,
        vector_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]]
    ) -> List[RecipeSearchResult]:
        """script_score 벡터 결과와 텍스트 결과 통합"""
        combined = {}
        
        # 벡터 결과 추가 (높은 가중치)
        for result in vector_results:
            source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", result)
            recipe_id = source.get("recipe_id", "")
            
            if recipe_id and recipe_id not in combined:
                combined[recipe_id] = RecipeSearchResult(
                    rcp_seq=str(recipe_id),
                    rcp_nm=source.get("name", ""),
                    rcp_category=source.get("category", ""),
                    rcp_way2=source.get("cooking_method", ""),
                    score=result.get("score", result.get("_score", 0)) * 1.2,  # 벡터 점수 부스트
                    match_reason="벡터 유사도",
                    ingredients=self._extract_recipe_ingredients_safe(source)
                )
        
        # 텍스트 결과 추가
        for result in text_results:
            source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", result)
            recipe_id = source.get("recipe_id", "")
            
            if recipe_id:
                text_score = result.get("score", result.get("_score", 0))
                
                if recipe_id in combined:
                    # 기존 벡터 결과와 점수 결합
                    combined[recipe_id].score = max(combined[recipe_id].score, text_score)
                    combined[recipe_id].match_reason += " + 텍스트 매칭"
                else:
                    combined[recipe_id] = RecipeSearchResult(
                        rcp_seq=str(recipe_id),
                        rcp_nm=source.get("name", ""),
                        rcp_category=source.get("category", ""),
                        rcp_way2=source.get("cooking_method", ""),
                        score=text_score,
                        match_reason="텍스트 매칭",
                        ingredients=self._extract_recipe_ingredients_safe(source)
                    )
        
        return list(combined.values())

    def _extract_recipe_ingredients_safe(self, recipe_source: Dict[str, Any]) -> List[RecipeIngredient]:
        """안전한 레시피 재료 정보 추출"""
        try:
            ingredients_text = recipe_source.get("ingredients", "") or ""
            if not ingredients_text:
                return []
            
            # 다양한 구분자로 분리 시도
            ingredient_names = []
            for separator in [",", "\n", ";", "|"]:
                if separator in ingredients_text:
                    ingredient_names = [name.strip() for name in str(ingredients_text).split(separator)]
                    break
            
            if not ingredient_names:
                ingredient_names = [str(ingredients_text).strip()]
            
            ingredients = []
            for i, name in enumerate(ingredient_names):
                if name and len(name.strip()) > 0:
                    ingredients.append(RecipeIngredient(
                        ingredient_id=i + 1,
                        name=name.strip(),
                        is_main_ingredient=(i < 3)
                    ))
            
            return ingredients[:10]  # 최대 10개 재료만
            
        except Exception as e:
            print(f"재료 추출 오류: {e}")
            return []