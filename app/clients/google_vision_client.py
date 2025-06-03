"""
Google Vision API 클라이언트
<<<<<<< HEAD
"""

from google.cloud import vision
=======

이 파일은 Google Cloud Vision API와의 통신을 담당합니다.
주요 기능:
1. 이미지 텍스트 추출
2. OCR 결과 처리
3. API 에러 처리

구현 시 고려사항:
- API 키 관리
- 요청 제한 처리
- 에러 처리 및 재시도
- 응답 캐싱
- 비용 최적화
"""

from google.cloud import vision
from app.config.settings import get_settings
import asyncio
>>>>>>> dev
from typing import List

class GoogleVisionClient:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()
<<<<<<< HEAD
=======
        self.settings = get_settings()
>>>>>>> dev
    
    async def extract_text(self, image_data: bytes) -> List[str]:
        """
        이미지에서 텍스트를 추출합니다.
<<<<<<< HEAD
        """
        image = vision.Image(content=image_data)
        response = self.client.text_detection(image=image)
        texts = response.text_annotations
        if not texts:
            return []
        # 첫 번째는 전체 텍스트, 나머지는 개별 텍스트
        return [text.description for text in texts]
=======
        
        Args:
            image_data: 이미지 바이트 데이터
            
        Returns:
            List[str]: 추출된 텍스트 목록
        """
        # TODO: 구현 필요
        # 1. Vision API 호출
        # 2. 결과 파싱
        # 3. 에러 처리
        pass 
>>>>>>> dev
