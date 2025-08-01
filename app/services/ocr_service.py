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

    # 🔧 네이버 OCR 방식: 모든 텍스트가 개별 분리됨  
    logger.info(f"📝 === 네이버 OCR 개별 텍스트 ({len(texts)}개) ===")
    logger.info(f"텍스트 목록: {texts}")
    logger.info(f"=== 텍스트 목록 끝 ===")
    
    # 🔧 모든 텍스트를 상품 후보로 직접 사용
    product_section = []
    for text in texts:
        text = text.strip()
        if text and len(text) > 0:
            # 가격이나 바코드 같은 숫자만 있는 텍스트 제외
            if not text.replace(',', '').replace('.', '').isdigit():
                # 한글이나 영문이 포함된 텍스트만 포함
                if re.search(r'[가-힣a-zA-Z]', text):
                    product_section.append(text)

    logger.info(f"🛍️ 추출된 상품 섹션 ({len(product_section)}개): {product_section}")

    # **상품명 패턴 필터링**
    logger.info(f"🔍 상품명 패턴 필터링 시작...")
    filtered_products = []
    excluded_products = []

    for p in product_section:
        cleaned_p = clean_text(p)
        if is_product_name(cleaned_p):
            filtered_products.append(p)
            logger.info(f"  ✅ 포함: '{p}' (정제: '{cleaned_p}')")
        else:
            excluded_products.append(p)
            logger.info(f"  ❌ 제외: '{p}' (정제: '{cleaned_p}')")
    
    logger.info(f"📊 필터링 결과: {len(filtered_products)}개 포함, {len(excluded_products)}개 제외")
    logger.info(f"포함된 상품들: {filtered_products}")
    logger.info(f"제외된 상품들: {excluded_products}")
    
    # 🎯 모든 상품 통합 처리 (포함+제외)
    all_products = filtered_products + excluded_products
    ingredients = []
    logger.info(f"🎯 전체 식재료 매칭 시작: {len(all_products)}개")
    
    for i, product in enumerate(all_products, 1):
        logger.info(f"--- [{i}/{len(all_products)}] 처리 중 ---")
        logger.info(f"원본 상품명: '{product}'")
        
        # 포함된 항목은 기존 정제 로직 적용
        if product in filtered_products:
            cleaned = clean_text(product)
            logger.info(f"정제된 텍스트: '{cleaned}'")
            
            if cleaned:
                head_noun_result = extract_head_noun(cleaned)
                core_ingredient = head_noun_result.head_noun
                logger.info(f"핵심 명사: '{core_ingredient}' (신뢰도: {head_noun_result.confidence})")
                
                # AI 우선 매칭 시도
                matched = await match_ingredient(core_ingredient)
            else:
                matched = None
        else:
            # 제외된 항목은 원본 그대로 AI 처리
            logger.info(f"제외된 항목 → AI 우선 처리")
            matched = await match_ingredient(product)
            core_ingredient = product
            
        if matched:
            # AI 추론 여부 확인하여 로그 출력
            if matched.get("ai_inferred", False):
                logger.info(f"🤖✅ AI 추론 매칭: '{matched.get('original_ocr', product)}' → '{matched['name']}'")
            else:
                logger.info(f"📖✅ 일반 매칭: '{product}' → '{matched['name']}'")
                
            ingredients.append(RecognizedIngredient(
                original_text=product,
                ingredient_id=matched.get("id"),
                matched_name=matched.get("name"),
                confidence=matched.get("confidence", 0.0),
                alternatives=matched.get("alternatives", []),
                extracted_head_noun=matched.get("original_ocr", core_ingredient) if matched.get("ai_inferred") else core_ingredient,
                extraction_confidence=0.7 if matched.get("ai_inferred") else (head_noun_result.confidence if product in filtered_products else 0.3),
                ai_inferred=matched.get("ai_inferred", False),
                original_ocr_text=matched.get("original_ocr", product)
            ))
        else:
            logger.info(f"❌ 매칭 실패: '{product}'")

    # 4. 결과 포맷팅
    avg_conf = sum(ing.confidence for ing in ingredients) / len(ingredients) if ingredients else 0.0
    processing_time = time.time() - start_time

    logger.info(f"🎉 === OCR 처리 완료 ===")
    logger.info(f"전체 인식 텍스트: {len(product_section)}개")
    logger.info(f"상품명 필터링 후: {len(filtered_products)}개")
    logger.info(f"최종 매칭 성공: {len(ingredients)}개")
    logger.info(f"평균 신뢰도: {avg_conf:.3f}")
    logger.info(f"처리 시간: {processing_time:.2f}초")
    logger.info(f"최종 결과: {[ing.matched_name for ing in ingredients]}")

    return OCRResponse(
        ingredients=ingredients,
        confidence=avg_conf,
        processing_time=processing_time
    )