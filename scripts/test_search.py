from opensearchpy import OpenSearch
import os
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일에서 환경변수 로드
load_dotenv()

# OpenSearch 클라이언트 설정
client = OpenSearch(
    hosts=[{'host': os.getenv('OPENSEARCH_HOST', 'localhost'), 'port': 9200}],
    http_auth=(os.getenv('OPENSEARCH_USER', 'admin'), os.getenv('OPENSEARCH_PASSWORD', 'admin')),
    use_ssl=True,
    verify_certs=False,
    ssl_show_warn=False
)

# OpenAI 클라이언트 설정
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str) -> list:
    """OpenAI API를 사용하여 텍스트의 임베딩 벡터 생성"""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def test_ingredient_search():
    """식재료 검색 테스트"""
    test_queries = [
        "시금치",           # 정상 검색어
        "ㅅ ㅣ 금치",       # 띄어쓰기 오류
        "시금찌",          # 오타
        "spinach",         # 영문
        "채소 시금치",      # 추가 설명
    ]
    
    for query in test_queries:
        print(f"\n검색어: {query}")
        
        # 1. 텍스트 검색 (Nori 분석기 사용)
        text_results = client.search(
            index="ingredients",
            body={
                "query": {
                    "match": {
                        "name": {
                            "query": query,
                            "analyzer": "korean"
                        }
                    }
                }
            }
        )
        
        print("텍스트 검색 결과:")
        for hit in text_results["hits"]["hits"]:
            print(f"- {hit['_source']['name']} (점수: {hit['_score']})")
        
        # 2. 벡터 검색 (의미 기반)
        # 검색어의 임베딩 벡터 생성
        query_vector = get_embedding(query)
        
        vector_results = client.search(
            index="ingredients",
            body={
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                            "params": {"query_vector": query_vector}
                        }
                    }
                }
            }
        )
        
        print("벡터 검색 결과:")
        for hit in vector_results["hits"]["hits"]:
            print(f"- {hit['_source']['name']} (점수: {hit['_score']})")

if __name__ == "__main__":
    test_ingredient_search() 