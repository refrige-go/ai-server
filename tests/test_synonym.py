"""
동의어 매칭 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.synonym_matcher import get_synonym_matcher

def test_synonym_matching():
    """동의어 매칭 테스트"""
    print("🔍 동의어 매칭 테스트\n")
    
    matcher = get_synonym_matcher()
    
    test_cases = [
        "밀가루",
        "박력분", 
        "우리밀가루",
        "닭고기",
        "삼겹살",
        "대패삼겹살",
        "시금치",
        "ㅅㅣ금치",  # 오타
        "후추가루",
        "없는재료123"
    ]
    
    for test_input in test_cases:
        print(f"입력: '{test_input}'")
        
        # 표준명 매칭
        standard_match = matcher.find_standard_ingredient(test_input)
        if standard_match:
            category, standard_name, confidence = standard_match
            print(f"  ✅ 표준명: {standard_name} ({category}) - 신뢰도: {confidence:.2f}")
        else:
            print("  ❌ 표준명 매칭 실패")
        
        # 유사 재료
        similar_matches = matcher.find_similar_ingredients(test_input, limit=3)
        if similar_matches:
            print("  🔍 유사 재료:")
            for category, name, confidence in similar_matches:
                print(f"    - {name} ({category}) - {confidence:.2f}")
        
        # 쿼리 확장
        expanded = matcher.expand_ingredient_query(test_input)
        print(f"  📈 확장 쿼리: {expanded[:5]}")  # 상위 5개만 표시
        
        print()

if __name__ == "__main__":
    test_synonym_matching()