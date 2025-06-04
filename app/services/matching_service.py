# app/services/matching_service.py
from app.clients.opensearch_client import opensearch_client
import logging

logger = logging.getLogger(__name__)

async def search_ingredient_in_opensearch(query: str) -> dict:
    index = "ingredients"  # 실제 인덱스명에 맞게 수정
    body = {
        "query": {
            "match": {
                "name": query
            }
        }
    }
    response = await opensearch_client.search(index=index, body=body)
    hits = response.get("hits", {}).get("hits", [])
    if hits:
        source = hits[0]["_source"]
        return {
            "id": source.get("id"),
            "name": source.get("name"),
            "confidence": hits[0]["_score"] / 10,  # 점수 정규화는 필요에 따라 조정
            "alternatives": []
        }
    return None

def match_ingredient(text: str) -> dict:
    logger.debug(f"매칭 시도: {text}")
    
    # 1. 오픈서치에서 검색
    os_result = search_ingredient_in_opensearch(text)
    if os_result:
        logger.debug(f"오픈서치 매칭 성공: {os_result}")
        return os_result
    
    # 2. 유사도 기반 매칭 (필요시 구현)
    logger.debug(f"오픈서치 매칭 실패, 유사도 매칭 시도: {text}")
    return {
        "id": None,
        "name": text,
        "confidence": 0.8,
        "alternatives": []
    }