"""
스마트 하이브리드 검색 서비스

텍스트 검색 우선 + 벡터 검색으로 의미적 확장 + 스마트 필터링
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
from ..utils.score_normalizer import ScoreNormalizer

class SmartHybridSearchService:
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
        스마트 하이브리드 검색: 텍스트 우선 + 벡터 확장 + 스마트 필터링
        """
        start_time = time.time()
        
        results = {}
        
        try:
            if search_type in ["all", "ingredient"]:
                ingredient_results = await self._search_ingredients_hybrid(query, limit)
                results["ingredients"] = ingredient_results
                
            if search_type in ["all", "recipe"]:
                recipe_results = await self._search_recipes_hybrid(query, limit)
                results["recipes"] = recipe_results
        except Exception as e:
            print(f"검색 중 오류: {e}")
            import traceback
            print(f"오류 상세: {traceback.format_exc()}")
            results = {"recipes": [], "ingredients": []}
        
        processing_time = time.time() - start_time
        
        return SemanticSearchResponse(
            recipes=results.get("recipes", []),
            ingredients=results.get("ingredients", []),
            total_matches=len(results.get("recipes", [])) + len(results.get("ingredients", [])),
            processing_time=processing_time
        )

    async def _search_recipes_hybrid(self, query: str, limit: int) -> List[RecipeSearchResult]:
        """스마트 하이브리드 레시피 검색"""
        try:
            print(f"=== 스마트 하이브리드 레시피 검색: '{query}' ===")
            
            # 1단계: 텍스트 검색 (정확한 매칭)
            text_results = await self._text_search_recipes(query, limit)
            print(f"1단계 텍스트 검색: {len(text_results)}개")
            
            # 2단계: 벡터 검색 결정 (텍스트 결과가 부족할 때만)
            vector_results = []
            if len(text_results) < limit and self._should_use_vector_search(query, text_results):
                try:
                    query_vector = await self.openai_client.get_embedding(query)
                    vector_results = await self.opensearch_client.search_recipes_by_ingredients(
                        [query_vector], limit * 2
                    )
                    print(f"2단계 벡터 검색: {len(vector_results)}개")
                except Exception as e:
                    print(f"벡터 검색 실패: {e}")
            
            # 3단계: 스마트 통합 및 필터링
            final_results = self._smart_combine_and_filter(query, text_results, vector_results, limit)
            
            print("=== 최종 스마트 하이브리드 결과 ===")
            for i, recipe in enumerate(final_results, 1):
                print(f"{i}. {recipe.rcp_nm} = {recipe.score:.1f}점 ({recipe.match_reason})")
            
            return final_results
            
        except Exception as e:
            print(f"하이브리드 검색 오류: {e}")
            # 폴백: 텍스트 검색만
            return await self._fallback_text_search(query, limit)

    def _should_use_vector_search(self, query: str, text_results: List[Dict]) -> bool:
        """벡터 검색을 사용할지 결정하는 스마트 로직"""
        
        # 1. 텍스트 결과가 충분하면 벡터 검색 불필요
        if len(text_results) >= 8:
            print("  텍스트 결과 충분 → 벡터 검색 생략")
            return False
        
        # 2. 매우 구체적인 검색어면 벡터 검색 불필요
        specific_keywords = [
            # 특정 음식명
            "라면", "파스타", "피자", "햄버거", "김치찌개", "된장찌개",
            # 특정 재료명  
            "양파", "마늘", "돼지고기", "소고기", "닭고기",
            # 특정 브랜드
            "신라면", "짜파게티"
        ]
        
        query_lower = query.lower()
        for keyword in specific_keywords:
            if keyword in query_lower:
                print(f"  구체적 검색어 '{keyword}' 감지 → 벡터 검색 생략")
                return False
        
        # 3. 추상적이거나 의미적 검색어면 벡터 검색 활용
        semantic_keywords = [
            # 감정/상황
            "따뜻한", "시원한", "매운", "달콤한", "건강한", "다이어트",
            # 시간/상황
            "아침", "점심", "저녁", "야식", "간식", "술안주",
            # 추상적 개념
            "간단한", "빠른", "쉬운", "특별한", "고급", "집밥"
        ]
        
        for keyword in semantic_keywords:
            if keyword in query_lower:
                print(f"  의미적 검색어 '{keyword}' 감지 → 벡터 검색 활용")
                return True
        
        # 4. 텍스트 결과가 적으면 벡터로 보완
        if len(text_results) < 3:
            print(f"  텍스트 결과 부족 ({len(text_results)}개) → 벡터 검색으로 보완")
            return True
        
        print("  기본: 벡터 검색 생략")
        return False

    def _smart_combine_and_filter(
        self,
        query: str,
        text_results: List[Dict],
        vector_results: List[Dict],
        limit: int
    ) -> List[RecipeSearchResult]:
        """스마트 통합 및 필터링"""
        
        combined = {}
        query_lower = query.lower().strip()
        
        print("=== 스마트 통합 및 필터링 ===")
        
        # 1단계: 텍스트 결과 우선 처리 (높은 점수)
        for result in text_results:
            source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", result)
            recipe_id = source.get("recipe_id", "")
            recipe_name = source.get("name", "")
            ingredients_text = source.get("ingredients", "")
            
            if recipe_id and recipe_name:
                text_score = result.get("score", result.get("_score", 0))
                normalized_score = ScoreNormalizer.normalize_text_score(text_score)
                
                # 정확한 매칭 보너스
                exact_bonus = self._calculate_text_match_bonus(query_lower, recipe_name, ingredients_text)
                final_score = min(normalized_score + exact_bonus, 100.0)
                
                combined[recipe_id] = {
                    'result': RecipeSearchResult(
                        rcp_seq=str(recipe_id),
                        rcp_nm=recipe_name,
                        rcp_category=source.get("category", ""),
                        rcp_way2=source.get("cooking_method", ""),
                        image=source.get("image", ""),
                        thumbnail=source.get("thumbnail", ""),
                        score=final_score,
                        match_reason="텍스트 매칭",
                        ingredients=self._extract_recipe_ingredients_safe(source)
                    ),
                    'source': 'text'
                }
                
                print(f"  텍스트: {recipe_name} = {final_score:.1f}점")
        
        # 2단계: 벡터 결과 필터링 및 추가 (관련성 검증 후)
        for result in vector_results:
            source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", result)
            recipe_id = source.get("recipe_id", "")
            recipe_name = source.get("name", "")
            
            if recipe_id and recipe_id not in combined:  # 텍스트에 없는 것만
                # 벡터 결과 관련성 검증
                relevance_score = self._verify_vector_relevance(query_lower, recipe_name, source.get("ingredients", ""))
                
                if relevance_score >= 0.3:  # 30% 이상 관련성 있을 때만 추가
                    vector_score = result.get("score", result.get("_score", 0))
                    normalized_score = ScoreNormalizer.normalize_vector_score(vector_score)
                    
                    # 벡터 점수에 관련성 가중치 적용
                    final_score = normalized_score * relevance_score * 0.7  # 최대 70%
                    
                    combined[recipe_id] = {
                        'result': RecipeSearchResult(
                            rcp_seq=str(recipe_id),
                            rcp_nm=recipe_name,
                            rcp_category=source.get("category", ""),
                            rcp_way2=source.get("cooking_method", ""),
                            image=source.get("image", ""),
                            thumbnail=source.get("thumbnail", ""),
                            score=final_score,
                            match_reason=f"의미적 유사성 ({relevance_score*100:.0f}%)",
                            ingredients=self._extract_recipe_ingredients_safe(source)
                        ),
                        'source': 'vector'
                    }
                    
                    print(f"  벡터: {recipe_name} = {final_score:.1f}점 (관련성: {relevance_score*100:.0f}%)")
                else:
                    print(f"  벡터 필터링: {recipe_name} (관련성 {relevance_score*100:.0f}% < 30%)")
        
        # 3단계: 점수 순 정렬 및 반환
        results = [item['result'] for item in combined.values()]
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]

    def _verify_vector_relevance(self, query_lower: str, recipe_name: str, ingredients: str) -> float:
        """벡터 검색 결과의 관련성 검증 (0.0-1.0)"""
        
        recipe_name_lower = recipe_name.lower()
        ingredients_lower = str(ingredients).lower()
        
        # 1. 직접 매칭이 있으면 높은 관련성
        if (query_lower in recipe_name_lower or 
            query_lower in ingredients_lower):
            return 1.0
        
        # 2. 단어 단위 매칭 확인
        query_words = set(query_lower.split())
        recipe_words = set(recipe_name_lower.split())
        ingredient_words = set(ingredients_lower.split())
        all_words = recipe_words.union(ingredient_words)
        
        common_words = query_words.intersection(all_words)
        if common_words:
            word_match_ratio = len(common_words) / len(query_words)
            return max(word_match_ratio, 0.5)  # 최소 50% 관련성
        
        # 3. 카테고리 기반 관련성 (간단한 규칙)
        category_rules = {
            # 면류 관련
            "면": ["라면", "국수", "파스타", "우동", "냉면"],
            "볶음": ["볶음밥", "볶음면", "볶음"],
            "국물": ["찌개", "국", "탕", "스프"],
            "디저트": ["케이크", "쿠키", "파이", "타르트", "푸딩"]
        }
        
        for category, keywords in category_rules.items():
            if any(keyword in query_lower for keyword in keywords):
                if any(keyword in recipe_name_lower for keyword in keywords):
                    return 0.6  # 60% 관련성
        
        # 4. 기본적으로 낮은 관련성
        return 0.1

    def _calculate_text_match_bonus(self, query_lower: str, recipe_name: str, ingredients_text: str) -> float:
        """텍스트 매칭 보너스 계산"""
        recipe_name_lower = recipe_name.lower()
        ingredients_lower = str(ingredients_text).lower()
        
        if query_lower == recipe_name_lower:
            return 50.0  # 완전일치
        elif query_lower in recipe_name_lower:
            return 35.0  # 부분일치
        elif query_lower in ingredients_lower:
            return 25.0  # 재료일치
        else:
            # 단어 매칭
            query_words = set(query_lower.split())
            recipe_words = set(recipe_name_lower.split())
            ingredient_words = set(ingredients_lower.split())
            all_words = recipe_words.union(ingredient_words)
            
            common_words = query_words.intersection(all_words)
            if common_words:
                match_ratio = len(common_words) / len(query_words)
                return match_ratio * 20.0
        
        return 0.0

    # 나머지 메서드들...
    async def _search_ingredients_hybrid(self, query: str, limit: int) -> List[IngredientSearchResult]:
        """재료 하이브리드 검색 (간단 버전)"""
        try:
            text_results = await self._text_search_ingredients(query, limit)
            
            results = []
            for result in text_results:
                source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", {})
                name = source.get("name", "")
                
                if name:
                    text_score = result.get("score", result.get("_score", 0))
                    normalized_score = ScoreNormalizer.normalize_text_score(text_score)
                    
                    # 재료 정확 매칭
                    query_lower = query.lower()
                    name_lower = name.lower()
                    
                    if query_lower == name_lower:
                        bonus = 50.0
                        match_reason = "완전일치"
                    elif query_lower in name_lower or name_lower in query_lower:
                        bonus = 30.0
                        match_reason = "부분일치"
                    else:
                        bonus = 0.0
                        match_reason = "텍스트 매칭"
                    
                    final_score = min(normalized_score + bonus, 100.0)
                    
                    results.append(IngredientSearchResult(
                        ingredient_id=source.get("ingredient_id", 0),
                        name=name,
                        category=source.get("category", ""),
                        score=final_score,
                        match_reason=match_reason
                    ))
            
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            print(f"재료 검색 오류: {e}")
            return []

    async def _fallback_text_search(self, query: str, limit: int) -> List[RecipeSearchResult]:
        """폴백: 텍스트 검색만"""
        try:
            text_results = await self._text_search_recipes(query, limit)
            
            results = []
            for result in text_results:
                source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", {})
                
                text_score = result.get("score", result.get("_score", 0))
                normalized_score = ScoreNormalizer.normalize_text_score(text_score)
                
                results.append(RecipeSearchResult(
                    rcp_seq=str(source.get("recipe_id", "")),
                    rcp_nm=source.get("name", ""),
                    rcp_category=source.get("category", ""),
                    rcp_way2=source.get("cooking_method", ""),
                    image=source.get("image", ""),
                    thumbnail=source.get("thumbnail", ""),
                    score=normalized_score,
                    match_reason="텍스트 매칭",
                    ingredients=self._extract_recipe_ingredients_safe(source)
                ))
            
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            print(f"폴백 검색 오류: {e}")
            return []

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

    def _extract_recipe_ingredients_safe(self, recipe_source: Dict[str, Any]) -> List[RecipeIngredient]:
        """안전한 레시피 재료 정보 추출"""
        try:
            ingredients_text = recipe_source.get("ingredients", "") or ""
            if not ingredients_text:
                return []
            
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
            
            return ingredients[:10]
            
        except Exception as e:
            print(f"재료 추출 오류: {e}")
            return []
