from opensearchpy import OpenSearch, RequestsHttpConnection
import os
from dotenv import load_dotenv
from openai import OpenAI
import time
import requests

load_dotenv()

def test_opensearch_connection():
    """OpenSearch 연결 테스트 (여러 방법 시도)"""
    
    # 1. AWS 도메인 직접 접근 테스트
    aws_host = 'vpc-refrige-go-pomktvnaxb7w7sxhi74g26ujsq.ap-northeast-2.es.amazonaws.com'
    
    print("1. AWS OpenSearch 도메인 핑 테스트")
    try:
        response = requests.get(f'https://{aws_host}', timeout=10, verify=False)
        print(f"   ✅ HTTP 응답: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 연결 실패: {e}")
    
    # 2. 기본 인증 방식 시도
    print("\n2. 기본 HTTP 인증 시도")
    try:
        client = OpenSearch(
            hosts=[{'host': aws_host, 'port': 443}],
            http_auth=(os.getenv('OPENSEARCH_USER', 'admin'), os.getenv('OPENSEARCH_PASSWORD', 'admin')),
            use_ssl=True,
            verify_certs=False,
            ssl_show_warn=False,
            timeout=30,
            connection_class=RequestsHttpConnection
        )
        
        info = client.info()
        print("   ✅ OpenSearch 연결 성공!")
        print(f"   클러스터 정보: {info['cluster_name']}")
        return client
        
    except Exception as e:
        print(f"   ❌ 기본 인증 실패: {e}")
    
    # 3. 로컬 OpenSearch 시도 (개발용)
    print("\n3. 로컬 OpenSearch 연결 시도")
    try:
        local_client = OpenSearch(
            hosts=[{'host': 'localhost', 'port': 9200}],
            http_auth=('admin', 'admin'),
            use_ssl=False,
            verify_certs=False,
            timeout=10
        )
        
        info = local_client.info()
        print("   ✅ 로컬 OpenSearch 연결 성공!")
        return local_client
        
    except Exception as e:
        print(f"   ❌ 로컬 연결 실패: {e}")
    
    return None

def test_ingredient_search():
    """식재료 검색 테스트"""
    
    # OpenSearch 연결 테스트
    client = test_opensearch_connection()
    
    if client is None:
        print("\n❌ OpenSearch 연결 불가 - 테스트 중단")
        print("\n💡 해결 방법:")
        print("1. AWS OpenSearch 도메인의 액세스 정책에 본인 IP 추가")
        print("2. VPC 설정 확인 (퍼블릭 액세스 허용)")
        print("3. 로컬 OpenSearch 설치 및 실행")
        print("4. AWS IAM 인증 방식 사용")
        return
    
    # OpenAI API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다!")
        return
    
    print(f"\n✅ OpenAI API Key 확인: {api_key[:10]}...{api_key[-4:]}")
    
    # 인덱스 존재 확인
    try:
        indices = client.indices.get_alias()
        print(f"✅ 사용 가능한 인덱스: {list(indices.keys())}")
        
        if 'ingredients' not in indices:
            print("❌ 'ingredients' 인덱스가 존재하지 않습니다!")
            return
            
    except Exception as e:
        print(f"❌ 인덱스 조회 실패: {e}")
        return
    
    # 실제 검색 테스트 진행...
    test_queries = ["시금치"]
    
    for query in test_queries:
        print(f"\n🔍 검색어: {query}")
        
        # 텍스트 검색만 먼저 테스트
        try:
            text_results = client.search(
                index="ingredients",
                body={
                    "query": {
                        "match": {
                            "name": query
                        }
                    },
                    "size": 5
                }
            )
            
            print("📝 텍스트 검색 결과:")
            for hit in text_results["hits"]["hits"]:
                print(f"  - {hit['_source']['name']} (점수: {hit['_score']:.4f})")
                
        except Exception as e:
            print(f"❌ 텍스트 검색 실패: {e}")

if __name__ == "__main__":
    print("🚀 OpenSearch 연결 및 검색 테스트 시작")
    test_ingredient_search()
    print("✅ 테스트 완료")