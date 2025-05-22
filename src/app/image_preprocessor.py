import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import os

#기울기 보정
def deskew(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

class ImagePreprocessor:
    def __init__(self):
        pass

    def preprocess_image(self, image_path):
        img = Image.open(image_path)
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
        cv2.imwrite(image_path, img_binary)
        return image_path