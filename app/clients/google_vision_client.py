"""
Google Vision API 클라이언트
"""

from google.cloud import vision
from typing import List

class GoogleVisionClient:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()
    
    async def extract_text(self, image_data: bytes) -> List[str]:
        """
        이미지에서 텍스트를 추출합니다.
        """
        image = vision.Image(content=image_data)
        response = self.client.text_detection(image=image)
        texts = response.text_annotations
        if not texts:
            return []
        # 첫 번째는 전체 텍스트, 나머지는 개별 텍스트
        return [text.description for text in texts]