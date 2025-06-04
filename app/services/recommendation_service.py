"""
추천 서비스 (수정됨)

업로드된 OpenSearch 데이터를 기반으로 레시피 추천을 제공합니다.
매칭 이유 생성 로직을 개선하여 정확한 재료 매칭 정보를 제공합니다.
"""

from app.models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    RecipeScore,
    RecipeIngredient
)
from app.clients.opensearch_client import OpenSearchClient
from app.clients.openai_client import OpenAIClient
from typing import List, Dict, Any, Tuple, Set
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
            
            # 임베딩 생성에 실패하면 텍스트 검색으로 대체
            if not ingredient_embeddings:
                logger.warning("임베딩 생성 실패, 텍스트 검색으로 대체")
                # 재료들을 합쳐서 텍스트 검색
                ingredient_query = " ".join(request.ingredients)
                recipes = await self.opensearch_client.search_recipes_by_text(
                    ingredient_query,
                    limit=request.limit
                )
            else:
                # 2. OpenSearch에서 레시피 검색
                recipes = await self.opensearch_client.search_recipes_by_ingredients(
                    ingredient_embeddings,
                    limit=request.limit
                )
            
            # 디버깅: 첫 번째 레시피 데이터 구조 출력 (더 상세하게)
            if recipes:
                logger.info(f"전체 레시피 개수: {len(recipes)}")
                logger.info(f"첫 번째 레시피 데이터 구조: {list(recipes[0].keys())}")
                
                # 레시피 이름 관련 필드들 찾기
                sample_recipe = recipes[0]
                name_related_fields = {}
                for key, value in sample_recipe.items():
                    if any(keyword in key.lower() for keyword in ['name', 'nm', 'title', 'recipe']):
                        name_related_fields[key] = value
                        
                logger.info(f"이름 관련 필드들: {name_related_fields}")
                logger.info(f"전체 샘플 데이터: {sample_recipe}")
            else:
                logger.warning("검색된 레시피가 없습니다.")
            
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
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
            # 임베딩 생성 실패 시 비어있는 리스트 반환
            return []

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
            # 1. 재료 매칭 분석 (상세한 매칭 정보 포함)
            ingredient_analysis = self._analyze_ingredient_matching(
                recipe.get("ingredients", ""),
                requested_ingredients
            )
            
            # 2. 기본 검색 점수와 재료 매칭 점수 결합
            final_score = (recipe.get("score", 0) * 0.7) + (ingredient_analysis["score"] * 0.3)
            
            # 3. 실제 데이터 구조에 맞는 레시피 이름 찾기
            recipe_name = (
                recipe.get("name") or             # 실제 데이터에서 사용하는 필드
                recipe.get("rcp_nm") or 
                recipe.get("recipe_name") or 
                recipe.get("title") or
                recipe.get("RCP_NM") or
                recipe.get("recipeName") or
                str(recipe.get("_id", "레시피"))   # 최후의 수단으로 ID 사용
            )
            
            # 4. 실제 데이터 구조에 맞는 레시피 ID 찾기
            recipe_id = (
                recipe.get("recipe_id") or       # 실제 데이터에서 사용하는 필드
                recipe.get("rcp_seq") or 
                recipe.get("_id") or 
                ""
            )
            
            # 5. 실제 데이터 구조에 맞는 조리법 찾기
            cooking_method = (
                recipe.get("cooking_method") or  # 실제 데이터에서 사용하는 필드
                recipe.get("rcp_way2") or 
                ""
            )
            
            # 6. 실제 데이터 구조에 맞는 카테고리 찾기
            category = (
                recipe.get("category") or        # 실제 데이터에서 사용하는 필드
                recipe.get("rcp_category") or 
                ""
            )
            
            # 7. RecipeScore 객체 생성
            scored_recipe = RecipeScore(
                rcp_seq=str(recipe_id),
                rcp_nm=recipe_name,
                score=final_score,
                match_reason=self._generate_improved_match_reason(
                    recipe_name,
                    ingredient_analysis
                ),
                missing_ingredients=ingredient_analysis["missing_ingredients"],
                matched_ingredients=ingredient_analysis["matched_ingredients"],
                ingredients=self._extract_recipe_ingredients(recipe),
                rcp_way2=cooking_method,
                rcp_category=category
            )
            
            # 디버깅을 위한 로깅 추가
            logger.info(f"레시피: {recipe_name}")
            logger.info(f"매칭된 재료: {ingredient_analysis['matched_ingredients']}")
            logger.info(f"부족한 재료: {ingredient_analysis['missing_ingredients']}")
            logger.info(f"매칭 이유: {scored_recipe.match_reason}")
            
            scored_recipes.append(scored_recipe)
        
        # 점수 기준 정렬
        return sorted(
            scored_recipes,
            key=lambda x: x.score,
            reverse=True
        )

    def _analyze_ingredient_matching(
        self,
        recipe_ingredients_text: str,
        requested_ingredients: List[str]
    ) -> Dict[str, Any]:
        """
        재료 매칭을 상세히 분석합니다.
        
        Returns:
            Dict containing:
            - score: 매칭 점수 (0.0 ~ 1.0)
            - matched_ingredients: 매칭된 재료 목록
            - missing_ingredients: 부족한 재료 목록
            - total_recipe_ingredients: 레시피의 전체 재료 수
            - match_count: 매칭된 재료 수
        """
        if not recipe_ingredients_text or not requested_ingredients:
            return {
                "score": 0.0,
                "matched_ingredients": [],
                "missing_ingredients": requested_ingredients.copy(),
                "total_recipe_ingredients": 0,
                "match_count": 0
            }
        
        # 레시피 재료를 정리
        recipe_ingredients = [
            ing.strip().lower() 
            for ing in str(recipe_ingredients_text).split(",")
            if ing.strip()
        ]
        
        # 요청된 재료를 정리
        requested_lower = [ing.strip().lower() for ing in requested_ingredients]
        
        # 매칭 분석
        matched_ingredients = []
        missing_ingredients = []
        
        for requested in requested_lower:
            matched = False
            for recipe_ing in recipe_ingredients:
                # 정확한 매칭 또는 부분 매칭 확인
                if (requested in recipe_ing or 
                    recipe_ing in requested or
                    self._is_similar_ingredient(requested, recipe_ing)):
                    matched_ingredients.append(requested)
                    matched = True
                    break
            
            if not matched:
                missing_ingredients.append(requested)
        
        # 매칭 점수 계산
        if len(requested_ingredients) == 0:
            score = 0.0
        else:
            score = len(matched_ingredients) / len(requested_ingredients)
        
        return {
            "score": score,
            "matched_ingredients": matched_ingredients,
            "missing_ingredients": missing_ingredients,
            "total_recipe_ingredients": len(recipe_ingredients),
            "match_count": len(matched_ingredients)
        }

    def _is_similar_ingredient(self, ingredient1: str, ingredient2: str) -> bool:
        """
        두 재료가 유사한지 확인합니다.
        """
        # 동의어 매칭 로직 (확장 가능)
        synonyms = {
            "파프리카": ["피망", "빨간피망", "노란피망"],
            "양배추": ["배추", "캐비지"],
            "대파": ["파", "쪽파"],
            "오렌지": ["오렌지주스", "오랜지"],
            "당근": ["당근즙"]
        }
        
        for main_ingredient, synonym_list in synonyms.items():
            if ((ingredient1 == main_ingredient and ingredient2 in synonym_list) or
                (ingredient2 == main_ingredient and ingredient1 in synonym_list) or
                (ingredient1 in synonym_list and ingredient2 == main_ingredient) or
                (ingredient2 in synonym_list and ingredient1 == main_ingredient)):
                return True
        
        return False

    def _generate_improved_match_reason(
        self,
        recipe_name: str,
        ingredient_analysis: Dict[str, Any]
    ) -> str:
        """
        개선된 매칭 이유를 생성합니다.
        """
        matched_count = ingredient_analysis["match_count"]
        missing_count = len(ingredient_analysis["missing_ingredients"])
        total_requested = matched_count + missing_count
        
        # 모든 재료가 있는 경우
        if missing_count == 0 and matched_count > 0:
            # 모든 재료가 매칭되었으므로 missing_ingredients를 None으로 설정
            ingredient_analysis["missing_ingredients"] = None
            return "모든 재료 OK"
        
        # 일부 재료가 부족한 경우
        elif missing_count > 0:
            if missing_count == 1:
                missing_ingredient = ingredient_analysis["missing_ingredients"][0]
                return f"{missing_ingredient} 만 더 있으면 완성!"
            else:
                # 부족한 재료가 여러 개인 경우
                if missing_count <= 2:
                    missing_str = ", ".join(ingredient_analysis["missing_ingredients"])
                    return f"{missing_str} 만 더 있으면 완성!"
                else:
                    return f"{missing_count}개 재료 더 필요"
        
        # 매칭된 재료가 없는 경우
        else:
            return "유사한 재료로 만들 수 있는 레시피"

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
        
        ingredient_names = [name.strip() for name in str(ingredients_text).split(",")]
        
        ingredients = []
        for i, name in enumerate(ingredient_names[:10]):  # 최대 10개 재료
            if name:
                ingredients.append(RecipeIngredient(
                    ingredient_id=i + 1,  # 임시 ID
                    name=name,
                    is_main_ingredient=(i < 3)  # 처음 3개를 주재료로 가정
                ))
        
        return ingredients
