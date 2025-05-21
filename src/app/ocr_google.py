import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\User\ocr-vision-460506-12c47533f78d.json"

from google.cloud import vision
import re

def is_product_name(line):
    if re.fullmatch(r"\d{10,13}", line.replace(" ", "")):
        return False
    if re.fullmatch(r"[\d, ]+", line):
        return False
    if any(keyword in line for keyword in ["합계", "총액", "부가세", "면세", "과세", "가 세"]):
        return False
    if re.search(r"[가-힣a-zA-Z]", line):
        return True
    return False

def clean_product_name(name):
    # 1. 괄호, 특수문자, 조), 통), e데이, 행사, 1+1 등 제거
    name = re.sub(r'조\)|통\)|e데이|행사|1\+1', '', name)
    # 2. 단위(숫자+g, 숫자+ml, 숫자+L 등) 제거
    name = re.sub(r'\d+\s*(g|ml|L|kg|개|봉|팩|통|캔)', '', name, flags=re.IGNORECASE)
    # 3. 기타 불필요한 특수문자, 공백 정리
    name = re.sub(r'[^가-힣a-zA-Z0-9 ]', '', name)
    # 4. 앞뒤 공백 정리
    name = name.strip()
    return name

def detect_text(image_path):
    client = vision.ImageAnnotatorClient()
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        print('감지된 텍스트:')
        print(texts[0].description)
        # 줄 단위로 분리
        lines = texts[0].description.split('\n')
        # 품목만 추출
        product_names = [line for line in lines if is_product_name(line)]
        # 품목명 정제
        cleaned_products = [clean_product_name(name) for name in product_names if clean_product_name(name)]
        print("최종 품목명:", cleaned_products)
        return cleaned_products
    else:
        print('텍스트가 감지되지 않았습니다.')
        return []

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

if __name__ == '__main__':
    image_path = 'goodbill.jpg'  # 실제 이미지 파일 경로
    detect_text(image_path)