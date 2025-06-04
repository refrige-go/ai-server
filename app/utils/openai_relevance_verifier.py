# app/utils/openai_relevance_verifier.py
"""
OpenAI 기반 실시간 관련성 검증기
하드코딩 없는 동적 관련성 판단
"""

from typing import Dict, List, Any, Tuple
from ..clients.openai_client import OpenAIClient
import json
import asyncio

class OpenAIRelevanceVerifier:
    def __init__(self):
        self.openai_client = OpenAIClient()
        # 캐시로 반복 호출 최소화
        self._relevance_cache = {}
        
    async def verify_relevance(self, query: str, recipe_name: str, ingredients: str = "") -> Dict[str, Any]:
        """
        OpenAI로 검색어와 레시피의 관련성 실시간 검증
        
        Returns:
        {
            "relevance_score": 0.0-1.0,
            "is_relevant": True/False,
            "reasoning": "설명",
            "suggested_threshold": 0.0-1.0,
            "keywords_found": ["키워드1", "키워드2"]
        }
        """
        
        # 캐시 확인
        cache_key = f"{query.lower()}:{recipe_name.lower()}"
        if cache_key in self._relevance_cache:
            return self._relevance_cache[cache_key]
        
        prompt = f"""
다음 검색어와 레시피의 관련성을 분석해주세요:

검색어: "{query}"
레시피명: "{recipe_name}"
재료: "{ingredients[:200]}"

분석 요청사항:
1. 관련성 점수 (0.0-1.0):
   - 1.0: 완벽히 관련됨 (검색 의도와 정확히 일치)
   - 0.8: 매우 관련됨 (검색 의도에 잘 맞음)
   - 0.6: 관련됨 (검색 의도에 어느정도 맞음)
   - 0.4: 약간 관련됨 (관련성은 있지만 약함)
   - 0.2: 거의 관련없음 (억지로 연결 가능)
   - 0.0: 전혀 관련없음

2. 관련성 판단 (0.5 이상이면 relevant)

3. 판단 근거 설명

4. 이 검색어에 적절한 임계값 제안 (0.3-0.8)

5. 검색어에서 찾은 핵심 키워드들

특별히 고려할 점:
- 동의어 관계: 피망↔파프리카, 양배추↔배추, 대파↔파, 쪽파↔대파
- 상위-하위 관계: 볶음 요리 → 볶음밥, 볶음면, 피망 요리 → 피망볶음, 피망전 등
- 용도별 관계: 아침 음식 → 토스트, 시리얼, 계란 요리
- 재료 활용 검색의 경우:
  * "피망 요리" → 피망(파프리카)이 들어간 모든 요리 (피망볶음, 피망전, 피망샐러드 등)
  * "양파 요리" → 양파가 들어간 모든 요리
  * "닭고기 요리" → 닭고기가 들어간 모든 요리
- 상황별 관계: 겨울 음식 → 따뜻한 국물 요리, 아침 간단한 → 토스트, 계란 요리
- 조리법 관계: 볶음 → 볶음밥, 볶음면, 찌개 → 김치찌개, 된장찌개

검색 의도 파악:
- "재료명 + 요리"는 해당 재료를 사용한 요리를 찾는 것
- "상황 + 음식"은 그 상황에 맞는 음식을 찾는 것
- "조리법 + 음식"은 그 조리법으로 만든 음식을 찾는 것

JSON 형식으로 답변:
{{
    "relevance_score": 0.85,
    "is_relevant": true,
    "reasoning": "구체적인 판단 근거",
    "suggested_threshold": 0.5,
    "keywords_found": ["키워드1", "키워드2"]
}}
"""

        try:
            response = await self.openai_client.chat_completion([
                {"role": "system", "content": "당신은 음식 검색 관련성 판단 전문가입니다. 정확하고 일관성 있게 판단해주세요."},
                {"role": "user", "content": prompt}
            ])
            
            content = response.choices[0].message.content.strip()
            
            # JSON 추출
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
            
            result = json.loads(content)
            
            # 캐시 저장
            self._relevance_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            print(f"OpenAI 관련성 검증 실패: {e}")
            # 폴백: 간단한 키워드 매칭
            return self._fallback_relevance_check(query, recipe_name, ingredients)
    
    def _fallback_relevance_check(self, query: str, recipe_name: str, ingredients: str) -> Dict[str, Any]:
        """OpenAI 실패시 폴백 로직"""
        query_lower = query.lower()
        recipe_lower = recipe_name.lower()
        ingredients_lower = ingredients.lower()
        
        # 기본 키워드 매칭
        query_words = set(query_lower.split())
        recipe_words = set(recipe_lower.split())
        ingredient_words = set(ingredients_lower.split())
        all_words = recipe_words.union(ingredient_words)
        
        common_words = query_words.intersection(all_words)
        
        if query_lower in recipe_lower:
            relevance_score = 1.0
        elif common_words:
            relevance_score = len(common_words) / len(query_words)
        else:
            relevance_score = 0.0
        
        return {
            "relevance_score": relevance_score,
            "is_relevant": relevance_score >= 0.4,
            "reasoning": f"폴백 매칭: 공통단어 {common_words}",
            "suggested_threshold": 0.4,
            "keywords_found": list(common_words)
        }

    async def batch_verify_relevance(self, query: str, recipes: List[Dict]) -> List[Dict[str, Any]]:
        """여러 레시피의 관련성을 배치로 검증"""
        tasks = []
        for recipe in recipes:
            source = recipe if isinstance(recipe, dict) and "_source" not in recipe else recipe.get("_source", recipe)
            recipe_name = source.get("name", "")
            ingredients = source.get("ingredients", "")
            
            task = self.verify_relevance(query, recipe_name, ingredients)
            tasks.append(task)
        
        # 동시 실행으로 성능 향상
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"레시피 {i} 관련성 검증 실패: {result}")
                processed_results.append(self._fallback_relevance_check(
                    query, recipes[i].get("_source", {}).get("name", ""), 
                    recipes[i].get("_source", {}).get("ingredients", "")
                ))
            else:
                processed_results.append(result)
        
        return processed_results
