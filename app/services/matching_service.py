# app/services/matching_service.py
from app.config.db import find_in_database
import logging

logger = logging.getLogger(__name__)

def match_ingredient(text: str) -> dict:
    logger.debug(f"매칭 시도: {text}")
    
    # 1. DB에서 검색
    db_result = find_in_database(text)
    if db_result:
        logger.debug(f"DB 매칭 성공: {db_result}")
        return {
            "id": db_result.id,
            "name": db_result.name,
            "confidence": db_result.confidence,
            "alternatives": db_result.alternatives
        }
    
    # 2. 유사도 기반 매칭 (필요시 구현)
    logger.debug(f"DB 매칭 실패, 유사도 매칭 시도: {text}")
    return {
        "id": None,
        "name": text,
        "confidence": 0.8,
        "alternatives": []
    }