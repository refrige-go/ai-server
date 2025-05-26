import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\User\ocr-vision-460506-12c47533f78d.json"

from google.cloud import vision
import re
import requests

def is_valid_product_name(name):
    # 1. 숫자만 있는 경우 제외
    if re.fullmatch(r'\d+', name):
        return False
    # # 2. 날짜/시간 패턴 제외 (예: 20210117, 15:57 등)
    # if re.search(r'\d{4}[-]?\d{2}[-]?\d{2}', name):  # 20210117, 2021-01-17 등
    #     return False
    # if re.search(r'\d{1,2}:\d{2}', name):  # 15:57 등
    #     return False
    # 3. POS, 총 품목, 합계, 금액 등 키워드 포함 제외
    exclude_keywords = ['POS', '총 품목', '합계', '금액', '수량', '구매', '상품명','단가','전화']
    for keyword in exclude_keywords:
        if keyword.replace(" ", "") in name.replace(" ", ""):
            return False
    # 4. 영문+숫자, 한글+숫자 조합 제외 (예: abc123, 콜라500ml 등)
    if re.search(r'[가-힣a-zA-Z]+[0-9]+', name):
        return False
    if re.search(r'[0-9]+[a-zA-Z가-힣]+', name):
        return False
    # 5. 길이가 너무 짧은 경우 제외
    if len(name.strip()) < 2:
        return False
    return True


def filter_korean_number(items):
    # 한글+숫자 조합만 남기지 않도록 필터링
    filtered = []
    for item in items:
        # 예: '초코파이12개', '사과500g' 등은 제외
        if not re.search(r'[가-힣]+[0-9]+', item):
            filtered.append(item)
    return filtered

def filter_kor_eng_num(items):
    filtered = []
    for item in items:
        # 한글+숫자, 영어+숫자, 숫자+영어 조합이 포함된 항목은 제외
        if re.search(r'[가-힣]+[0-9]+', item):  # 한글+숫자
            continue
        if re.search(r'[a-zA-Z]+[0-9]+', item):  # 영어+숫자
            continue
        if re.search(r'[0-9]+[a-zA-Z]+', item):  # 숫자+영어
            continue
        filtered.append(item)
    return filtered   


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

        # === 날짜만 정규표현식으로 추출 ===
        purchase_date = None
        for line in lines:
            # yyyy-mm-dd 또는 yyyy-mm-dd hh:mm:ss 형식 추출
            match = re.search(r'\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?', line)
            if match:
                purchase_date = match.group()
                break
        print("구매일자:", purchase_date)
        # =======================================

        # 1차: 품목만 추출
        product_names = [line for line in lines if is_product_name(line)]
        # 2차: 정제
        cleaned_products = [clean_product_name(name) for name in product_names if clean_product_name(name)]
        # 3차: 불필요한 값 필터링
        filtered_products = [name for name in cleaned_products if is_valid_product_name(name)]
        print("최종 품목명:", filtered_products)

        # JSON 형태로 변환
        json_data = {
            "rawText": texts[0].description,
            "extractedProducts": filtered_products,
            "totalProducts": len(filtered_products),
            "purchaseDate": "2018-04-25 10:12:12" #구매날짜 추가
        }

        # 백엔드 API 호출
        try:
            api_response = requests.post(
                'http://localhost:8080/api/products/match',
                json=filtered_products,  # 문자열 리스트를 직접 전송
                headers={'Content-Type': 'application/json'}
            )
            api_response.raise_for_status()  # HTTP 에러 체크
            matched_products = api_response.json()
            print("매칭된 상품:", matched_products)
            # return matched_products, purchase_date -----------------1
            return {
                "ingredients": matched_products,  # 또는 filtered_products
                "purchaseDate": purchase_date
            }
        except requests.exceptions.RequestException as e:
            print(f"백엔드 API 호출 실패: {e}")
            return [], purchase_date

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
    image_path = 'fruitbill.jpg'  # 실제 이미지 파일 경로 -> ocr-google.py를 실행시킬 때 인식하는 사진
    detect_text(image_path)