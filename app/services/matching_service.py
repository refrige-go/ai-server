from app.clients.opensearch_client import opensearch_client
import logging
import json
import os

logger = logging.getLogger(__name__)

SYNONYM_PATH = os.path.join(os.path.dirname(__file__), "../../data/synonym_dictionary.json")
with open(SYNONYM_PATH, "r", encoding="utf-8") as f:
    synonym_dict = json.load(f)

# 동의어 사전 역방향 매핑 생성
synonym_lookup = {}
for category, items in synonym_dict.items():
    for standard_name, synonyms in items.items():
        for synonym in synonyms:
            synonym_lookup[synonym.replace(" ", "")] = {
                "standard_name": standard_name,
                "category": category
            }

def match_with_synonym_dict(text: str) -> dict:
    key = text.strip().replace(" ", "")
    entry = synonym_lookup.get(key)
    if entry:
        return {
            "id": None,  # 필요시 표준명에 id를 추가해서 넣을 수 있음
            "name": entry["standard_name"],
            "confidence": 1.0,
            "alternatives": []  # 필요시 동의어 리스트도 넣을 수 있음
        }
    return None

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
            "id": source.get("ingredient_id"),
            "name": source.get("name"),
            "confidence": hits[0]["_score"] / 10,  # 점수 정규화는 필요에 따라 조정
            "alternatives": []
        }
    return None

async def match_ingredient(text: str) -> dict:
    logger.debug(f"매칭 시도: {text}")

     # 1차: 동의어 사전 매칭
    synonym_result = match_with_synonym_dict(text)
    if synonym_result:
        logger.debug(f"동의어 사전 매칭 성공: {synonym_result}")
        
        # 동의어 매칭 후 표준명으로 OpenSearch 검색하여 ingredient_id 찾기
        standard_name = synonym_result["name"]
        os_result = await search_ingredient_in_opensearch(standard_name)
        if os_result:
            logger.debug(f"표준명으로 ingredient_id 찾기 성공: {os_result}")
            return {
                "id": os_result["id"],
                "name": synonym_result["name"],
                "confidence": synonym_result["confidence"],
                "alternatives": synonym_result["alternatives"]
            }
        
        # OpenSearch에서 찾지 못하면 동의어 결과 그대로 반환
        return synonym_result

    # 2차: 오픈서치 매칭
    os_result = await search_ingredient_in_opensearch(text)
    if os_result:
        logger.debug(f"오픈서치 매칭 성공: {os_result}")
        return os_result

    # 3차: fallback
    logger.debug(f"모든 매칭 실패, 유사도 매칭 시도: {text}")
    return {
        "id": None,
        "name": text,
        "confidence": 0.3,
        "alternatives": []
    }