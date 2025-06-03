#!/usr/bin/env python3
"""
AI 서버 개발 환경 자동 세팅 스크립트
==================================

이 스크립트는 AI 서버의 로컬 개발 환경을 자동으로 구축합니다.
recipe-ai-project의 OpenSearch와 연결하여 작동합니다.

사용법:
    python setup.py                    # 전체 세팅
    python setup.py --check            # 연결 상태만 확인
    python setup.py --install-deps     # 패키지만 설치
    python setup.py --test-api         # API 테스트만 실행

요구사항:
    - recipe-ai-project의 OpenSearch가 실행 중이어야 함
    - Python 3.8+
    - pip
"""

import os
import sys
import subprocess
import argparse
import time
import requests
from pathlib import Path

def print_banner():
    """프로젝트 배너 출력"""
    print("=" * 60)
    print("🤖 AI Recipe Server - Local Setup")
    print("=" * 60)
    print("🔗 recipe-ai-project OpenSearch와 연결하는 AI 서버를 구축합니다")
    print("🚀 FastAPI 기반 벡터 검색 API 서버를 실행합니다")
    print("-" * 60)

def check_python_version():
    """Python 버전 확인"""
    print("🐍 Python 버전 확인 중...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 이상이 필요합니다")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_recipe_ai_opensearch():
    """recipe-ai-project의 OpenSearch 연결 확인"""
    print("\n🔍 recipe-ai-project OpenSearch 연결 확인 중...")
    
    try:
        response = requests.get('http://localhost:9200', timeout=5)
        if response.status_code == 200:
            info = response.json()
            print(f"✅ OpenSearch 연결 성공!")
            print(f"   클러스터: {info.get('cluster_name', 'N/A')}")
            print(f"   버전: {info.get('version', {}).get('number', 'N/A')}")
            
            # 인덱스 확인
            try:
                indices_response = requests.get('http://localhost:9200/_cat/indices?format=json', timeout=5)
                if indices_response.status_code == 200:
                    indices = indices_response.json()
                    recipe_exists = any(idx['index'] == 'recipes' for idx in indices)
                    ingredient_exists = any(idx['index'] == 'ingredients' for idx in indices)
                    
                    if recipe_exists and ingredient_exists:
                        print("✅ 필요한 인덱스 (recipes, ingredients) 확인됨")
                        return True
                    else:
                        print("⚠️ 인덱스가 없습니다. recipe-ai-project에서 임베딩을 업로드해주세요")
                        print("   실행: cd recipe-ai-project && python setup.py")
                        return False
            except:
                print("⚠️ 인덱스 상태를 확인할 수 없습니다")
                return True
            
        else:
            print(f"❌ OpenSearch 응답 오류: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException:
        print("❌ OpenSearch에 연결할 수 없습니다")
        print("   recipe-ai-project에서 OpenSearch를 먼저 실행해주세요:")
        print("   cd recipe-ai-project && python setup.py")
        return False

def install_dependencies():
    """Python 패키지 설치"""
    print("\n📦 Python 패키지 설치 중...")
    
    try:
        # requirements.txt가 있는지 확인
        if not Path("requirements.txt").exists():
            print("❌ requirements.txt 파일이 없습니다")
            return False
        
        # pip 업그레이드
        print("   pip 업그레이드 중...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True, capture_output=True)
        
        # 패키지 설치
        print("   dependencies 설치 중...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              check=True, capture_output=True, text=True)
        
        print("✅ Python 패키지 설치 완료")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 패키지 설치 실패: {e}")
        print(f"오류 출력: {e.stderr}")
        return False

def setup_environment():
    """환경 설정 파일 생성"""
    print("\n⚙️ 환경 설정 파일 확인 중...")
    
    env_local_path = Path(".env.local")
    
    if env_local_path.exists():
        print("✅ .env.local 파일이 이미 존재합니다")
        return True
    
    # .env.local 템플릿 생성
    env_content = """# AI 서버 로컬 개발 환경 설정
# OpenSearch 설정 (recipe-ai-project 로컬 OpenSearch)
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USERNAME=
OPENSEARCH_PASSWORD=
OPENSEARCH_USE_SSL=false

# OpenAI 설정 (필수)
OPENAI_API_KEY=your_openai_api_key_here

# Google Cloud Vision 설정 (OCR 기능용)
GOOGLE_APPLICATION_CREDENTIALS=./certificates/service-account.json
GOOGLE_CLOUD_PROJECT=your_project_id_here

# 날씨 API 설정 (선택사항)
WEATHER_API_KEY=your_weather_api_key_here

# 서버 설정
HOST=0.0.0.0
PORT=8000
DEBUG=true
ENVIRONMENT=development
"""
    
    try:
        with open(env_local_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ .env.local 파일 생성 완료")
        print("   필요한 API 키들을 .env.local 파일에 설정해주세요")
        return True
    except Exception as e:
        print(f"❌ .env.local 파일 생성 실패: {e}")
        return False

def test_ai_server():
    """AI 서버 연결 테스트"""
    print("\n🧪 AI 서버 연결 테스트...")
    
    # 서버가 실행 중인지 확인
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ AI 서버 연결 성공")
            
            # API 테스트
            print("   API 기능 테스트 중...")
            
            # 텍스트 검색 테스트
            try:
                search_response = requests.get(
                    'http://localhost:8000/api/v1/search/recipes',
                    params={'query': '볶음', 'limit': 3},
                    timeout=10
                )
                if search_response.status_code == 200:
                    results = search_response.json()
                    print(f"   ✅ 레시피 검색 성공: {len(results.get('results', []))}개 결과")
                else:
                    print(f"   ⚠️ 레시피 검색 실패: HTTP {search_response.status_code}")
            except:
                print("   ⚠️ 레시피 검색 테스트 실패")
            
            return True
        else:
            print(f"❌ AI 서버 응답 오류: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException:
        print("❌ AI 서버에 연결할 수 없습니다")
        print("   AI 서버를 먼저 실행해주세요: uvicorn app.main:app --reload")
        return False

def run_ai_server():
    """AI 서버 실행"""
    print("\n🚀 AI 서버 실행 중...")
    print("   서버 주소: http://localhost:8000")
    print("   API 문서: http://localhost:8000/docs")
    print("   중지: Ctrl+C")
    print("-" * 40)
    
    try:
        # uvicorn으로 서버 실행
        os.system("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    except KeyboardInterrupt:
        print("\n서버가 중지되었습니다.")

def check_status():
    """전체 상태 확인"""
    print("🔍 시스템 상태 확인:")
    
    # OpenSearch 확인
    opensearch_ok = check_recipe_ai_opensearch()
    
    # AI 서버 확인
    ai_server_ok = test_ai_server()
    
    print("\n📊 상태 요약:")
    print(f"   OpenSearch: {'✅ 정상' if opensearch_ok else '❌ 연결 실패'}")
    print(f"   AI 서버: {'✅ 정상' if ai_server_ok else '❌ 연결 실패'}")
    
    if opensearch_ok and ai_server_ok:
        print("\n🎉 모든 시스템이 정상 작동 중입니다!")
    else:
        print("\n⚠️ 일부 시스템에 문제가 있습니다. 위의 메시지를 확인해주세요.")

def print_next_steps():
    """다음 단계 안내"""
    print("\n" + "=" * 60)
    print("🎉 AI 서버 설정 완료!")
    print("=" * 60)
    print("\n📋 접속 정보:")
    print("   🖥️ AI 서버: http://localhost:8000")
    print("   📚 API 문서: http://localhost:8000/docs")
    print("   🔍 OpenSearch: http://localhost:9200")
    print("   📊 Dashboard: http://localhost:5601")
    
    print("\n🧪 테스트 명령어:")
    print("   curl http://localhost:8000/health")
    print("   curl 'http://localhost:8000/api/v1/search/recipes?query=볶음&limit=3'")
    
    print("\n🚀 서버 실행:")
    print("   uvicorn app.main:app --reload")
    print("   또는: python setup.py --run")
    
    print("\n🔧 관리 명령어:")
    print("   python setup.py --check       # 상태 확인")
    print("   python setup.py --test-api    # API 테스트")
    
    print("\n📚 다음 단계:")
    print("   1. .env.local에서 OpenAI API 키 설정")
    print("   2. Java 백엔드에서 AI 서버 API 연동")
    print("   3. 프론트엔드에서 검색 기능 구현")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='AI Recipe Server Local Setup')
    parser.add_argument('--check', action='store_true', help='연결 상태만 확인')
    parser.add_argument('--install-deps', action='store_true', help='패키지만 설치')
    parser.add_argument('--test-api', action='store_true', help='API 테스트만 실행')
    parser.add_argument('--run', action='store_true', help='서버 실행')
    
    args = parser.parse_args()
    
    print_banner()
    
    # 상태 확인 모드
    if args.check:
        check_status()
        return
    
    # 패키지 설치 모드
    if args.install_deps:
        if not check_python_version():
            return
        install_dependencies()
        return
    
    # API 테스트 모드
    if args.test_api:
        test_ai_server()
        return
    
    # 서버 실행 모드
    if args.run:
        run_ai_server()
        return
    
    # 일반 세팅 모드
    try:
        # 1. Python 버전 확인
        if not check_python_version():
            return
        
        # 2. OpenSearch 연결 확인
        if not check_recipe_ai_opensearch():
            print("\n💡 해결 방법:")
            print("   1. recipe-ai-project 디렉토리로 이동")
            print("   2. python setup.py 실행하여 OpenSearch 구동")
            print("   3. 다시 이 스크립트 실행")
            return
        
        # 3. 환경 설정
        if not setup_environment():
            return
        
        # 4. 패키지 설치
        if not install_dependencies():
            return
        
        # 5. 완료 정보 출력
        print_next_steps()
        
        # 6. 서버 실행 옵션 제공
        print("\n" + "=" * 60)
        user_input = input("지금 서버를 실행하시겠습니까? (y/N): ").strip().lower()
        if user_input in ['y', 'yes']:
            run_ai_server()
        else:
            print("서버 실행은 나중에 다음 명령어로 할 수 있습니다:")
            print("uvicorn app.main:app --reload")
        
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 중단했습니다")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    main()
