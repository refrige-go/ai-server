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
    
    # 적응형 이진화
    img_adaptive = cv2.adaptiveThreshold(
        img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    # 노이즈 제거
    img_denoised = cv2.fastNlMeansDenoising(img_adaptive, None, 30, 7, 21)
    # 샤프닝
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    img_sharp = cv2.filter2D(img_denoised, -1, kernel)
    # (필요시) 컬러 반전
    # img_sharp = cv2.bitwise_not(img_sharp)
    _, buffer = cv2.imencode('.jpg', img_sharp)
    return buffer.tobytes()