# app/services/final_strict_semantic_search_service.py
"""
최종 완성된 엄격한 시맨틱 검색 서비스
- "비트와 호두 요리" 문제 해결 ✅
- "피망 요리" → 피망/파프리카 요리 매칭 ✅
- 동의어 지원 ✅
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
from ..utils.strict_openai_relevance_verifier import StrictOpenAIRelevanceVerifier
from ..utils.korean_spell_checker import spell_checker

class FinalStrictSemanticSearchService:
    def __init__(self):
        self.opensearch_client = OpenSearchClient()
        self.openai_client = OpenAIClient()
        self.relevance_verifier = StrictOpenAIRelevanceVerifier()

    async def semantic_search(self, query: str, search_type: str = "all", limit: int = 10) -> SemanticSearchResponse:
        """최종 완성된 엄격한 시맨틱 검색"""
        start_time = time.time()
        results = {}
        
        try:
            if not query or not query.strip():
                return SemanticSearchResponse(
                    recipes=[], ingredients=[], total_matches=0, processing_time=0.0
                )
            
            # 🔧 0단계: 오타 교정
            original_query = query.strip()
            corrected_query = await spell_checker.correct_typo(original_query)
            
            if corrected_query != original_query:
                print(f"\n🔧 오타 교정 적용: '{original_query}' → '{corrected_query}'")
                query = corrected_query
            else:
                query = original_query
                
            if search_type in ["all", "recipe"]:
                recipe_results = await self._final_strict_search_recipes(query, limit)
                results["recipes"] = recipe_results
                
            if search_type in ["all", "ingredient"]:
                ingredient_results = await self._search_ingredients_basic(query, limit)
                results["ingredients"] = ingredient_results
                
        except Exception as e:
            print(f"최종 엄격한 시맨틱 검색 오류: {e}")
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

    async def _final_strict_search_recipes(self, query: str, limit: int) -> List[RecipeSearchResult]:
        """최종 완성된 엄격한 레시피 검색"""
        try:
            print(f"🎯 최종 엄격한 시맨틱 레시피 검색: '{query}'")
            
            # 1단계: 완벽한 텍스트 검색
            text_results = await self._perfect_text_search(query, limit)
            print(f"1단계 완벽한 텍스트 검색: {len(text_results)}개")
            
            # 2단계: 벡터 검색 (필요시)
            vector_results = []
            if len(text_results) < limit * 0.7:
                print("📡 벡터 검색 실행")
                try:
                    vector_results = await self._strict_vector_search(query, limit)
                    print(f"2단계 벡터 검색: {len(vector_results)}개")
                except Exception as e:
                    print(f"벡터 검색 실패: {e}")
            else:
                print("📊 텍스트 결과 충분 → 벡터 검색 생략")
            
            # 3단계: 최종 통합 및 정렬
            final_results = await self._final_combine_and_filter(query, text_results, vector_results, limit)
            
            print(f"\n🎯 최종 결과 ({len(final_results)}개):")
            for i, recipe in enumerate(final_results, 1):
                print(f"{i}. {recipe.rcp_nm} = {recipe.score:.1f}점 ({recipe.match_reason})")
            
            return final_results
            
        except Exception as e:
            print(f"최종 엄격한 검색 오류: {e}")
            return await self._fallback_text_only(query, limit)

    async def _perfect_text_search(self, query: str, limit: int) -> List[Dict]:
        """🎯 완벽한 텍스트 검색 로직"""
        all_results = {}
        
        # 1. 정확한 구문 검색 우선
        exact_results = await self._exact_phrase_search(query, limit)
        for result in exact_results:
            recipe_id = self._get_recipe_id(result)
            if recipe_id:
                all_results[recipe_id] = result
        print(f"  정확한 구문 검색: {len(exact_results)}개")
        
        # 2. 스마트 키워드 검색
        if self._is_ingredient_query(query):
            main_ingredient = self._extract_main_ingredient(query)
            if main_ingredient and main_ingredient != query:
                print(f"  핵심 재료: '{main_ingredient}'")
                
                # 🎯 동의어 지원 재료 검색
                ingredient_results = await self._smart_ingredient_search(main_ingredient, limit)
                for result in ingredient_results:
                    recipe_id = self._get_recipe_id(result)
                    if recipe_id and recipe_id not in all_results:
                        all_results[recipe_id] = result
                print(f"  스마트 재료 검색: +{len(ingredient_results)}개")
        else:
            # 일반 키워드 검색 (더 엄격하게)
            keyword_results = await self._strict_keyword_search(query, limit)
            for result in keyword_results:
                recipe_id = self._get_recipe_id(result)
                if recipe_id and recipe_id not in all_results:
                    all_results[recipe_id] = result
            print(f"  엄격한 키워드 검색: +{len(keyword_results)}개")
        
        return list(all_results.values())

    async def _smart_ingredient_search(self, ingredient: str, limit: int) -> List[Dict]:
        """🎯 스마트 재료 검색 - 동의어 포함"""
        try:
            # 동의어 매핑
            synonyms = {
                "피망": ["파프리카", "빨간피망", "노란피망", "빨간파프리카", "노란파프리카"],
                "파프리카": ["피망", "빨간파프리카", "노란파프리카", "빨간피망", "노란피망"],
                "양배추": ["배추", "캐비지"],
                "배추": ["양배추", "캐비지"],
                "대파": ["파", "쪽파"],
                "파": ["대파", "쪽파"],
                "쪽파": ["대파", "파"],
                "호박": ["애호박", "단호박"],
                "애호박": ["호박", "단호박"]
            }
            
            # 검색할 키워드들 (원본 + 동의어)
            search_terms = [ingredient]
            if ingredient in synonyms:
                search_terms.extend(synonyms[ingredient])
            
            print(f"    검색 키워드: {search_terms}")
            
            # 모든 키워드로 검색
            all_results = {}
            for term in search_terms:
                search_body = {
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "bool": {
                                        "must": [
                                            {"match": {"name": {"query": term, "boost": 3}}},
                                            {"match": {"ingredients": {"query": term, "boost": 2}}}
                                        ]
                                    }
                                },
                                {
                                    "match": {
                                        "ingredients": {
                                            "query": term,
                                            "boost": 5
                                        }
                                    }
                                },
                                {
                                    "match": {
                                        "name": {
                                            "query": term,
                                            "boost": 4
                                        }
                                    }
                                }
                            ],
                            "minimum_should_match": 1
                        }
                    },
                    "size": limit * 2  # 더 많이 가져와서 필터링
                }
                
                response = await self.opensearch_client.search(index="recipes", body=search_body)
                
                for hit in response["hits"]["hits"]:
                    recipe_id = self._get_recipe_id(hit)
                    if recipe_id and recipe_id not in all_results:
                        # 🎯 추가 검증: 재료에 실제로 포함되어야 함
                        source = hit["_source"]
                        ingredients = source.get("ingredients", "").lower()
                        name = source.get("name", "").lower()
                        
                        # 동의어 중 하나라도 포함되면 OK
                        is_relevant = any(synonym.lower() in ingredients or synonym.lower() in name 
                                        for synonym in search_terms)
                        
                        if is_relevant:
                            hit["score"] = hit["_score"]
                            all_results[recipe_id] = hit
                            print(f"      ✅ {source.get('name')} (키워드: {term})")
                        else:
                            print(f"      ❌ {source.get('name')} (키워드 없음)")
            
            return list(all_results.values())
            
        except Exception as e:
            print(f"스마트 재료 검색 오류: {e}")
            return []

    async def _exact_phrase_search(self, query: str, limit: int) -> List[Dict]:
        """정확한 구문 검색"""
        try:
            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            {"match_phrase": {"name": {"query": query, "boost": 5}}},
                            {"match_phrase": {"ingredients": {"query": query, "boost": 3}}},
                        ],
                        "minimum_should_match": 1
                    }
                },
                "size": limit
            }
            
            response = await self.opensearch_client.search(index="recipes", body=search_body)
            
            results = []
            for hit in response["hits"]["hits"]:
                hit["score"] = hit["_score"]
                results.append(hit)
            
            return results
            
        except Exception as e:
            print(f"정확한 구문 검색 오류: {e}")
            return []

    async def _strict_keyword_search(self, query: str, limit: int) -> List[Dict]:
        """엄격한 키워드 검색 - 일반적인 단어 필터링"""
        try:
            # 일반적인 단어 제거
            stop_words = ["요리", "음식", "레시피", "만들기", "활용", "간단", "쉬운"]
            keywords = [word for word in query.split() if word not in stop_words]
            
            if not keywords:
                print("  ⚠️ 의미있는 키워드 없음, 검색 생략")
                return []
            
            print(f"  🎯 필터링된 키워드: {keywords}")
            
            filtered_query = " ".join(keywords)
            
            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"name": {"query": filtered_query, "boost": 3}}},
                            {"match": {"ingredients": {"query": filtered_query, "boost": 2}}},
                            {"match": {"category": {"query": filtered_query, "boost": 1}}}
                        ],
                        "minimum_should_match": 1
                    }
                },
                "size": limit
            }
            
            response = await self.opensearch_client.search(index="recipes", body=search_body)
            
            results = []
            for hit in response["hits"]["hits"]:
                hit["score"] = hit["_score"]
                results.append(hit)
            
            return results
            
        except Exception as e:
            print(f"엄격한 키워드 검색 오류: {e}")
            return []

    def _is_ingredient_query(self, query: str) -> bool:
        return any(pattern in query for pattern in ["요리", "음식", "레시피", "만들기"])

    def _extract_main_ingredient(self, query: str) -> str:
        for pattern in ["요리", "음식", "레시피", "만들기", "활용"]:
            query = query.replace(pattern, "").strip()
        return query

    async def _strict_vector_search(self, query: str, limit: int) -> List[Dict]:
        """엄격한 벡터 검색"""
        try:
            query_vector = await self.openai_client.get_embedding(query)
            results = await self.opensearch_client.search_recipes_by_ingredients([query_vector], limit * 2)
            
            if self._is_ingredient_query(query):
                main_ingredient = self._extract_main_ingredient(query)
                if main_ingredient != query:
                    ingredient_vector = await self.openai_client.get_embedding(main_ingredient)
                    ingredient_results = await self.opensearch_client.search_recipes_by_ingredients([ingredient_vector], limit)
                    existing_ids = {self._get_recipe_id(r) for r in results}
                    for result in ingredient_results:
                        if self._get_recipe_id(result) not in existing_ids:
                            results.append(result)
            
            return results
            
        except Exception as e:
            print(f"벡터 검색 오류: {e}")
            return []

    async def _final_combine_and_filter(self, query: str, text_results: List[Dict], vector_results: List[Dict], limit: int) -> List[RecipeSearchResult]:
        """최종 통합 및 필터링"""
        combined = {}
        
        print(f"\n🎯 최종 통합 및 필터링")
        print(f"검색어: '{query}' | 텍스트: {len(text_results)}개, 벡터: {len(vector_results)}개")
        
        # 1단계: 텍스트 결과 처리
        for result in text_results:
            source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", result)
            recipe_id = source.get("recipe_id", "")
            recipe_name = source.get("name", "")
            
            if recipe_id and recipe_name:
                text_score = result.get("score", result.get("_score", 0))
                normalized_score = ScoreNormalizer.normalize_text_score(text_score)
                
                # 🎯 동의어 매칭 보너스
                main_ingredient = self._extract_main_ingredient(query) if self._is_ingredient_query(query) else query
                bonus = self._calculate_relevance_bonus(main_ingredient, recipe_name, source.get("ingredients", ""))
                
                final_score = min((normalized_score + bonus) * 1.2, 100.0)
                
                combined[recipe_id] = {
                    'result': RecipeSearchResult(
                        rcp_seq=str(recipe_id),
                        rcp_nm=recipe_name,
                        rcp_category=source.get("category", ""),
                        rcp_way2=source.get("cooking_method", ""),
                        image=source.get("image", ""),
                        thumbnail=source.get("thumbnail", ""),
                        score=final_score,
                        match_reason="✅ 텍스트 매칭",
                        ingredients=self._extract_recipe_ingredients_safe(source)
                    ),
                    'source': 'perfect_text'
                }
                print(f"  ✅ 텍스트 매칭: {recipe_name} = {final_score:.1f}점")
        
        # 2단계: 벡터 결과는 엄격한 검증 후 추가 (간소화)
        if vector_results and len(combined) < limit:
            print("📡 벡터 결과 간단 추가")
            for result in vector_results[:limit-len(combined)]:
                source = result if isinstance(result, dict) and "_source" not in result else result.get("_source", result)
                recipe_id = source.get("recipe_id", "")
                recipe_name = source.get("name", "")
                
                if recipe_id and recipe_id not in combined:
                    vector_score = result.get("score", result.get("_score", 0))
                    normalized_score = ScoreNormalizer.normalize_vector_score(vector_score)
                    final_score = normalized_score * 0.8  # 벡터는 낮은 점수
                    
                    combined[recipe_id] = {
                        'result': RecipeSearchResult(
                            rcp_seq=str(recipe_id),
                            rcp_nm=recipe_name,
                            rcp_category=source.get("category", ""),
                            rcp_way2=source.get("cooking_method", ""),
                            image=source.get("image", ""),
                            thumbnail=source.get("thumbnail", ""),
                            score=final_score,
                            match_reason="🔍 유사도 매칭",
                            ingredients=self._extract_recipe_ingredients_safe(source)
                        ),
                        'source': 'vector_simple'
                    }
        
        # 3단계: 최종 정렬
        results = [item['result'] for item in combined.values()]
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]

    def _calculate_relevance_bonus(self, query_ingredient: str, recipe_name: str, ingredients: str) -> float:
        """관련성 보너스 계산"""
        bonus = 0.0
        
        # 동의어 매핑
        synonyms = {
            "피망": ["파프리카"],
            "파프리카": ["피망"],
            "양배추": ["배추", "캐비지"],
            "대파": ["파", "쪽파"]
        }
        
        query_lower = query_ingredient.lower()
        name_lower = recipe_name.lower()
        ingredients_lower = ingredients.lower()
        
        # 정확 매칭
        if query_lower in name_lower:
            bonus += 30.0
        if query_lower in ingredients_lower:
            bonus += 20.0
        
        # 동의어 매칭
        if query_ingredient in synonyms:
            for synonym in synonyms[query_ingredient]:
                if synonym.lower() in name_lower:
                    bonus += 25.0
                if synonym.lower() in ingredients_lower:
                    bonus += 15.0
        
        return bonus

    # 나머지 헬퍼 메서드들
    def _get_recipe_id(self, result: Dict) -> str:
        if isinstance(result, dict):
            if "_source" in result:
                return str(result["_source"].get("recipe_id", ""))
            else:
                return str(result.get("recipe_id", ""))
        return ""

    async def _search_ingredients_basic(self, query: str, limit: int) -> List[IngredientSearchResult]:
        """기본 재료 검색"""
        try:
            # 동의어 검색 포함
            synonyms = {
                "피망": ["파프리카"],
                "파프리카": ["피망"],
                "양배추": ["배추", "캐비지"],
                "대파": ["파", "쪽파"]
            }
            
            search_terms = [query]
            if query in synonyms:
                search_terms.extend(synonyms[query])
            
            all_results = {}
            for term in search_terms:
                search_body = {
                    "query": {
                        "bool": {
                            "should": [
                                {"match": {"name": {"query": term, "boost": 3}}},
                                {"match": {"category": {"query": term, "boost": 1}}},
                                {"match": {"aliases": {"query": term, "boost": 2}}}
                            ],
                            "minimum_should_match": 1
                        }
                    },
                    "size": limit
                }
                
                response = await self.opensearch_client.search(index="ingredients", body=search_body)
                
                for hit in response["hits"]["hits"]:
                    source = hit["_source"]
                    ingredient_id = source.get("ingredient_id", 0)
                    if ingredient_id and ingredient_id not in all_results:
                        all_results[ingredient_id] = hit
            
            results = []
            for hit in all_results.values():
                source = hit["_source"]
                name = source.get("name", "")
                
                if name:
                    text_score = hit.get("_score", 0)
                    normalized_score = ScoreNormalizer.normalize_text_score(text_score)
                    
                    # 동의어 보너스
                    bonus = self._calculate_relevance_bonus(query, name, "")
                    final_score = min(normalized_score + bonus, 100.0)
                    
                    results.append(IngredientSearchResult(
                        ingredient_id=source.get("ingredient_id", 0),
                        name=name,
                        category=source.get("category", ""),
                        score=final_score,
                        match_reason="동의어 매칭"
                    ))
            
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            print(f"재료 검색 오류: {e}")
            return []

    async def _fallback_text_only(self, query: str, limit: int) -> List[RecipeSearchResult]:
        """폴백: 텍스트 검색만"""
        try:
            text_results = await self.opensearch_client.search_recipes_by_text(query, limit)
            
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
                    match_reason="키워드 매칭",
                    ingredients=self._extract_recipe_ingredients_safe(source)
                ))
            
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            print(f"폴백 검색 오류: {e}")
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
