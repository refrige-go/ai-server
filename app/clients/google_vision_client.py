
"""
Google Vision API 클라이언트 (APIGW 사용)
"""

import time
import httpx
import base64
import logging
from typing import List
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class GoogleVisionClient:
    def __init__(self):
        logger.info("🔧 Google Vision Client 초기화 시작")
        self.settings = get_settings()
        self.api_key = self.settings.ocr_api_key
        self.apigw_url = self.settings.ocr_apigw_url
        
        logger.info(f"🔍 OCR API Key 길이: {len(self.api_key)}")
        logger.info(f"🔍 OCR APIGW URL: {self.apigw_url[:50]}..." if self.apigw_url else "🔍 OCR APIGW URL: 없음")
        
        # 🔧 네이버 OCR만 사용 (강제 설정)
        self.use_apigw = True
        
        if self.use_apigw:
            logger.info(f"🔧 네이버 OCR APIGW 사용 결정")
        else:
            logger.error(f"❌ APIGW 설정이 없어서 OCR을 사용할 수 없습니다")
    
    async def extract_text(self, image_data: bytes) -> List[str]:
        """
        이미지에서 텍스트를 추출합니다.
        """
        logger.info(f"🔍 extract_text 호출됨 - 이미지 크기: {len(image_data)} bytes")
        logger.info(f"🔍 APIGW 사용 여부: {self.use_apigw}")
        
        if self.use_apigw:
            result = await self._extract_text_via_apigw(image_data)
            logger.info(f"🔍 APIGW 결과: {len(result)}개 텍스트")
            return result

        else:
            logger.error(f"❌ OCR 설정 오류")
            return []

    async def _extract_text_via_apigw(self, image_data: bytes) -> List[str]:
        """
        APIGW를 통해 OCR 텍스트 추출
        """
        logger.info(f"🔧 APIGW OCR 시작")
        try:
            # 이미지를 base64로 인코딩
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            logger.info(f"🔍 Base64 인코딩 완료: {len(image_base64)} chars")
            
            # APIGW 요청 페이로드
            payload = {
                "images": [
                    {
                        "format": "jpg",
                        "name": "demo",
                        "data": image_base64
                    }
                ],
                "requestId": "string",
                "version": "V2",
                "timestamp": int(time.time() * 1000)
            }
            
            # HTTP 헤더 (NCP APIGW 형식)
            headers = {
                "Content-Type": "application/json",
                "X-OCR-SECRET": self.api_key,
                "Accept": "application/json"
            }
            
            logger.info(f"🔍 APIGW 요청 준비 완료")
            
            # APIGW로 요청
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"🔍 APIGW OCR 요청 전송: {self.apigw_url}")
                response = await client.post(
                    self.apigw_url,
                    json=payload,
                    headers=headers
                )
                
                logger.info(f"🔍 APIGW 응답 코드: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ APIGW OCR 성공")
                    logger.info(f"🔍 응답 키들: {list(result.keys())}")
                    logger.info(f"🔍 전체 응답: {result}")
                    
                    # NCP OCR 응답에서 텍스트 추출
                    texts = []
                    if "images" in result:
                        for img in result["images"]:
                            if "fields" in img:
                                for field in img["fields"]:
                                    texts.append(field.get("inferText", ""))
                    
                    logger.info(f"🔍 추출된 텍스트 개수: {len(texts)}")
                    return texts if texts else []
                else:
                    logger.error(f"❌ APIGW OCR 실패: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ APIGW OCR 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    