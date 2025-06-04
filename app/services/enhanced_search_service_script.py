"""
강화된 검색 서비스 - OpenAI 기반 관련성 평가 적용

벡터 검색 + OpenAI 관련성 재평가 방식 사용
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
from ..utils.openai_relevance_scorer import AIEnhancedScoreCalculator
from ..utils.score_normalizer import ScoreNormalizer

def get_synonym_matcher():
    """동의어 매칭 대체 함수 - 추후 구현 예정"""
    return None  # 현재는 사용하지 않음

class EnhancedSearchService:
    def __init__(self):
        self.opensearch_client = OpenSearchClient()
        self.openai_client = OpenAIClient()
        self.ai_scorer = AIEnhancedScoreCalculator(min_score_threshold=70.0)  # 70점 이상만 반환
        self.synonym_matcher = get_synonym_matcher()

    async def semantic_search(
        self,
        query: str,
        search_type: str = "all",
        limit: int = 10
    ) -> SemanticSearchResponse:
        """
        하이브리드 시맨틱 검색 수행 - OpenAI 관련성 평가 적용
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
        """script_score를 사용한 재료 검색 (점수 정규화 적용)"""
        try:
            # 1. OpenAI 임베딩 생성
            query_vector = await self.openai_client.get_embedding(query)
            
            # 2. script_score 방식으로 벡터 검색
            vector_results = await self.opensearch_client.vector_search_ingredients(
                query_vector, limit
            )
            
            # 3. 텍스트 검색과 결합
            text_results = await self._text_search_ingredients(query, limit)
            
            # 4. 결과 통합 (점수 정규화 포함)
            combined_results = self._combine_ingredient_results_normalized(vector_results, text_results)
            
            return sorted(combined_results, key=lambda x: x.score, reverse=True)[:limit]
            
        except Exception as e:
            print(f"재료 검색 오류: {e}")
            # 벡터 검색 실패 시 텍스트 검색만 사용
            return await self._text_search_ingredients_only(query, limit)

    async def _search_recipes_script_score(self, query: str, limit: int) -> List[RecipeSearchResult]:
        """script_score를 사용한 레시피 검색 + OpenAI 관련성 평가"""
        try:
            # 1. OpenAI 임베딩 생성
            query_vector = await self.openai_client.get_embedding(query)
            
            # 2. script_score 방식으로 벡터 검색
            vector_results = await self.opensearch_client.search_recipes_by_ingredients(
                [query_vector], limit
            )
            
            # 3. 텍스트 검색
            text_results = await self._text_search_recipes(query, limit)
            
            # 4. 결과 통합 (점수 정규화 포함)
            combined_results = self._combine_recipe_results_normalized(vector_results, text_results)
            
            # 5. OpenAI 기반 관련성 평가 적용
            recipe_dicts = []
            for recipe in combined_results:
                recipe_dict = {
                    'rcp_seq': recipe.rcp_seq,
                    'rcp_nm': recipe.rcp_nm,
                    'rcp_category': recipe.rcp_category,
                    'rcp_way2': recipe.rcp_way2,
                    'image': recipe.image,
                    'thumbnail': recipe.thumbnail,
                    'score': recipe.score,
                    'match_reason': recipe.match_reason,
                    'ingredients': [{
                        'name': ing.name,
                        'ingredient_id': ing.ingredient_id,
                        'is_main_ingredient': ing.is_main_ingredient
                    } for ing in recipe.ingredients] if recipe.ingredients else []
                }
                recipe_dicts.append(recipe_dict)
            
            # OpenAI로 관련성 재평가
            enhanced_dicts = await self.ai_scorer.enhance_search_results(query, recipe_dicts)
            
            # 다시 RecipeSearchResult 객체로 변환
            final_results = []
            for recipe_dict in enhanced_dicts:
                ingredients = []
                for ing_dict in recipe_dict.get('ingredients', []):
                    ingredients.append(RecipeIngredient(
                        ingredient_id=ing_dict.get('ingredient_id', 0),
                        name=ing_dict.get('name', ''),
                        is_main_ingredient=ing_dict.get('is_main_ingredient', False)
                    ))
                
                final_results.append(RecipeSearchResult(
                    rcp_seq=recipe_dict['rcp_seq'],
                    rcp_nm=recipe_dict['rcp_nm'],
                    rcp_category=recipe_dict['rcp_category'],
                    rcp_way2=recipe_dict['rcp_way2'],
                    image=recipe_dict.get('image', ''),
                    thumbnail=recipe_dict.get('thumbnail', ''),
                    score=recipe_dict['score'],
                    match_reason=f"{recipe_dict['match_reason']} + AI 분석",
                    ingredients=ingredients
                ))
            
            return final_results[:limit]
            
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
        """텍스트 검색만 사용하는 재료 검색 (점수 정규화 적용)"""
        try:
            text_results = await self.opensearch_client.search_ingredients_by_text(query, limit)
            
            results = []
            for result in text_results:
                source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", {})
                original_score = result.get("score", result.get("_score", 0))
                
                results.append(IngredientSearchResult(
                    ingredient_id=source.get("ingredient_id", 0),
                    name=source.get("name", ""),
                    category=source.get("category", ""),
                    score=ScoreNormalizer.normalize_text_score(original_score),
                    match_reason="텍스트 매칭"
                ))
            
            return results
            
        except Exception as e:
            print(f"재료 텍스트 전용 검색 오류: {e}")
            return []

    async def _text_search_recipes_only(self, query: str, limit: int) -> List[RecipeSearchResult]:
        """텍스트 검색만 사용하는 레시피 검색 (점수 정규화 적용)"""
        try:
            text_results = await self.opensearch_client.search_recipes_by_text(query, limit)
            
            results = []
            for result in text_results:
                source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", {})
                original_score = result.get("score", result.get("_score", 0))
                
                results.append(RecipeSearchResult(
                    rcp_seq=str(source.get("recipe_id", "")),
                    rcp_nm=source.get("name", ""),
                    rcp_category=source.get("category", ""),
                    rcp_way2=source.get("cooking_method", ""),
                    image=source.get("image", ""),
                    thumbnail=source.get("thumbnail", ""),
                    score=ScoreNormalizer.normalize_text_score(original_score),
                    match_reason="텍스트 매칭",
                    ingredients=self._extract_recipe_ingredients_safe(source)
                ))
            
            return results
            
        except Exception as e:
            print(f"레시피 텍스트 전용 검색 오류: {e}")
            return []

    def _combine_ingredient_results_normalized(
        self,
        vector_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]]
    ) -> List[IngredientSearchResult]:
        """script_score 벡터 결과와 텍스트 결과 통합 (절대 점수 정규화 적용)"""
        combined = {}
        
        # 벡터 결과 추가
        for result in vector_results:
            source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", result)
            name = source.get("name", "")
            key = name.lower()
            
            if name and key not in combined:
                vector_score = result.get("score", result.get("_score", 0))
                # 벡터 점수 절대 정규화 (0-1 범위를 0-100%로)
                normalized_score = ScoreNormalizer.normalize_vector_score(vector_score)
                
                combined[key] = IngredientSearchResult(
                    ingredient_id=source.get("ingredient_id", 0),
                    name=name,
                    category=source.get("category", ""),
                    score=normalized_score,
                    match_reason="벡터 유사도"
                )
        
        # 텍스트 결과 추가
        for result in text_results:
            source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", result)
            name = source.get("name", "")
            key = name.lower()
            
            if name:
                text_score = result.get("score", result.get("_score", 0))
                normalized_text_score = ScoreNormalizer.normalize_text_score(text_score)
                
                if key in combined:
                    # 기존 벡터 결과와 하이브리드 점수 계산
                    hybrid_score = ScoreNormalizer.calculate_hybrid_score(
                        combined[key].score / 100.0,  # 0-1 범위로 변환
                        text_score,
                        vector_weight=0.6,
                        text_weight=0.4
                    )
                    combined[key].score = hybrid_score
                    combined[key].match_reason += " + 텍스트 매칭"
                else:
                    combined[key] = IngredientSearchResult(
                        ingredient_id=source.get("ingredient_id", 0),
                        name=name,
                        category=source.get("category", ""),
                        score=normalized_text_score,
                        match_reason="텍스트 매칭"
                    )
        
        return list(combined.values())

    def _combine_recipe_results_normalized(
        self,
        vector_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]]
    ) -> List[RecipeSearchResult]:
        """script_score 벡터 결과와 텍스트 결과 통합 (절대 점수 정규화 적용)"""
        combined = {}
        
        # 벡터 결과 추가
        for result in vector_results:
            source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", result)
            recipe_id = source.get("recipe_id", "")
            
            if recipe_id and recipe_id not in combined:
                vector_score = result.get("score", result.get("_score", 0))
                # 벡터 점수 절대 정규화 (0-1 범위를 0-100%로)
                normalized_score = ScoreNormalizer.normalize_vector_score(vector_score)
                
                combined[recipe_id] = RecipeSearchResult(
                    rcp_seq=str(recipe_id),
                    rcp_nm=source.get("name", ""),
                    rcp_category=source.get("category", ""),
                    rcp_way2=source.get("cooking_method", ""),
                    image=source.get("image", ""),
                    thumbnail=source.get("thumbnail", ""),
                    score=normalized_score,
                    match_reason="벡터 유사도",
                    ingredients=self._extract_recipe_ingredients_safe(source)
                )
        
        # 텍스트 결과 추가
        for result in text_results:
            source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", result)
            recipe_id = source.get("recipe_id", "")
            
            if recipe_id:
                text_score = result.get("score", result.get("_score", 0))
                normalized_text_score = ScoreNormalizer.normalize_text_score(text_score)
                
                if recipe_id in combined:
                    # 기존 벡터 결과와 하이브리드 점수 계산
                    hybrid_score = ScoreNormalizer.calculate_hybrid_score(
                        combined[recipe_id].score / 100.0,  # 0-1 범위로 변환
                        text_score,
                        vector_weight=0.6,
                        text_weight=0.4
                    )
                    combined[recipe_id].score = hybrid_score
                    combined[recipe_id].match_reason += " + 텍스트 매칭"
                else:
                    combined[recipe_id] = RecipeSearchResult(
                        rcp_seq=str(recipe_id),
                        rcp_nm=source.get("name", ""),
                        rcp_category=source.get("category", ""),
                        rcp_way2=source.get("cooking_method", ""),
                        image=source.get("image", ""),
                        thumbnail=source.get("thumbnail", ""),
                        score=normalized_text_score,
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
