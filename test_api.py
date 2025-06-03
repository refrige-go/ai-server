"""
AI 서버 API 테스트
주요 API 엔드포인트들의 동작을 확인하는 테스트
"""

import requests
import json

AI_SERVER_URL = "http://localhost:8000"

def test_recipe_recommendation():
    """레시피 추천 API 테스트"""
    print("🎯 레시피 추천 API 테스트...")
    
    try:
        response = requests.post(
            f"{AI_SERVER_URL}/api/recommend/by-ingredients",
            json={
                "ingredients": ["양파", "당근", "소고기"],
                "limit": 3
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            recipes = data.get('recipes', [])
            
            print(f"✅ 추천 API 성공: {len(recipes)}개 레시피")
            for i, recipe in enumerate(recipes[:2], 1):
                print(f"   {i}. {recipe.get('rcp_nm', 'N/A')} (점수: {recipe.get('score', 0):.2f})")
            
            return True
        else:
            print(f"❌ 추천 API 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 추천 API 오류: {e}")
        return False

def test_text_search():
    """텍스트 검색 API 테스트"""
    print("\n🔍 텍스트 검색 API 테스트...")
    
    try:
        # 레시피 검색
        response = requests.get(
            f"{AI_SERVER_URL}/api/integration/recipes/search/text",
            params={"q": "볶음", "limit": 2},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            print(f"✅ 레시피 검색 성공: {len(results)}개 결과")
            for i, recipe in enumerate(results, 1):
                print(f"   {i}. {recipe.get('name', 'N/A')}")
            
            return True
        else:
            print(f"❌ 검색 API 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 검색 API 오류: {e}")
        return False

def test_vector_search():
    """벡터 검색 API 테스트"""
    print("\n🧠 벡터 검색 API 테스트...")
    
    try:
        response = requests.post(
            f"{AI_SERVER_URL}/api/integration/recipes/recommend/vector",
            json={
                "ingredients": ["고기", "야채"],
                "limit": 2
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            print(f"✅ 벡터 검색 성공: {len(results)}개 결과")
            print(f"   처리 시간: {data.get('processing_time', 0):.1f}초")
            for i, recipe in enumerate(results, 1):
                print(f"   {i}. {recipe.get('name', 'N/A')} (점수: {recipe.get('score', 0):.2f})")
            
            return True
        else:
            print(f"❌ 벡터 검색 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 벡터 검색 오류: {e}")
        return False

def test_api_docs():
    """API 문서 접근 테스트"""
    print("\n📚 API 문서 접근 테스트...")
    
    try:
        response = requests.get(f"{AI_SERVER_URL}/docs", timeout=5)
        
        if response.status_code == 200:
            print("✅ API 문서 접근 가능")
            print(f"   URL: {AI_SERVER_URL}/docs")
            return True
        else:
            print(f"❌ API 문서 접근 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API 문서 접근 오류: {e}")
        return False

def main():
    """전체 API 테스트 실행"""
    print("🧪 AI 서버 API 테스트")
    print("=" * 40)
    
    # 각 API 테스트 실행
    tests = [
        test_recipe_recommendation,
        test_text_search,
        test_vector_search,
        test_api_docs
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    # 결과 요약
    print("\n" + "=" * 40)
    print(f"📊 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 API가 정상적으로 작동합니다!")
        print("\n💡 Java 백엔드에서 사용 가능한 주요 API:")
        print(f"   • 레시피 추천: POST {AI_SERVER_URL}/api/recommend/by-ingredients")
        print(f"   • 텍스트 검색: GET {AI_SERVER_URL}/api/integration/recipes/search/text")
        print(f"   • 벡터 검색: POST {AI_SERVER_URL}/api/integration/recipes/recommend/vector")
    else:
        print("⚠️ 일부 API에서 문제가 발견되었습니다.")
        print("💡 환경 설정을 확인해주세요:")
        print("   1. OpenAI API 키가 올바르게 설정되었는지 확인")
        print("   2. OpenSearch(recipe-ai-project)가 실행 중인지 확인")
        print("   3. .env 파일의 설정값들을 확인")

if __name__ == "__main__":
    main()
