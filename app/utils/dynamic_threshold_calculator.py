# app/utils/dynamic_threshold_calculator.py
"""
동적 임계값 계산기
검색 상황에 따라 임계값을 동적으로 조정
"""

from typing import List

class DynamicThresholdCalculator:
    
    @staticmethod
    def calculate_threshold(
        query: str,
        text_results_count: int,
        openai_suggestions: List[float] = None
    ) -> float:
        """
        검색 상황에 따른 동적 임계값 계산
        
        Args:
            query: 검색어
            text_results_count: 텍스트 검색 결과 수
            openai_suggestions: OpenAI가 제안한 임계값들
        
        Returns:
            적절한 임계값 (0.0-1.0)
        """
        
        # 기본 임계값
        base_threshold = 0.5
        
        # 1. 텍스트 검색 결과에 따른 조정
        if text_results_count >= 10:
            # 텍스트 결과가 많으면 벡터 검색을 엄격하게
            text_bonus = 0.2
        elif text_results_count >= 5:
            text_bonus = 0.1
        elif text_results_count >= 1:
            text_bonus = 0.0
        else:
            # 텍스트 결과가 없으면 벡터 검색을 관대하게
            text_bonus = -0.2
        
        # 2. 검색어 길이에 따른 조정
        query_length = len(query.split())
        if query_length >= 5:
            # 긴 검색어는 더 관대하게 (의미적 검색 중요)
            length_bonus = -0.1
        elif query_length == 1:
            # 짧은 검색어는 더 엄격하게
            length_bonus = 0.1
        else:
            length_bonus = 0.0
        
        # 3. OpenAI 제안값 반영
        if openai_suggestions and len(openai_suggestions) > 0:
            # OpenAI 제안값들의 평균 사용
            avg_suggestion = sum(openai_suggestions) / len(openai_suggestions)
            # 기본값과 가중평균
            openai_bonus = (avg_suggestion - base_threshold) * 0.3
        else:
            openai_bonus = 0.0
        
        # 최종 임계값 계산
        final_threshold = base_threshold + text_bonus + length_bonus + openai_bonus
        
        # 범위 제한 (0.2 ~ 0.8)
        final_threshold = max(0.2, min(0.8, final_threshold))
        
        print(f"동적 임계값 계산:")
        print(f"  기본값: {base_threshold}")
        print(f"  텍스트 보정: {text_bonus} (결과수: {text_results_count})")
        print(f"  길이 보정: {length_bonus} (단어수: {query_length})")
        print(f"  AI 보정: {openai_bonus}")
        print(f"  최종 임계값: {final_threshold}")
        
        return final_threshold
