"""
AI 서버 연결 테스트 스크립트
"""

import asyncio
import os
from dotenv import load_dotenv
from app.clients.opensearch_client import OpenSearchClient
from app.clients.openai_client import OpenAIClient

load_dotenv()

async def test_opensearch_connection():
    """OpenSearch 연결 테스트"""
    print("🔍 OpenSearch 연결 테스트...")
    
    try:
        client = OpenSearchClient()
        
        # 인덱스 존재 확인
        recipes_exists = client.client.indices.exists(index="recipes")
        ingredients_exists = client.client.indices.exists(index="ingredients")
        
        print(f"   - recipes 인덱스: {'✅ 존재' if recipes_exists else '❌ 없음'}")
        print(f"   - ingredients 인덱스: {'✅ 존재' if ingredients_exists else '❌ 없음'}")
        
        if recipes_exists:
            count = client.client.count(index="recipes")["count"]
            print(f"   - recipes 문서 수: {count}개")
            
        if ingredients_exists:
            count = client.client.count(index="ingredients")["count"]
            print(f"   - ingredients 문서 수: {count}개")
            
        client.close()
        return True
        
    except Exception as e:
        print(f"   ❌ OpenSearch 연결 실패: {e}")
        return False

async def test_openai_connection():
    """OpenAI 연결 테스트"""
    print("🤖 OpenAI 연결 테스트...")
    
    try:
        client = OpenAIClient()
        embedding = await client.get_embedding("테스트")
        
        print(f"   ✅ OpenAI 연결 성공")
        print(f"   - 임베딩 차원: {len(embedding)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ OpenAI 연결 실패: {e}")
        return False

async def test_vector_search():
    """벡터 검색 테스트"""
    print("🔍 벡터 검색 테스트...")
    
    try:
        opensearch_client = OpenSearchClient()
        openai_client = OpenAIClient()
        
        # 테스트 쿼리
        test_query = "닭고기 요리"
        query_vector = await openai_client.get_embedding(test_query)
        
        # 레시피 검색
        results = await opensearch_client.vector_search(
            index="recipes",
            vector=query_vector,
            limit=3
        )
        
        print(f"   ✅ 벡터 검색 성공: {len(results)}개 결과")
        for i, result in enumerate(results, 1):
            source = result["_source"]
            print(f"   {i}. {source.get('name', 'Unknown')} (점수: {result['_score']:.3f})")
        
        opensearch_client.close()
        return True
        
    except Exception as e:
        print(f"   ❌ 벡터 검색 실패: {e}")
        return False

async def main():
    """전체 테스트 실행"""
    print("🚀 AI 서버 연결 테스트 시작\n")
    
    opensearch_ok = await test_opensearch_connection()
    print()
    
    openai_ok = await test_openai_connection()
    print()
    
    if opensearch_ok and openai_ok:
        await test_vector_search()
        print()
    
    if opensearch_ok and openai_ok:
        print("🎉 모든 연결 테스트 성공!")
    else:
        print("❌ 일부 연결 테스트 실패")

if __name__ == "__main__":
    asyncio.run(main())