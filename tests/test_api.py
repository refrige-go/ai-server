"""
AI 서버 API 테스트 스크립트
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_check():
    """헬스 체크 테스트"""
    print("🏥 헬스 체크 테스트...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("   ✅ 서버 정상 실행 중")
            return True
        else:
            print(f"   ❌ 서버 응답 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 연결 실패: {e}")
        return False

def test_search_api():
    """검색 API 테스트"""
    print("🔍 검색 API 테스트...")
    
    try:
        payload = {
            "query": "닭고기 요리",
            "search_type": "recipe",
            "limit": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/search/semantic",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 검색 성공: {data['total_matches']}개 결과")
            
            for recipe in data['recipes'][:3]:
                print(f"   - {recipe['rcp_nm']} (점수: {recipe['score']:.3f})")
            
            return True
        else:
            print(f"   ❌ 검색 실패: {response.status_code}")
            print(f"   오류: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 검색 API 오류: {e}")
        return False

def test_recommendation_api():
    """추천 API 테스트"""
    print("🍳 추천 API 테스트...")
    
    try:
        payload = {
            "ingredients": ["닭고기", "감자", "양파"],
            "limit": 5,
            "user_id": "test_user"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/recipes/recommend",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 추천 성공: {data['total_matches']}개 결과")
            
            for recipe in data['recipes'][:3]:
                print(f"   - {recipe['rcp_nm']} (점수: {recipe['score']:.3f})")
                print(f"     이유: {recipe['match_reason']}")
            
            return True
        else:
            print(f"   ❌ 추천 실패: {response.status_code}")
            print(f"   오류: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 추천 API 오류: {e}")
        return False

def main():
    """전체 API 테스트 실행"""
    print("🚀 AI 서버 API 테스트 시작\n")
    
    # 1. 헬스 체크
    health_ok = test_health_check()
    print()
    
    if not health_ok:
        print("❌ 서버가 실행되지 않고 있습니다. 먼저 서버를 시작하세요:")
        print("uvicorn app.main:app --reload")
        return
    
    # 2. 검색 API 테스트
    search_ok = test_search_api()
    print()
    
    # 3. 추천 API 테스트
    recommend_ok = test_recommendation_api()
    print()
    
    # 결과 요약
    if search_ok and recommend_ok:
        print("🎉 모든 API 테스트 성공!")
    else:
        print("❌ 일부 API 테스트 실패")
        if not search_ok:
            print("   - 검색 API 확인 필요")
        if not recommend_ok:
            print("   - 추천 API 확인 필요")

if __name__ == "__main__":
    main()