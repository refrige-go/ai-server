from google.cloud import vision
import os

def detect_text(image_path):
    """이미지에서 텍스트를 감지하는 함수"""
    # Vision API 클라이언트 생성
    client = vision.ImageAnnotatorClient()

    # 이미지 파일 읽기
    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    # Vision API 요청 생성
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        print('감지된 텍스트:')
        print(texts[0].description)
    else:
        print('텍스트가 감지되지 않았습니다.')

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

if __name__ == '__main__':
    # 테스트할 이미지 경로
    image_path = 'test.jpg'  # 여기에 실제 이미지 파일 경로를 입력하세요
    detect_text(image_path) 