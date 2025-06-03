#!/usr/bin/env python3
"""
OpenSearch 및 OpenAI 연결 테스트 스크립트
"""

import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.clients.opensearch_client import opensearch_client
from app.clients.openai_client import openai_client

async def test_connections():
    """모든 외부 서비스 연결 테스트"""
    print("🔧 AI 서버 연결 테스트")
    print("=" * 50)
    
    # 1. OpenSearch 연결 테스트
    print("1. OpenSearch 연결 테스트...")
    try:
        connection_ok = await opensearch_client.test_connection()
        if connection_ok:
            print("   ✅ OpenSearch 연결 성공")
            
            # 통계 확인
            stats = await opensearch_client.get_stats()
            print(f"   📊 레시피: {stats['recipes_count']}개")
            print(f"   📊 재료: {stats['ingredients_count']}개")
        else:
            print("   ❌ OpenSearch 연결 실패")
            print("   💡 recipe-ai-project의 OpenSearch가 실행 중인지 확인하세요")
            return False
    except Exception as e:
        print(f"   ❌ OpenSearch 오류: {e}")
        return False
    
    # 2. OpenAI 연결 테스트
    print("\n2. OpenAI API 테스트...")
    try:
        test_embedding = await openai_client.get_embedding("테스트")
        print(f"   ✅ OpenAI API 연결 성공 ({len(test_embedding)}차원)")
    except Exception as e:
        print(f"   ❌ OpenAI API 오류: {e}")
        print("   💡 .env 파일의 OPENAI_API_KEY를 확인하세요")
        return False
    
    print("\n🎉 모든 연결 테스트 통과!")
    print("\n🚀 서버를 시작할 수 있습니다:")
    print("   uvicorn app.main:app --reload")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_connections())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n테스트가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n예상치 못한 오류: {e}")
        sys.exit(1)