"""
점수 정규화 유틸리티 - score_normalizer.py 수정 (절대 정규화)

AI 서버에서 생성되는 다양한 점수들을 0-100% 범위로 정규화
"""

import math
from typing import List, Dict, Any

class ScoreNormalizer:
    
    @staticmethod
    def normalize_to_percentage(original_score: float, max_expected_score: float = 10.0) -> float:
        """
        원시 점수를 0-100% 범위로 정규화
        
        Args:
            original_score: AI 서버의 원시 점수
            max_expected_score: 예상되는 최대 점수 (기본값: 10.0)
        
        Returns:
            0-100 범위의 정규화된 점수
        """
        if original_score <= 0:
            return 0.0
        
        if max_expected_score <= 0:
            max_expected_score = 10.0
        
        # 정규화: (점수 / 최대예상점수) * 100, 최대 100%로 제한
        normalized_score = min((original_score / max_expected_score) * 100.0, 100.0)
        
        return round(normalized_score, 2)  # 소수점 2자리까지
    
    @staticmethod
    def normalize_vector_score(vector_score: float) -> float:
        """
        벡터 유사도 점수 정규화 (보통 0-1 범위지만 때로는 더 클 수 있음)
        """
        if vector_score <= 0:
            return 0.0
        
        # 1.0 이상이면 1.0으로 클램핑 후 백분율 변환
        clamped_score = min(vector_score, 1.0)
        return round(clamped_score * 100.0, 2)
    
    @staticmethod
    def normalize_text_score(text_score: float) -> float:
        """
        텍스트 검색 점수 정규화 (OpenSearch TF-IDF 점수는 보통 1-50 범위)
        """
        return ScoreNormalizer.normalize_to_percentage(text_score, 50.0)
    
    @staticmethod
    def normalize_scores_in_collection(items: List[Dict[str, Any]], score_key: str = 'score') -> List[Dict[str, Any]]:
        """
        컬렉션 내 모든 점수를 개별적으로 절대 점수로 정규화 (상대 정규화 아님)
        """
        if not items:
            return items
        
        # 각 점수를 개별적으로 절대 기준으로 정규화
        for item in items:
            original_score = item.get(score_key, 0)
            
            # 점수 범위에 따라 적절한 정규화 방법 선택
            if original_score <= 1.0:
                # 벡터 유사도 점수 (0-1 범위)
                normalized_score = ScoreNormalizer.normalize_vector_score(original_score)
            else:
                # 텍스트 검색 점수 (1-50+ 범위)
                normalized_score = ScoreNormalizer.normalize_text_score(original_score)
            
            item[score_key] = round(normalized_score, 2)
        
        print(f"컬렉션 점수 정규화 완료: {len(items)} 개 항목 (절대 기준)")
        
        return items
    
    @staticmethod
    def calculate_hybrid_score(vector_score: float, text_score: float, 
                             vector_weight: float = 0.6, text_weight: float = 0.4) -> float:
        """
        하이브리드 점수 계산 (벡터 + 텍스트)
        """
        normalized_vector = ScoreNormalizer.normalize_vector_score(vector_score)
        normalized_text = ScoreNormalizer.normalize_text_score(text_score)
        
        # 가중 평균
        hybrid_score = (normalized_vector * vector_weight + normalized_text * text_weight) / (vector_weight + text_weight)
        
        return round(hybrid_score, 2)
    
    @staticmethod
    def clamp_score(score: float, min_score: float = 0.0, max_score: float = 100.0) -> float:
        """
        점수를 지정된 범위로 제한
        """
        return max(min_score, min(score, max_score))
    
    @staticmethod
    def boost_score(score: float, boost_factor: float = 1.2, max_after_boost: float = 100.0) -> float:
        """
        점수 부스팅 (단, 최대값을 초과하지 않도록)
        """
        boosted = score * boost_factor
        return min(boosted, max_after_boost)

    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """
        안전한 나눗셈 (0으로 나누기 방지)
        """
        if denominator == 0:
            return default
        return numerator / denominator
