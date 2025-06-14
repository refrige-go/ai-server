"""
OCR API 엔드포인트

이 파일은 영수증 이미지를 처리하는 API 엔드포인트를 정의합니다.
주요 기능:
1. 이미지 파일 업로드 처리
2. OCR 서비스 호출
3. 결과 반환

구현 시 고려사항:
- 이미지 파일 유효성 검사
- 에러 처리 및 로깅
- 응답 형식 준수 (OCRResponse)
- 비동기 처리
"""

from fastapi import APIRouter, UploadFile, File
from app.models.schemas import OCRResponse
from app.services.ocr_service import analyze_receipt_image

router = APIRouter()

@router.post("/process", response_model=OCRResponse)
async def process_ocr_image(image: UploadFile = File(...)):
    """
    영수증 이미지를 처리하여 식재료를 인식합니다.
    
    Args:
        image: 업로드된 영수증 이미지 파일
        
    Returns:
        OCRResponse: 인식된 식재료 목록과 신뢰도
    """
    return await analyze_receipt_image(image) 