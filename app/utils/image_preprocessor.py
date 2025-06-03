<<<<<<< HEAD
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io

def preprocess_image(image_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = ImageEnhance.Brightness(img).enhance(1.2)
    img = img.filter(ImageFilter.SHARPEN)
    if img.width < 1000:
        scale = 1000 / img.width
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    img_np = np.array(img)
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(img_gray, (3, 3), 0)
    _, img_binary = cv2.threshold(img_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, buffer = cv2.imencode('.jpg', img_binary)
    return buffer.tobytes()
=======
"""
이미지 전처리 유틸리티

이 파일은 OCR 처리 전 이미지 전처리를 담당합니다.
주요 기능:
1. 이미지 크기 조정
2. 이미지 품질 개선
3. 노이즈 제거
4. 대비 조정

구현 시 고려사항:
- 이미지 품질 최적화
- OCR 정확도 향상
- 처리 속도 최적화
- 메모리 사용량 최적화
"""

from PIL import Image
import io
from typing import Tuple

def preprocess_image(image_data: bytes) -> bytes:
    """
    OCR 처리를 위해 이미지를 전처리합니다.
    
    Args:
        image_data: 원본 이미지 바이트 데이터
        
    Returns:
        bytes: 전처리된 이미지 바이트 데이터
    """
    # TODO: 구현 필요
    # 1. 이미지 크기 조정
    # 2. 대비 조정
    # 3. 노이즈 제거
    # 4. 품질 최적화
    pass

def resize_image(image: Image.Image, max_size: Tuple[int, int]) -> Image.Image:
    """
    이미지 크기를 조정합니다.
    
    Args:
        image: PIL Image 객체
        max_size: 최대 크기 (width, height)
        
    Returns:
        Image.Image: 크기가 조정된 이미지
    """
    # TODO: 구현 필요
    pass 
>>>>>>> dev
