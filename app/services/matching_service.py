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
async def search_ingredient_in_opensearch(query: str) -> dict:
    index = "ingredients"
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
        score = hits[0]["_score"]
        
        # 점수 임계값 추가
        if score < 3.0:
            logger.debug(f"OpenSearch 점수 너무 낮음: {score:.2f} < 3.0, 매칭 실패")
            return None
            
        source = hits[0]["_source"]
        logger.debug(f"OpenSearch 점수: {score:.2f}")
        return {
            "id": source.get("ingredient_id"),
            "name": source.get("name"),
            "confidence": min(score / 10, 1.0),
            "alternatives": []
        }
    return None

async def match_ingredient(text: str) -> dict:
    logger.debug(f"매칭 시도: {text}")

     # 📖 1차: 동의어 사전 매칭
    logger.debug(f"동의어 사전 매칭 시도: {text}")
    synonym_result = match_with_synonym_dict(text)
    if synonym_result:
        logger.info(f"📖✅ 동의어 사전 매칭: '{text}' → '{synonym_result['name']}'")
        return synonym_result

    # 🔍 2차: OpenSearch 매칭
    logger.debug(f"OpenSearch 매칭 시도: {text}")
    os_result = await search_ingredient_in_opensearch(text)
    if os_result and os_result.get('confidence', 0) >= 0.5:  # 신뢰도 임계값 추가
        logger.info(f"🔍✅ OpenSearch 매칭: '{text}' → '{os_result['name']}'")
        return os_result

    # 🤖 3차: AI 기반 텍스트 정제/추론
    logger.info(f"🤖 AI 추론 시도: {text}")
    try:
        from app.clients.openai_client import openai_client
        inferred_ingredient = await openai_client.infer_ingredient_from_ocr(text)
        
        # AI가 명시적으로 비식재료로 판단한 경우
        if inferred_ingredient is None:
            logger.info(f"🚫 AI가 비식재료로 판단 → 매칭 중단: '{text}'")
            return None
        
        # AI가 새로운 식재료를 추론한 경우
        if inferred_ingredient and inferred_ingredient != text:
            logger.info(f"🤖 AI 추론 성공: '{text}' → '{inferred_ingredient}'")
            
            # AI 추론 결과로 다시 동의어 매칭 시도
            ai_synonym_result = match_with_synonym_dict(inferred_ingredient)
            if ai_synonym_result:
                logger.info(f"🤖✅ AI 추론 후 동의어 매칭: '{text}' → '{inferred_ingredient}' → '{ai_synonym_result['name']}'")
                ai_synonym_result["ai_inferred"] = True
                ai_synonym_result["original_text"] = text
                return ai_synonym_result
            
            # AI 추론 결과로 다시 OpenSearch 매칭 시도
            ai_os_result = await search_ingredient_in_opensearch(inferred_ingredient)
            if ai_os_result and ai_os_result.get('confidence', 0) >= 0.5:
                logger.info(f"🤖✅ AI 추론 후 OpenSearch 매칭: '{text}' → '{inferred_ingredient}' → '{ai_os_result['name']}'")
                ai_os_result["ai_inferred"] = True
                ai_os_result["original_text"] = text
                return ai_os_result

        # AI가 식재료로 판단했다면 그대로 반환    
        if inferred_ingredient:
            logger.info(f"🤖✅ AI 식재료 판단: '{text}' → 새로운 식재료로 추가")
            return {
                "id": None,
                "name": inferred_ingredient,
                "confidence": 0.8,
                "ai_inferred": True,
                "original_text": text,
                "is_new_ingredient": True,  # 새로운 식재료 표시
                "alternatives": []
            }
                
    except Exception as e:
        logger.error(f"🤖🚨 AI 추론 중 오류: {e}")

    logger.debug(f"모든 매칭 실패: {text}")
    return None