"""
동의어 매칭 유틸리티

synonym_dictionary.json을 활용한 재료 매칭 기능
"""

import json
import os
from typing import List, Dict, Tuple, Optional
from functools import lru_cache

class SynonymMatcher:
    def __init__(self):
        self.synonym_dict = self._load_synonym_dictionary()
        self.reverse_dict = self._build_reverse_dictionary()
    
    def _load_synonym_dictionary(self) -> Dict:
        """동의어 사전 로드"""
        try:
            # 프로젝트 루트의 data 폴더에서 파일 로드
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            file_path = os.path.join(current_dir, "data", "synonym_dictionary.json")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"동의어 사전 로드 실패: {e}")
            return {}
    
    def _build_reverse_dictionary(self) -> Dict[str, Tuple[str, str]]:
        """역방향 매핑 사전 구축 (동의어 -> (카테고리, 표준명))"""
        reverse_dict = {}
        
        for category, ingredients in self.synonym_dict.items():
            for standard_name, synonyms in ingredients.items():
                # 표준명 자체도 매핑에 추가
                reverse_dict[standard_name.lower()] = (category, standard_name)
                
                # 모든 동의어 매핑
                for synonym in synonyms:
                    reverse_dict[synonym.lower()] = (category, standard_name)
        
        return reverse_dict
    
    def find_standard_ingredient(self, user_input: str) -> Optional[Tuple[str, str, float]]:
        """
        사용자 입력을 표준 재료명으로 매핑
        
        Args:
            user_input: 사용자가 입력한 재료명
            
        Returns:
            Tuple[카테고리, 표준명, 신뢰도] 또는 None
        """
        user_input_clean = user_input.strip().lower()
        
        # 1. 정확 매칭
        if user_input_clean in self.reverse_dict:
            category, standard_name = self.reverse_dict[user_input_clean]
            return (category, standard_name, 1.0)
        
        # 2. 부분 매칭 (포함 관계)
        best_match = None
        best_score = 0.0
        
        for synonym, (category, standard_name) in self.reverse_dict.items():
            # 입력이 동의어에 포함되는 경우
            if user_input_clean in synonym:
                score = len(user_input_clean) / len(synonym)
                if score > best_score:
                    best_match = (category, standard_name, score * 0.8)  # 부분 매칭은 점수 할인
                    best_score = score
            
            # 동의어가 입력에 포함되는 경우
            elif synonym in user_input_clean:
                score = len(synonym) / len(user_input_clean)
                if score > best_score:
                    best_match = (category, standard_name, score * 0.7)  # 더 큰 할인
                    best_score = score
        
        return best_match
    
    def find_similar_ingredients(self, user_input: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        """
        유사한 재료들을 찾아 반환
        
        Args:
            user_input: 사용자 입력
            limit: 반환할 최대 결과 수
            
        Returns:
            List[(카테고리, 표준명, 신뢰도)]
        """
        user_input_clean = user_input.strip().lower()
        matches = []
        
        for synonym, (category, standard_name) in self.reverse_dict.items():
            # 문자열 유사도 계산 (간단한 방식)
            similarity = self._calculate_similarity(user_input_clean, synonym)
            
            if similarity > 0.3:  # 최소 유사도 임계값
                matches.append((category, standard_name, similarity))
        
        # 점수 순으로 정렬하고 중복 제거
        matches = sorted(set(matches), key=lambda x: x[2], reverse=True)
        return matches[:limit]
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """간단한 문자열 유사도 계산"""
        # 공통 문자 비율 계산
        set1, set2 = set(str1), set(str2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def expand_ingredient_query(self, ingredient: str) -> List[str]:
        """
        재료명을 동의어로 확장
        
        Args:
            ingredient: 원본 재료명
            
        Returns:
            확장된 재료명 리스트 (원본 포함)
        """
        result = [ingredient]
        
        # 표준명 찾기
        match = self.find_standard_ingredient(ingredient)
        if match:
            category, standard_name, confidence = match
            
            # 해당 표준명의 모든 동의어 추가
            if category in self.synonym_dict and standard_name in self.synonym_dict[category]:
                synonyms = self.synonym_dict[category][standard_name]
                result.extend(synonyms)
        
        return list(set(result))  # 중복 제거

# 전역 인스턴스 (싱글톤 패턴)
_synonym_matcher = None

def get_synonym_matcher() -> SynonymMatcher:
    """동의어 매처 싱글톤 인스턴스 반환"""
    global _synonym_matcher
    if _synonym_matcher is None:
        _synonym_matcher = SynonymMatcher()
    return _synonym_matcher