import re
import asyncio
from typing import Dict, List, Tuple
from app.clients.opensearch_client import opensearch_client

class KoreanSpellChecker:
    def __init__(self):
        # 한글 자모 매핑
        self.cho = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        self.jung = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
        self.jong = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        
        # 키보드 인접 키 매핑 (오타 교정용)
        self.keyboard_adjacent = {
            'ㅂ': ['ㅁ', 'ㅃ', 'ㅍ'],
            'ㅁ': ['ㅂ', 'ㄴ'],
            'ㄴ': ['ㅁ', 'ㅇ'],
            'ㅇ': ['ㄴ', 'ㄹ'],
            'ㄹ': ['ㅇ', 'ㅎ'],
            'ㅎ': ['ㄹ', 'ㅋ'],
            'ㅋ': ['ㅎ', 'ㅌ'],
            'ㅌ': ['ㅋ', 'ㅊ'],
            'ㅊ': ['ㅌ', 'ㅈ'],
            'ㅈ': ['ㅊ', 'ㅅ'],
            'ㅅ': ['ㅈ', 'ㄷ'],
            'ㄷ': ['ㅅ', 'ㄱ'],
            'ㄱ': ['ㄷ', 'ㅂ']
        }
    
    def decompose_hangul(self, char):
        """한글 자모 분해"""
        if not ('가' <= char <= '힣'):
            return char
            
        code = ord(char) - ord('가')
        cho_idx = code // (21 * 28)
        jung_idx = (code % (21 * 28)) // 28
        jong_idx = code % 28
        
        return self.cho[cho_idx] + self.jung[jung_idx] + (self.jong[jong_idx] if jong_idx else '')
    
    def compose_hangul(self, jamo_str):
        """자모를 한글로 조합"""
        if len(jamo_str) < 2:
            return jamo_str
            
        result = ""
        i = 0
        while i < len(jamo_str):
            if i + 1 < len(jamo_str):
                cho = jamo_str[i] if jamo_str[i] in self.cho else 'ㅇ'
                jung = jamo_str[i+1] if jamo_str[i+1] in self.jung else 'ㅡ'
                jong = jamo_str[i+2] if i+2 < len(jamo_str) and jamo_str[i+2] in self.jong[1:] else ''
                
                try:
                    cho_idx = self.cho.index(cho)
                    jung_idx = self.jung.index(jung)
                    jong_idx = self.jong.index(jong) if jong else 0
                    
                    code = ord('가') + (cho_idx * 21 + jung_idx) * 28 + jong_idx
                    result += chr(code)
                    
                    i += 3 if jong else 2
                except ValueError:
                    result += jamo_str[i]
                    i += 1
            else:
                result += jamo_str[i]
                i += 1
                
        return result
    
    async def correct_typo(self, text: str) -> str:
        """오타 교정 메인 함수"""
        original_text = text.strip()
        
        if not original_text:
            return original_text
        
        # 1. 자모 분리된 텍스트 처리 (ㄹㅏ면 → 라면)
        if re.match(r'^[ㄱ-ㅎㅏ-ㅣ\s]+$', original_text):
            composed = self.compose_hangul(original_text.replace(' ', ''))
            if composed != original_text:
                print(f"🔧 자모 조합: '{original_text}' → '{composed}'")
                return await self.find_similar_word_opensearch(composed)
        
        # 2. OpenSearch에서 유사한 단어 검색
        corrected = await self.find_similar_word_opensearch(original_text)
        
        if corrected != original_text:
            print(f"🔧 오타 교정: '{original_text}' → '{corrected}'")
        
        return corrected
    
    async def find_similar_word_opensearch(self, word: str) -> str:
        """OpenSearch에서 유사한 단어 찾기"""
        try:
            # 1. 퍼지 검색 + 정확 매칭 조합
            search_body = {
                "size": 10,
                "query": {
                    "bool": {
                        "should": [
                            # 정확 매칭 (가장 높은 점수)
                            {
                                "match": {
                                    "name": {
                                        "query": word,
                                        "boost": 10
                                    }
                                }
                            },
                            # 퍼지 검색 (오타 허용)
                            {
                                "fuzzy": {
                                    "name": {
                                        "value": word,
                                        "fuzziness": "AUTO",
                                        "boost": 5
                                    }
                                }
                            },
                            # 부분 매칭
                            {
                                "wildcard": {
                                    "name": {
                                        "value": f"*{word}*",
                                        "boost": 3
                                    }
                                }
                            }
                        ]
                    }
                },
                "_source": ["name", "category"]
            }
            
            # 레시피와 재료 모두에서 검색
            recipe_response = await opensearch_client.search(index="recipes", body=search_body)
            ingredient_response = await opensearch_client.search(index="ingredients", body=search_body)
            
            candidates = []
            
            # 레시피명에서 후보 수집
            for hit in recipe_response["hits"]["hits"]:
                name = hit["_source"].get("name", "")
                score = hit["_score"]
                similarity = self.calculate_similarity(word, name)
                
                if similarity > 0.5:  # 유사도 임계값
                    candidates.append((name, score * similarity, "recipe"))
            
            # 재료명에서 후보 수집
            for hit in ingredient_response["hits"]["hits"]:
                name = hit["_source"].get("name", "")
                score = hit["_score"]
                similarity = self.calculate_similarity(word, name)
                
                if similarity > 0.5:
                    candidates.append((name, score * similarity, "ingredient"))
            
            # 점수순 정렬
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            if candidates:
                best_match = candidates[0][0]
                best_score = candidates[0][1]
                
                # 충분히 높은 점수일 때만 교정
                if best_score > 2.0 or self.calculate_similarity(word, best_match) > 0.7:
                    return best_match
            
            return word
            
        except Exception as e:
            print(f"OpenSearch 오타 교정 실패: {e}")
            return word
    
    def calculate_similarity(self, word1: str, word2: str) -> float:
        """Levenshtein distance 기반 유사도 계산"""
        if len(word1) == 0 or len(word2) == 0:
            return 0
            
        # 길이 차이가 너무 크면 유사도 낮음
        if abs(len(word1) - len(word2)) > max(len(word1), len(word2)) // 2:
            return 0
            
        matrix = [[0] * (len(word2) + 1) for _ in range(len(word1) + 1)]
        
        for i in range(len(word1) + 1):
            matrix[i][0] = i
        for j in range(len(word2) + 1):
            matrix[0][j] = j
            
        for i in range(1, len(word1) + 1):
            for j in range(1, len(word2) + 1):
                cost = 0 if word1[i-1] == word2[j-1] else 1
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        distance = matrix[len(word1)][len(word2)]
        max_len = max(len(word1), len(word2))
        return 1 - (distance / max_len)
    
    def get_typo_suggestions(self, word: str) -> List[str]:
        """오타 교정 후보들 반환"""
        suggestions = []
        
        # 자모 분리된 경우
        if re.match(r'^[ㄱ-ㅎㅏ-ㅣ\s]+$', word):
            composed = self.compose_hangul(word.replace(' ', ''))
            if composed != word:
                suggestions.append(composed)
        
        # 키보드 인접 키 오타 교정
        for i, char in enumerate(word):
            if char in self.keyboard_adjacent:
                for adjacent_char in self.keyboard_adjacent[char]:
                    suggestion = word[:i] + adjacent_char + word[i+1:]
                    suggestions.append(suggestion)
        
        return list(set(suggestions))[:5]  # 중복 제거 후 최대 5개

# 싱글톤 인스턴스
spell_checker = KoreanSpellChecker()
