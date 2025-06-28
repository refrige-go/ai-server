"""
OCR API 엔드포인트

이 파일은 영수증 이미지를 처리하는 API 엔드포인트를 정의합니다.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import OCRResponse
from app.services.ocr_service import analyze_receipt_image

router = APIRouter()

@router.post("/process", response_model=OCRResponse)
async def process_ocr_image(image: UploadFile = File(...)):
    """
    영수증 이미지를 처리하여 식재료를 인식합니다.
    """
    if not image:
        raise HTTPException(status_code=400, detail="이미지 파일이 필요합니다.")
    return await analyze_receipt_image(image)