"""
OpenAI 기반 관련성 점수 계산기

벡터 검색 결과를 OpenAI로 재평가하여 더 정확한 관련성 점수 제공
"""

import asyncio
from typing import List, Dict, Any
import json
from ..clients.openai_client import OpenAIClient

class OpenAIRelevanceScorer:
    def __init__(self):
        self.openai_client = OpenAIClient()
    
    async def score_recipes_relevance(
        self, 
        query: str, 
        recipes: List[Dict[str, Any]], 
        batch_size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        OpenAI를 사용해 레시피들의 관련성을 평가
        
        Args:
            query: 사용자 검색어 (예: "과일 파이")
            recipes: 평가할 레시피 리스트
            batch_size: 한 번에 평가할 레시피 수
        
        Returns:
            관련성 점수가 추가된 레시피 리스트
        """
        if not recipes:
            return recipes
        
        scored_recipes = []
        
        # 배치 단위로 처리 (OpenAI API 효율성)
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            batch_scores = await self._score_batch(query, batch)
            scored_recipes.extend(batch_scores)
        
        # 점수순 정렬
        scored_recipes.sort(key=lambda x: x.get('ai_relevance_score', 0), reverse=True)
        return scored_recipes
    
    async def _score_batch(self, query: str, recipe_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """배치 단위로 레시피 관련성 평가"""
        
        # 레시피 정보를 간단한 텍스트로 변환
        recipe_texts = []
        for i, recipe in enumerate(recipe_batch):
            recipe_name = recipe.get('rcp_nm', recipe.get('name', ''))
            ingredients = self._extract_ingredients_text(recipe)
            category = recipe.get('rcp_category', recipe.get('category', ''))
            
            recipe_text = f"{i+1}. 레시피: {recipe_name}"
            if category:
                recipe_text += f" (카테고리: {category})"
            if ingredients:
                recipe_text += f" - 주요재료: {ingredients}"
            
            recipe_texts.append(recipe_text)
        
        # OpenAI 프롬프트 구성
        prompt = self._create_scoring_prompt(query, recipe_texts)
        
        try:
            # OpenAI API 호출
            response = await self._call_openai_for_scoring(prompt)
            print(f"OpenAI 응답: {response}")
            scores = self._parse_scores_from_response(response)
            print(f"파싱된 점수: {scores}")
            
            # 결과에 점수 추가
            for i, recipe in enumerate(recipe_batch):
                recipe_name = recipe.get('rcp_nm', recipe.get('name', ''))
                ai_score = scores.get(str(i+1), 50.0)  # 기본값 50점
                original_score = recipe.get('score', 0)
                
                # 정확한 매칭 보너스 계산
                exact_match_bonus = self._calculate_exact_match_bonus(query, recipe_name)
                
                # 최종 점수 계산: AI 점수 + 정확 매칭 보너스
                final_score = min(ai_score + exact_match_bonus, 100.0)
                
                recipe['ai_relevance_score'] = ai_score
                recipe['exact_match_bonus'] = exact_match_bonus
                recipe['original_vector_score'] = original_score
                recipe['score'] = round(final_score, 2)
                
                print(f"  - {recipe_name}: AI={ai_score:.1f}, 보너스={exact_match_bonus:.1f}, 최종={final_score:.1f}")
            
            return recipe_batch
            
        except Exception as e:
            print(f"OpenAI 관련성 평가 오류: {e}")
            # 오류 시 원본 점수 유지
            for recipe in recipe_batch:
                recipe['ai_relevance_score'] = recipe.get('score', 50.0)
            return recipe_batch
    
    def _create_scoring_prompt(self, query: str, recipe_texts: List[str]) -> str:
        """고품질 OpenAI 점수 평가 프롬프트 생성"""
        
        recipes_text = "\n".join(recipe_texts)
        
        prompt = f"""사용자가 "{query}"를 검색했습니다.

다음 레시피들이 사용자의 검색 의도와 얼마나 관련이 있는지 0-100점으로 엄격하게 평가해주세요:

{recipes_text}

평가 기준:
- 검색어와 레시피명의 직접적 연관성 (가장 중요)
- 재료의 유사성 및 적합성
- 요리 방식이나 카테고리의 관련성
- 사용자가 실제로 찾고 있을 가능성

점수 가이드라인:
- 90-100점: 완전히 일치하거나 밀접하게 관련된 레시피
- 70-89점: 높은 관련성을 가진 레시피
- 50-69점: 보통 수준의 관련성
- 30-49점: 낮은 관련성
- 0-29점: 거의 무관하거나 전혀 다른 음식

응답 형식 (JSON):
{{
  "1": 85,
  "2": 72,
  "3": 15,
  "4": 90,
  "5": 8
}}

각 레시피에 대해 0-100 사이의 정수로 엄격하게 점수를 매겨주세요. 모든 레시피가 비슷한 점수를 받지 않도록 차이를 두어 평가해주세요."""

        return prompt
    
    async def _call_openai_for_scoring(self, prompt: str) -> str:
        """OpenAI API 호출"""
        try:
            response = await self.openai_client.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 음식 레시피의 관련성을 정확하게 평가하는 전문가입니다. 사용자의 검색 의도를 파악하고 각 레시피가 얼마나 적합한지 객관적으로 판단해주세요."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 일관성을 위해 낮은 temperature
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API 호출 오류: {e}")
            raise
    
    def _parse_scores_from_response(self, response: str) -> Dict[str, float]:
        """OpenAI 응답에서 점수 추출"""
        try:
            # JSON 응답 파싱
            scores_dict = json.loads(response)
            
            # 문자열 키를 유지하고 점수를 float로 변환
            parsed_scores = {}
            for key, value in scores_dict.items():
                try:
                    score = float(value)
                    # 점수 범위 검증 (0-100)
                    score = max(0.0, min(score, 100.0))
                    parsed_scores[str(key)] = score
                except (ValueError, TypeError):
                    parsed_scores[str(key)] = 50.0  # 기본값
            
            return parsed_scores
            
        except json.JSONDecodeError:
            print(f"OpenAI 응답 파싱 실패: {response}")
            # 파싱 실패 시 기본 점수 반환
            return {"1": 50.0, "2": 50.0, "3": 50.0, "4": 50.0, "5": 50.0}
    
    def _extract_ingredients_text(self, recipe: Dict[str, Any]) -> str:
        """레시피에서 재료 텍스트 추출"""
        try:
            ingredients = recipe.get('ingredients', [])
            
            if isinstance(ingredients, list):
                # 재료 객체 리스트인 경우
                ingredient_names = []
                for ing in ingredients[:5]:  # 처음 5개 재료만
                    if isinstance(ing, dict):
                        name = ing.get('name', '')
                    else:
                        name = str(ing)
                    
                    if name:
                        ingredient_names.append(name)
                
                return ", ".join(ingredient_names)
            
            elif isinstance(ingredients, str):
                # 문자열인 경우 처음 100자만
                return ingredients[:100]
            
            return ""
            
        except Exception as e:
            print(f"재료 추출 오류: {e}")
            return ""
    
    def _calculate_exact_match_bonus(self, query: str, recipe_name: str) -> float:
        """정확한 매칭 보너스 계산"""
        query_lower = query.lower().strip()
        name_lower = recipe_name.lower().strip()
        
        # 완전 일치
        if query_lower == name_lower:
            return 20.0  # 20점 보너스
        
        # 검색어가 레시피명에 포함
        if query_lower in name_lower:
            return 15.0  # 15점 보너스
        
        # 레시피명이 검색어에 포함
        if name_lower in query_lower:
            return 10.0  # 10점 보너스
        
        # 개별 단어 매칭
        query_words = set(query_lower.split())
        name_words = set(name_lower.split())
        
        common_words = query_words.intersection(name_words)
        if common_words:
            match_ratio = len(common_words) / len(query_words)
            return match_ratio * 10.0  # 최대 10점 보너스
        
        return 0.0  # 보너스 없음


# 기존 SmartScoreCalculator를 대체하는 간단한 래퍼
class AIEnhancedScoreCalculator:
    def __init__(self, min_score_threshold: float = 60.0):
        self.ai_scorer = OpenAIRelevanceScorer()
        self.min_score_threshold = min_score_threshold
    
    async def enhance_search_results(
        self, 
        query: str, 
        search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        검색 결과를 OpenAI로 재평가 및 점수 기준 필터링
        
        기존 SmartScoreCalculator.adjust_search_scores()를 대체
        """
        print(f"AI 기반 관련성 평가 시작: {len(search_results)}개 결과")
        
        # OpenAI로 관련성 평가
        enhanced_results = await self.ai_scorer.score_recipes_relevance(query, search_results)
        
        # 점수 기준으로 필터링
        filtered_results = [
            result for result in enhanced_results 
            if result.get('score', 0) >= self.min_score_threshold
        ]
        
        print(f"AI 기반 관련성 평가 완료: {len(enhanced_results)}개 → {len(filtered_results)}개 (기준: {self.min_score_threshold}점 이상)")
        
        return filtered_results
