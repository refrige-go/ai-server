"""
강화된 검색 서비스

동의어 사전 + 벡터 검색을 결합한 하이브리드 검색
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
        하이브리드 시맨틱 검색 수행
        """
        start_time = time.time()
        
        results = {}
        
        if search_type in ["all", "ingredient"]:
            ingredient_results = await self._search_ingredients_hybrid(query, limit)
            results["ingredients"] = ingredient_results
            
        if search_type in ["all", "recipe"]:
            recipe_results = await self._search_recipes_hybrid(query, limit)
            results["recipes"] = recipe_results
        
        processing_time = time.time() - start_time
        
        return SemanticSearchResponse(
            recipes=results.get("recipes", []),
            ingredients=results.get("ingredients", []),
            total_matches=len(results.get("recipes", [])) + len(results.get("ingredients", [])),
            processing_time=processing_time
        )

    async def _search_ingredients_hybrid(self, query: str, limit: int) -> List[IngredientSearchResult]:
        """재료 하이브리드 검색"""
        all_results = []
        
        # 1. 동의어 사전 검색
        synonym_results = self._search_ingredients_by_synonym(query)
        
        # 2. 벡터 검색
        vector_results = await self._search_ingredients_by_vector(query, limit)
        
        # 3. 텍스트 검색 (확장된 쿼리)
        expanded_queries = self.synonym_matcher.expand_ingredient_query(query)
        text_results = await self._search_ingredients_by_text(expanded_queries, limit)
        
        # 4. 결과 통합 및 점수 조정
        combined_results = self._combine_ingredient_results(
            synonym_results, vector_results, text_results
        )
        
        return sorted(combined_results, key=lambda x: x.score, reverse=True)[:limit]

    def _search_ingredients_by_synonym(self, query: str) -> List[IngredientSearchResult]:
        """동의어 사전 기반 재료 검색"""
        results = []
        
        # 정확 매칭
        exact_match = self.synonym_matcher.find_standard_ingredient(query)
        if exact_match:
            category, standard_name, confidence = exact_match
            results.append(IngredientSearchResult(
                ingredient_id=hash(standard_name) % 1000000,  # 임시 ID
                name=standard_name,
                category=category,
                score=confidence,
                match_reason=f"동의어 사전 정확 매칭 (신뢰도: {confidence:.2f})"
            ))
        
        # 유사 매칭
        similar_matches = self.synonym_matcher.find_similar_ingredients(query, limit=5)
        for category, standard_name, confidence in similar_matches:
            if confidence < 1.0:  # 정확 매칭이 아닌 경우만
                results.append(IngredientSearchResult(
                    ingredient_id=hash(standard_name) % 1000000,
                    name=standard_name,
                    category=category,
                    score=confidence * 0.8,  # 동의어 점수 가중치
                    match_reason=f"동의어 사전 유사 매칭 (신뢰도: {confidence:.2f})"
                ))
        
        return results

    async def _search_ingredients_by_vector(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """벡터 기반 재료 검색"""
        try:
            query_vector = await self.openai_client.get_embedding(query)
            results = await self.opensearch_client.vector_search(
                index="ingredients",
                vector=query_vector,
                limit=limit
            )
            return results
        except Exception as e:
            print(f"벡터 검색 오류: {e}")
            return []

    async def _search_ingredients_by_text(self, queries: List[str], limit: int) -> List[Dict[str, Any]]:
        """확장된 텍스트 검색"""
        all_results = []
        
        for query in queries[:3]:  # 상위 3개 쿼리만 사용
            try:
                results = await self.opensearch_client.search_ingredients_by_text(query, limit)
                all_results.extend(results)
            except Exception as e:
                print(f"텍스트 검색 오류: {e}")
        
        return all_results

    def _combine_ingredient_results(
        self,
        synonym_results: List[IngredientSearchResult],
        vector_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]]
    ) -> List[IngredientSearchResult]:
        """재료 검색 결과 통합"""
        combined = {}
        
        # 동의어 결과 추가 (높은 가중치)
        for result in synonym_results:
            key = result.name.lower()
            if key not in combined or combined[key].score < result.score:
                combined[key] = result
        
        # 벡터 결과 추가
        for result in vector_results:
            source = result["_source"]
            name = source.get("name", "")
            key = name.lower()
            
            vector_result = IngredientSearchResult(
                ingredient_id=source.get("ingredient_id", 0),
                name=name,
                category=source.get("category", ""),
                score=result["_score"] * 0.7,  # 벡터 점수 가중치
                match_reason="벡터 유사도 검색"
            )
            
            if key not in combined or combined[key].score < vector_result.score:
                combined[key] = vector_result
        
        # 텍스트 결과 추가
        for result in text_results:
            source = result["_source"]
            name = source.get("name", "")
            key = name.lower()
            
            text_result = IngredientSearchResult(
                ingredient_id=source.get("ingredient_id", 0),
                name=name,
                category=source.get("category", ""),
                score=result["_score"] * 0.6,  # 텍스트 점수 가중치
                match_reason="텍스트 매칭"
            )
            
            if key not in combined or combined[key].score < text_result.score:
                combined[key] = text_result
        
        return list(combined.values())

    async def _search_recipes_hybrid(self, query: str, limit: int) -> List[RecipeSearchResult]:
        """레시피 하이브리드 검색"""
        # 쿼리에서 재료 추출 및 확장
        expanded_queries = self.synonym_matcher.expand_ingredient_query(query)
        
        # 벡터 검색
        query_vector = await self.openai_client.get_embedding(query)
        vector_results = await self.opensearch_client.vector_search(
            index="recipes",
            vector=query_vector,
            limit=limit
        )
        
        # 확장된 텍스트 검색
        text_results = []
        for expanded_query in expanded_queries[:3]:
            try:
                results = await self.opensearch_client.search_recipes_by_text(expanded_query, limit)
                text_results.extend(results)
            except Exception as e:
                print(f"레시피 텍스트 검색 오류: {e}")
        
        # 결과 통합
        combined_results = self._combine_recipe_results(vector_results, text_results)
        
        return sorted(combined_results, key=lambda x: x.score, reverse=True)[:limit]

    def _combine_recipe_results(
        self,
        vector_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]]
    ) -> List[RecipeSearchResult]:
        """레시피 검색 결과 통합"""
        combined = {}
        
        # 벡터 결과 처리
        for result in vector_results:
            source = result["_source"]
            recipe_id = source.get("recipe_id", "")
            
            if recipe_id and recipe_id not in combined:
                combined[recipe_id] = RecipeSearchResult(
                    rcp_seq=recipe_id,
                    rcp_nm=source.get("name", ""),
                    rcp_category=source.get("category", ""),
                    rcp_way2=source.get("cooking_method", ""),
                    score=result["_score"],
                    match_reason="벡터 유사도 검색",
                    ingredients=self._extract_recipe_ingredients(source)
                )
        
        # 텍스트 결과 처리 (점수 부스트)
        for result in text_results:
            source = result["_source"]
            recipe_id = source.get("recipe_id", "")
            
            if recipe_id:
                text_score = result["_score"] * 0.8
                
                if recipe_id in combined:
                    # 기존 결과와 점수 결합
                    combined[recipe_id].score = max(combined[recipe_id].score, text_score)
                    combined[recipe_id].match_reason += " + 텍스트 매칭"
                else:
                    combined[recipe_id] = RecipeSearchResult(
                        rcp_seq=recipe_id,
                        rcp_nm=source.get("name", ""),
                        rcp_category=source.get("category", ""),
                        rcp_way2=source.get("cooking_method", ""),
                        score=text_score,
                        match_reason="텍스트 매칭",
                        ingredients=self._extract_recipe_ingredients(source)
                    )
        
        return list(combined.values())

    def _extract_recipe_ingredients(self, recipe_source: Dict[str, Any]) -> List[RecipeIngredient]:
        """레시피 재료 정보 추출"""
        ingredients_text = recipe_source.get("ingredients", "")
        if not ingredients_text:
            return []
        
        ingredient_names = [name.strip() for name in ingredients_text.split(",")]
        
        ingredients = []
        for i, name in enumerate(ingredient_names):
            if name:
                ingredients.append(RecipeIngredient(
                    ingredient_id=i + 1,
                    name=name,
                    is_main_ingredient=(i < 3)
                ))
        
        return ingredients