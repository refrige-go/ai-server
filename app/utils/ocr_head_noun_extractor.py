"""
한국어 복합명사구에서 핵심 명사(Head Noun) 추출 유틸리티

복합명사구 예시:
- "딸기 우유" → "우유" (핵심)
- "치즈 라면" → "라면" (핵심)  
- "복숭아 아이스티" → "아이스티" (핵심)
- "바닐라 아이스크림" → "아이스크림" (핵심)
"""

import re
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class NounPhraseAnalysis:
    """명사구 분석 결과"""
    original_phrase: str
    head_noun: str
    modifiers: List[str]
    confidence: float
    reasoning: str
    extraction_method: str

class HeadNounExtractor:
    """한국어 복합명사구에서 핵심 명사 추출기"""
    
    def __init__(self):
        # 1. 기본 식품/음료 카테고리 (핵심 명사 후보)
        self.base_food_categories = {
            # 음료류
            "음료": ["우유", "주스", "커피", "차", "아이스티", "탄산음료", "스무디", "쉐이크", "에이드"],
            # 주식류  
            "주식": ["밥", "라면", "국수", "파스타", "피자", "햄버거", "샌드위치", "토스트"],
            # 반찬류
            "반찬": ["찌개", "국", "탕", "볶음", "구이", "튀김", "무침", "나물"],
            # 디저트류
            "디저트": ["아이스크림", "케이크", "빵", "쿠키", "초콜릿", "젤리", "푸딩"],
            # 과일류
            "과일": ["사과", "바나나", "오렌지", "포도", "딸기", "복숭아", "키위"],
            # 채소류
            "채소": ["양파", "당근", "브로콜리", "시금치", "상추", "양배추", "파프리카"],
            # 육류
            "육류": ["돼지고기", "소고기", "닭고기", "양고기", "오리고기"],
            # 해산물
            "해산물": ["생선", "새우", "게", "조개", "굴", "문어", "오징어"]
        }
        
        # 2. 수식어 패턴 (맛, 색상, 종류 등을 나타내는 단어들)
        self.modifier_patterns = {
            # 맛 관련
            "flavor": ["달콤한", "신맛", "쓴맛", "매운", "짭짤한", "고소한", "새콤달콤한"],
            # 색상 관련  
            "color": ["빨간", "노란", "초록", "파란", "보라", "주황", "분홍"],
            # 종류 관련
            "type": ["딸기", "바닐라", "초코", "커피", "녹차", "레몬", "오렌지", "포도", "복숭아"],
            # 크기 관련
            "size": ["큰", "작은", "미니", "대형", "소형"],
            # 온도 관련
            "temperature": ["따뜻한", "차가운", "얼음", "뜨거운"],
            # 신선도 관련
            "freshness": ["신선한", "새로운", "오래된", "냉동", "냉장"]
        }
        
        # 3. 우선순위 규칙 (높은 우선순위가 핵심 명사일 가능성이 높음)
        self.priority_rules = {
            # 음료 > 맛 (아이스티 > 복숭아)
            "beverage_over_flavor": {
                "head": ["우유", "주스", "커피", "차", "아이스티", "탄산음료", "스무디", "쉐이크"],
                "modifier": ["딸기", "바닐라", "초코", "레몬", "오렌지", "포도", "복숭아", "망고"]
            },
            # 주식 > 재료 (라면 > 치즈)
            "staple_over_ingredient": {
                "head": ["라면", "밥", "국수", "파스타", "피자", "햄버거"],
                "modifier": ["치즈", "고기", "야채", "해산물"]
            },
            # 디저트 > 맛 (아이스크림 > 바닐라)
            "dessert_over_flavor": {
                "head": ["아이스크림", "케이크", "빵", "쿠키", "초콜릿"],
                "modifier": ["바닐라", "초코", "딸기", "커피", "녹차"]
            }
        }
        
        # 4. 한국어 조사 패턴 (조사 앞이 핵심 명사일 가능성이 높음)
        self.korean_particles = ["의", "이", "가", "을", "를", "에", "에서", "로", "으로"]
        
        # 5. 복합어 분리 패턴
        self.compound_patterns = [
            r'([가-힣]+)\s+([가-힣]+)',  # 공백으로 구분된 두 단어
            r'([가-힣]+)([가-힣]+)',     # 붙어있는 두 단어
        ]
    
    def extract_head_noun(self, phrase: str) -> NounPhraseAnalysis:
        """
        복합명사구에서 핵심 명사 추출
        
        Args:
            phrase: 분석할 명사구 (예: "복숭아 아이스티")
            
        Returns:
            NounPhraseAnalysis: 분석 결과
        """
        if not phrase or not phrase.strip():
            return NounPhraseAnalysis(
                original_phrase=phrase,
                head_noun="",
                modifiers=[],
                confidence=0.0,
                reasoning="빈 문자열",
                extraction_method="empty"
            )
        
        phrase = phrase.strip()
        logger.info(f"핵심 명사 추출 시작: '{phrase}'")
        
        # 1. 규칙 기반 분석
        rule_result = self._rule_based_analysis(phrase)
        if rule_result.confidence > 0.8:
            logger.info(f"규칙 기반 분석 성공: {rule_result.head_noun}")
            return rule_result
        
        # 2. base_food_categories 기반 분석
        dict_result = self._dictionary_based_analysis(phrase)
        if dict_result.confidence > 0.7:
            logger.info(f"사전 기반 분석 성공: {dict_result.head_noun}")
            return dict_result
        
        # 3. 패턴 기반 분석
        pattern_result = self._pattern_based_analysis(phrase)
        if pattern_result.confidence > 0.6:
            logger.info(f"패턴 기반 분석 성공: {pattern_result.head_noun}")
            return pattern_result
        
        # 4. 모든 매칭 실패시 fallback: 원본 전체 반환
        logger.info(f"모든 매칭 실패: 원본 전체 반환")
        return NounPhraseAnalysis(
            original_phrase=phrase,
            head_noun=phrase,  # 원본 전체 반환
            modifiers=[],
            confidence=0.3,    # 신뢰도 낮게
            reasoning="모든 매칭 실패, 원본 전체 반환",
            extraction_method="fallback_original"
        )
    
    def _rule_based_analysis(self, phrase: str) -> NounPhraseAnalysis:
        """우선순위 규칙 기반 분석"""
        words = self._split_phrase(phrase)
        if len(words) < 2:
            return NounPhraseAnalysis(
                original_phrase=phrase,
                head_noun=phrase,
                modifiers=[],
                confidence=0.5,
                reasoning="단일 단어",
                extraction_method="single_word"
            )
        
        # 우선순위 규칙 적용
        for rule_name, rule in self.priority_rules.items():
            for word1 in words:
                for word2 in words:
                    if word1 != word2:
                        if (word1 in rule["head"] and word2 in rule["modifier"]):
                            return NounPhraseAnalysis(
                                original_phrase=phrase,
                                head_noun=word1,
                                modifiers=[word2],
                                confidence=0.9,
                                reasoning=f"우선순위 규칙 적용: {rule_name}",
                                extraction_method="priority_rule"
                            )
        
        return NounPhraseAnalysis(
            original_phrase=phrase,
            head_noun="",
            modifiers=[],
            confidence=0.0,
            reasoning="규칙 매칭 없음",
            extraction_method="rule_based"
        )
    
    def _dictionary_based_analysis(self, phrase: str) -> NounPhraseAnalysis:
        """사전 기반 분석"""
        words = self._split_phrase(phrase)
        if len(words) < 2:
            return NounPhraseAnalysis(
                original_phrase=phrase,
                head_noun=phrase,
                modifiers=words,
                confidence=0.6,
                reasoning="단일 단어",
                extraction_method="dictionary_single"
            )
        
        # 각 카테고리별로 매칭 확인
        category_scores = {}
        for category, items in self.base_food_categories.items():
            for word in words:
                if word in items:
                    if category not in category_scores:
                        category_scores[category] = []
                    category_scores[category].append(word)
        
        # 가장 구체적인 카테고리의 단어를 핵심으로 선택
        # (음료 > 과일, 주식 > 재료 등)
        category_priority = ["음료", "주식", "디저트", "반찬", "육류", "해산물", "과일", "채소"]
        
        for priority_category in category_priority:
            if priority_category in category_scores:
                head_noun = category_scores[priority_category][0]
                modifiers = [w for w in words if w != head_noun]
                return NounPhraseAnalysis(
                    original_phrase=phrase,
                    head_noun=head_noun,
                    modifiers=modifiers,
                    confidence=0.8,
                    reasoning=f"사전 기반: {priority_category} 카테고리",
                    extraction_method="dictionary"
                )
        
        return NounPhraseAnalysis(
            original_phrase=phrase,
            head_noun="",
            modifiers=[],
            confidence=0.0,
            reasoning="사전 매칭 없음",
            extraction_method="dictionary"
        )
    
    def _pattern_based_analysis(self, phrase: str) -> NounPhraseAnalysis:
        """패턴 기반 분석"""
        words = self._split_phrase(phrase)
        if len(words) < 2:
            return NounPhraseAnalysis(
                original_phrase=phrase,
                head_noun=phrase,
                modifiers=[],
                confidence=0.5,
                reasoning="단일 단어",
                extraction_method="pattern_single"
            )
        
        # 수식어 패턴 확인
        modifiers = []
        potential_heads = []
        
        for word in words:
            is_modifier = False
            for pattern_type, pattern_words in self.modifier_patterns.items():
                if word in pattern_words:
                    modifiers.append(word)
                    is_modifier = True
                    break
            
            if not is_modifier:
                potential_heads.append(word)
        
        if potential_heads and modifiers:
            # 수식어가 있으면 나머지를 핵심으로 선택
            head_noun = potential_heads[0] if len(potential_heads) == 1 else potential_heads[-1]
            return NounPhraseAnalysis(
                original_phrase=phrase,
                head_noun=head_noun,
                modifiers=modifiers,
                confidence=0.7,
                reasoning="패턴 기반: 수식어 식별",
                extraction_method="pattern"
            )
        
        return NounPhraseAnalysis(
            original_phrase=phrase,
            head_noun="",
            modifiers=[],
            confidence=0.0,
            reasoning="패턴 매칭 없음",
            extraction_method="pattern"
        )
    
    def _fallback_analysis(self, phrase: str) -> NounPhraseAnalysis:
        """기본 추정 분석 (마지막 단어 우선)"""
        words = self._split_phrase(phrase)
        
        if len(words) == 1:
            return NounPhraseAnalysis(
                original_phrase=phrase,
                head_noun=words[0],
                modifiers=[],
                confidence=0.5,
                reasoning="단일 단어",
                extraction_method="fallback_single"
            )
        
        # 마지막 단어를 핵심으로 추정 (한국어 특성상 수식어가 앞에 오는 경우가 많음)
        head_noun = words[-1]
        modifiers = words[:-1]
        
        return NounPhraseAnalysis(
            original_phrase=phrase,
            head_noun=head_noun,
            modifiers=modifiers,
            confidence=0.6,
            reasoning="기본 추정: 마지막 단어 우선",
            extraction_method="fallback"
        )
    
    def _split_phrase(self, phrase: str) -> List[str]:
        """명사구를 단어로 분리"""
        # 사전에 있는 복합어(고유명사)는 분리하지 않고 그대로 반환
        for items in self.base_food_categories.values():
            if phrase in items:
             return [phrase]
        # 공백으로 분리
        if ' ' in phrase:
            return [word.strip() for word in phrase.split() if word.strip()]
        
        # 한글 복합어 분리 시도
        for pattern in self.compound_patterns:
            match = re.match(pattern, phrase)
            if match:
                return [group for group in match.groups() if group]
        
        # 분리할 수 없으면 전체를 하나의 단어로
        return [phrase]
    
    def analyze_multiple_candidates(self, candidates: List[str]) -> List[NounPhraseAnalysis]:
        """여러 후보를 분석하여 우선순위 결정"""
        analyses = []
        for candidate in candidates:
            analysis = self.extract_head_noun(candidate)
            analyses.append(analysis)
        
        # 신뢰도 순으로 정렬
        analyses.sort(key=lambda x: x.confidence, reverse=True)
        return analyses
    
    def get_best_candidate(self, candidates: List[str]) -> Optional[str]:
        """여러 후보 중 가장 적합한 것 선택"""
        analyses = self.analyze_multiple_candidates(candidates)
        
        if not analyses:
            return None
        
        best_analysis = analyses[0]
        if best_analysis.confidence > 0.5:
            return best_analysis.head_noun
        
        return None

# 전역 인스턴스
head_noun_extractor = HeadNounExtractor()

def extract_head_noun(phrase: str) -> NounPhraseAnalysis:
    """편의 함수: 핵심 명사 추출"""
    return head_noun_extractor.extract_head_noun(phrase)

def get_best_candidate(candidates: List[str]) -> Optional[str]:
    """편의 함수: 최적 후보 선택"""
    return head_noun_extractor.get_best_candidate(candidates) 