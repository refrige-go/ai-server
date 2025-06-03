"""
AI 서버 연결 테스트
팀원들이 AI 서버 설정 후 반드시 실행해야 할 테스트
"""

import requests
import sys

def test_server_health():
    """AI 서버 기본 연결 테스트"""
    print("🔗 AI 서버 연결 테스트 중...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ AI 서버 연결 성공!")
            print(f"   📊 레시피 데이터: {data.get('opensearch', {}).get('recipes_count', 0)}개")
            print(f"   📊 재료 데이터: {data.get('opensearch', {}).get('ingredients_count', 0)}개")
            print(f"   🔌 OpenSearch 연결: {'✅' if data.get('opensearch', {}).get('connected') else '❌'}")
            return True
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ AI 서버에 연결할 수 없습니다.")
        print("💡 해결 방법:")
        print("   1. AI 서버가 실행 중인지 확인: uvicorn app.main:app --reload --port 8000")
        print("   2. 가상환경이 활성화되어 있는지 확인")
        return False
    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        return False

def test_basic_api():
    """기본 API 동작 테스트"""
    print("\n🧪 기본 API 테스트 중...")
    
    try:
        # 간단한 추천 테스트
        response = requests.post(
            "http://localhost:8000/api/recommend/by-ingredients",
            json={"ingredients": ["양파"], "limit": 1},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            recipes = data.get('recipes', [])
            
            if recipes:
                recipe = recipes[0]
                print("✅ AI 추천 API 정상 작동!")
                print(f"   📝 추천 레시피: {recipe.get('rcp_nm', 'N/A')}")
                print(f"   🎯 매칭 점수: {recipe.get('score', 0):.2f}")
                return True
            else:
                print("⚠️ API는 작동하지만 추천 결과가 없습니다.")
                print("💡 OpenSearch 데이터를 확인해주세요.")
                return False
        else:
            print(f"❌ API 응답 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API 테스트 실패: {e}")
        return False

def main():
    """전체 테스트 실행"""
    print("🚀 AI 서버 필수 테스트 시작")
    print("=" * 50)
    
    # 기본 연결 테스트
    health_ok = test_server_health()
    
    if not health_ok:
        print("\n❌ 기본 연결에 실패했습니다. API 테스트를 건너뜁니다.")
        sys.exit(1)
    
    # API 테스트
    api_ok = test_basic_api()
    
    # 결과 요약
    print("\n" + "=" * 50)
    if health_ok and api_ok:
        print("🎉 모든 테스트 통과! AI 서버가 정상적으로 작동합니다.")
        print("\n📋 다음 단계:")
        print("   1. Java 백엔드에서 AI 서버 API 호출 구현")
        print("   2. 프론트엔드와 연동 테스트")
        print("   3. API 문서 확인: http://localhost:8000/docs")
    else:
        print("⚠️ 일부 테스트에서 문제가 발견되었습니다.")
        print("💡 문제 해결 후 다시 테스트해주세요.")
        sys.exit(1)

if __name__ == "__main__":
    main()
