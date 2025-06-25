"""
OCR 서비스 로직

이 파일은 OCR 처리의 핵심 비즈니스 로직을 구현합니다.
주요 기능:
1. 이미지 전처리
2. Google Vision API 호출
3. 텍스트 정제 및 식재료 매칭
4. 결과 포맷팅

구현 시 고려사항:
- 이미지 전처리 최적화
- OCR 결과 정확도 향상
- 에러 처리 및 재시도 로직
- 성능 최적화
- 로깅 및 모니터링
"""

from fastapi import UploadFile
from app.models.schemas import OCRResponse, RecognizedIngredient
from app.clients.google_vision_client import GoogleVisionClient
from app.utils.ocr_image_preprocessor import preprocess_image
from app.services.matching_service import match_ingredient
from app.utils.ocr_text_processor import clean_text, extract_product_section, is_product_name
from app.utils.ocr_head_noun_extractor import extract_head_noun
from app.services.matching_service import match_ingredient
from app.clients.opensearch_client import OpenSearchClient

import time

import re
import logging

logger = logging.getLogger(__name__)

async def analyze_receipt_image(image: UploadFile) -> OCRResponse:
    start_time = time.time()
    image_bytes = await image.read()
    logger.info(f"이미지 바이트 수: {len(image_bytes)}")

    # 1. 이미지 전처리
    processed_image = preprocess_image(image_bytes)
    logger.info("이미지 전처리 완료")

    # 2. Google Vision API 호출
    vision_client = GoogleVisionClient()
    texts = await vision_client.extract_text(processed_image)
    logger.info(f"OCR 결과: {texts}")

    if not texts:
        logger.warning("OCR 결과 없음")
        return OCRResponse(ingredients=[], confidence=0.0, processing_time=time.time() - start_time)

    # 3. 텍스트 정제 및 식재료 매칭
    full_text = texts[0]
    logger.info(f"OCR 전체 텍스트: {full_text}")

    product_section = extract_product_section(full_text)
    logger.info(f"추출된 상품 섹션: {product_section}")

    # **상품명 패턴 필터링**
    filtered_products = [p for p in product_section if is_product_name(clean_text(p))]
    logger.info(f"상품명 패턴 필터링 결과: {filtered_products}")
    
    # 상품명에서 식재료 추출
    ingredients = []
    for product in filtered_products:
        logger.info(f"처리 중인 상품: {product}")
        cleaned = clean_text(product)
        logger.info(f"정제된 텍스트: {cleaned}")
    
        if cleaned:
            # 핵심 명사 추출 추가
            head_noun_result = extract_head_noun(cleaned)
            core_ingredient = head_noun_result.head_noun
            
            # 핵심 명사로 매칭 시도
            matched = await match_ingredient(core_ingredient)  # 핵심 명사로 매칭, matching_service 호출
            logger.info(f"매칭 결과: {matched}")

            if matched:
                ingredients.append(RecognizedIngredient(
                    original_text=product,
                    ingredient_id=matched.get("id"),
                    matched_name=matched.get("name"),
                    confidence=matched.get("confidence", 0.0),
                    alternatives=matched.get("alternatives", []),
                    # 새로운 필드 추가
                    extracted_head_noun=core_ingredient,
                    extraction_confidence=head_noun_result.confidence
                ))
    # 4. 결과 포맷팅
    avg_conf = sum(ing.confidence for ing in ingredients) / len(ingredients) if ingredients else 0.0
    processing_time = time.time() - start_time

    logger.info(f"최종 결과: {ingredients}")
    return OCRResponse(
        ingredients=ingredients,
        confidence=avg_conf,
        processing_time=processing_time
    )