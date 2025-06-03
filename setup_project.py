"""
AI 서버 초기 설정 도우미
팀원들이 프로젝트를 처음 clone한 후 실행하는 설정 스크립트
"""

import os
import subprocess
import sys

def check_python_version():
    """Python 버전 확인"""
    print("🐍 Python 버전 확인 중...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        print(f"   현재 버전: {sys.version}")
        return False
    else:
        print(f"✅ Python {sys.version.split()[0]} 확인됨")
        return True

def check_env_file():
    """환경변수 파일 확인"""
    print("\n📋 환경변수 파일 확인 중...")
    
    if os.path.exists('.env'):
        print("✅ .env 파일이 존재합니다.")
        return True
    elif os.path.exists('.env.example'):
        print("⚠️ .env 파일이 없습니다.")
        print("💡 .env.example을 복사하여 .env 파일을 만들어주세요:")
        print("   Windows: copy .env.example .env")
        print("   Linux/Mac: cp .env.example .env")
        print("   그 후 .env 파일에서 API 키들을 설정해주세요.")
        return False
    else:
        print("❌ .env.example 파일도 없습니다.")
        return False

def install_dependencies():
    """의존성 설치"""
    print("\n📦 의존성 패키지 설치 중...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 패키지 설치 완료")
            return True
        else:
            print("❌ 패키지 설치 실패")
            print(f"   오류: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 패키지 설치 중 오류: {e}")
        return False

def check_opensearch_connection():
    """OpenSearch 연결 확인"""
    print("\n🔍 OpenSearch 연결 확인 중...")
    
    try:
        import requests
        response = requests.get("http://localhost:9201", timeout=5)
        
        if response.status_code == 200:
            print("✅ OpenSearch(포트 9201)에 연결 성공")
            return True
        else:
            print("⚠️ OpenSearch 연결 실패")
            print("💡 recipe-ai-project OpenSearch를 실행해주세요:")
            print("   cd ../recipe-ai-project")
            print("   docker-compose up -d")
            return False
            
    except Exception:
        print("⚠️ OpenSearch에 연결할 수 없습니다.")
        print("💡 recipe-ai-project OpenSearch를 실행해주세요:")
        print("   cd ../recipe-ai-project")
        print("   docker-compose up -d")
        return False

def main():
    """전체 설정 프로세스 실행"""
    print("🚀 AI 서버 초기 설정 시작")
    print("=" * 50)
    
    # 1. Python 버전 확인
    if not check_python_version():
        sys.exit(1)
    
    # 2. 환경변수 파일 확인
    env_ok = check_env_file()
    
    # 3. 의존성 설치
    deps_ok = install_dependencies()
    
    if not deps_ok:
        print("\n❌ 의존성 설치에 실패했습니다.")
        sys.exit(1)
    
    # 4. OpenSearch 연결 확인
    opensearch_ok = check_opensearch_connection()
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📋 설정 결과:")
    print(f"   ✅ Python 버전: 통과")
    print(f"   {'✅' if env_ok else '⚠️'} 환경변수 파일: {'완료' if env_ok else '설정 필요'}")
    print(f"   ✅ 패키지 설치: 완료")
    print(f"   {'✅' if opensearch_ok else '⚠️'} OpenSearch 연결: {'성공' if opensearch_ok else '확인 필요'}")
    
    if env_ok and opensearch_ok:
        print("\n🎉 설정 완료! 다음 단계:")
        print("   1. AI 서버 실행: uvicorn app.main:app --reload --port 8000")
        print("   2. 연결 테스트: python test_connection.py")
        print("   3. API 테스트: python test_api.py")
    else:
        print("\n⚠️ 추가 설정이 필요합니다:")
        if not env_ok:
            print("   • .env 파일 생성 및 API 키 설정")
        if not opensearch_ok:
            print("   • recipe-ai-project OpenSearch 실행")
        
        print("\n설정 완료 후 다시 실행해주세요.")

if __name__ == "__main__":
    main()
