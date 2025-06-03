"""
추천 서비스

업로드된 OpenSearch 데이터를 기반으로 레시피 추천을 제공합니다.
"""

from app.models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    RecipeScore,
    RecipeIngredient
)
from app.clients.opensearch_client import OpenSearchClient
from app.clients.openai_client import OpenAIClient
from typing import List, Dict, Any
import time
import logging

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self):
        self.opensearch_client = OpenSearchClient()
        self.openai_client = OpenAIClient()

    async def get_recommendations(
        self,
        request: RecommendationRequest
    ) -> RecommendationResponse:
        """
        재료 기반 레시피 추천을 제공합니다.
        """
        start_time = time.time()
        
        try:
            # 1. 재료 임베딩 생성
            ingredient_embeddings = await self._get_ingredient_embeddings(
                request.ingredients
            )
            
            # 2. OpenSearch에서 레시피 검색
            recipes = await self.opensearch_client.search_recipes_by_ingredients(
                ingredient_embeddings,
                limit=request.limit
            )
            
            # 3. 점수 계산 및 정렬
            scored_recipes = self._calculate_recipe_scores(
                recipes,
                request.ingredients
            )
            
            processing_time = time.time() - start_time
            
            # 4. 응답 포맷팅
            return RecommendationResponse(
                recipes=scored_recipes,
                total_matches=len(scored_recipes),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in get_recommendations: {str(e)}")
            raise

    async def _get_ingredient_embeddings(
        self,
        ingredients: List[str]
    ) -> List[List[float]]:
        """
        재료 목록의 임베딩을 생성합니다.
        """
        try:
            return await self.openai_client.get_embeddings(ingredients)
        except Exception as e:
            logger.error(f"Error in _get_ingredient_embeddings: {str(e)}")
            raise

    def _calculate_recipe_scores(
        self,
        recipes: List[Dict[str, Any]],
        requested_ingredients: List[str]
    ) -> List[RecipeScore]:
        """
        레시피 점수를 계산합니다.
        """
        scored_recipes = []
        
        for recipe in recipes:
            # 1. 재료 매칭 점수 계산
            ingredient_score = self._calculate_ingredient_score(
                recipe.get("ingredients", ""),
                requested_ingredients
            )
            
            # 2. 기본 검색 점수와 재료 매칭 점수 결합
            final_score = (recipe.get("score", 0) * 0.7) + (ingredient_score * 0.3)
            
            # 3. RecipeScore 객체 생성
            scored_recipe = RecipeScore(
                rcp_seq=recipe.get("recipe_id", ""),
                rcp_nm=recipe.get("name", ""),
                score=final_score,
                match_reason=self._generate_match_reason(
                    recipe,
                    requested_ingredients,
                    ingredient_score
                ),
                ingredients=self._extract_recipe_ingredients(recipe),
                rcp_way2=recipe.get("cooking_method", ""),
                rcp_category=recipe.get("category", "")
            )
            
            scored_recipes.append(scored_recipe)
        
        # 점수 기준 정렬
        return sorted(
            scored_recipes,
            key=lambda x: x.score,
            reverse=True
        )

    def _calculate_ingredient_score(
        self,
        recipe_ingredients_text: str,
        requested_ingredients: List[str]
    ) -> float:
        """
        재료 매칭 점수를 계산합니다.
        """
        if not recipe_ingredients_text:
            return 0.0
        
        recipe_ingredients = [
            ing.strip().lower() 
            for ing in recipe_ingredients_text.split(",")
        ]
        requested_lower = [ing.lower() for ing in requested_ingredients]
        
        # 매칭되는 재료 수 계산
        matches = 0
        for requested in requested_lower:
            for recipe_ing in recipe_ingredients:
                if requested in recipe_ing or recipe_ing in requested:
                    matches += 1
                    break
        
        # 매칭 비율 계산
        if len(requested_ingredients) == 0:
            return 0.0
        
        return min(matches / len(requested_ingredients), 1.0)

    def _generate_match_reason(
        self,
        recipe: Dict[str, Any],
        requested_ingredients: List[str],
        ingredient_score: float
    ) -> str:
        """
        매칭 이유를 생성합니다.
        """
        recipe_name = recipe.get("name", "레시피")
        
        if ingredient_score > 0.8:
            return f"{recipe_name}은(는) 요청하신 재료 대부분을 사용합니다"
        elif ingredient_score > 0.5:
            return f"{recipe_name}은(는) 요청하신 재료 일부를 사용합니다"
        else:
            return f"{recipe_name}은(는) 유사한 재료를 사용하는 레시피입니다"

    def _extract_recipe_ingredients(
        self, 
        recipe: Dict[str, Any]
    ) -> List[RecipeIngredient]:
        """
        레시피의 재료 정보를 추출합니다.
        """
        ingredients_text = recipe.get("ingredients", "")
        if not ingredients_text:
            return []
        
        ingredient_names = [name.strip() for name in ingredients_text.split(",")]
        
        ingredients = []
        for i, name in enumerate(ingredient_names):
            if name:
                ingredients.append(RecipeIngredient(
                    ingredient_id=i + 1,  # 임시 ID
                    name=name,
                    is_main_ingredient=(i < 3)  # 처음 3개를 주재료로 가정
                ))
        
        return ingredients