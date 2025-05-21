import os
import paddle
import cv2
import numpy as np
from paddleocr import PaddleOCR
import logging

logger = logging.getLogger(__name__)

class OptimizedGPUOCR:
    def __init__(self):
        # CUDA 설정
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
        paddle.device.set_device('gpu:0')
        
        # PaddleOCR 초기화
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="korean",
            use_gpu=True,
            gpu_mem=500,
            det_db_box_thresh=0.3,
            det_db_thresh=0.3,
            det_db_unclip_ratio=1.6,
            rec_thresh=0.5,
            cls_thresh=0.9,
            enable_mkldnn=False
        )
        logger.info("OptimizedGPUOCR 초기화 완료")
    
    def preprocess_image(self, image):
        """이미지 전처리 함수"""
        try:
            # 크기 조정
            if image.shape[1] < 1000:
                scale = 1000 / image.shape[1]
                image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # 이진화
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            # 샤프닝
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            sharpened = cv2.filter2D(binary, -1, kernel)
            return sharpened
        except Exception as e:
            logger.error(f"이미지 전처리 중 오류 발생: {str(e)}")
            raise
    
    def process_image(self, image_path):
        """이미지 OCR 처리 함수"""
        try:
            # 이미지 읽기
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("이미지를 읽을 수 없습니다.")
            
            # 전처리
            processed_image = self.preprocess_image(image)
            
            # OCR 실행
            result = self.ocr.ocr(processed_image, cls=True)
            
            return result
            
        except Exception as e:
            logger.error(f"OCR 처리 중 오류 발생: {str(e)}")
            return None

    def process_batch(self, images, batch_size=4):
        """여러 이미지 배치 처리 함수"""
        try:
            results = []
            for i in range(0, len(images), batch_size):
                batch = images[i:i + batch_size]
                batch_results = self.ocr.ocr(batch, cls=True)
                results.extend(batch_results)
            return results
        except Exception as e:
            logger.error(f"배치 처리 중 오류 발생: {str(e)}")
            return None

    @staticmethod
    def monitor_gpu_usage():
        """GPU 사용량 모니터링 함수"""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return {
                "used_memory": f"{info.used/1024**2:.2f}MB",
                "total_memory": f"{info.total/1024**2:.2f}MB",
                "usage_percent": f"{info.used/info.total*100:.2f}%"
            }
        except Exception as e:
            logger.error(f"GPU 모니터링 중 오류 발생: {str(e)}")
            return None 