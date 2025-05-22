from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
from PIL import Image, ImageEnhance
from PIL import ImageFilter
import os
import logging
import tempfile
import shutil
import re
import paddle
import sqlite3
from flask import Response
import json
import cv2
import numpy as np
import pymysql
from rapidfuzz import fuzz, process
from ocr_optimizer import OptimizedGPUOCR  # 새로운 최적화 클래스 import
from image_preprocessor import ImagePreprocessor
from konlpy.tag import Okt

okt = Okt()

def extract_nouns(text):
    return okt.nouns(text)

print(paddle.utils.run_check())
# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
ocr = PaddleOCR(use_angle_cls=True, lang="korean", det_db_box_thresh=0.5, drop_score=0.3)
preprocessor = ImagePreprocessor()  # 전처리기 인스턴스 생성

def get_db_connection():
    print("7-1-1. get_db_connection 진입")
    try:
        connection = pymysql.connect(
            host='localhost',       # MySQL 서버 주소
            port=3306,              # MySQL 포트 번호
            database='refrige_go',  # DB 이름
            user='noname',          # MySQL 사용자 이름
            password='noname',      # MySQL 비밀번호
            charset='utf8' 
        )
        print("7-1-2. DB 연결 성공")
        return connection
    except Exception as e:
        print("7-1-3. DB 연결 실패:", e)
        #raise
        return None

def clean_product_name(name):
    # 단위/수량 패턴 정의
    unit_patterns = [
        r'\d+\.?\d*\s*(?:kg|g|ml|l|개|병|팩|박스|봉|통|장|매|입|세트|캔|포|봉지|봉투|개입|매입|매수|매장|매통|매병|매팩|매박스|매봉|매통|매캔|매포|매봉지|매봉투)',  # 숫자 + 단위
        r'\d+\.?\d*\s*(?:원|원화|원권|원짜리)',  # 가격
        r'\d+\.?\d*\s*(?:%|퍼센트|프로)',  # 퍼센트
        r'\d+\.?\d*\s*(?:kcal|칼로리)',  # 칼로리
        r'\d+\.?\d*\s*(?:cm|mm|m)',  # 길이
        r'\d+\.?\d*\s*(?:시간|분|초)',  # 시간
        r'\d+\.?\d*\s*(?:년|월|일)',  # 날짜
    ]
    
    # 모든 단위/수량 패턴 제거
    cleaned = name
    for pattern in unit_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # 한글, 영문, 숫자만 남기고 나머지 제거
    cleaned = re.sub(r'[^가-힣a-zA-Z0-9]', '', cleaned)
    
    # 불필요한 접미사 제거
    cleaned = re.sub(r'[-./]+$', '', cleaned)
    
    # 연속된 공백 제거
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

def filter_quantity_and_units(text):
    """단위/수량/용량 등을 필터링하는 함수"""
    # 단위/수량 패턴 정의
    patterns = [
        r'\d+\.?\d*\s*(?:kg|g|ml|l|개|병|팩|박스|봉|통|장|매|입|세트|캔|포|봉지|봉투|개입|매입|매수|매장|매통|매병|매팩|매박스|매봉|매통|매캔|매포|매봉지|매봉투)',
        r'\d+\.?\d*\s*(?:원|원화|원권|원짜리)',
        r'\d+\.?\d*\s*(?:%|퍼센트|프로)',
        r'\d+\.?\d*\s*(?:kcal|칼로리)',
        r'\d+\.?\d*\s*(?:cm|mm|m)',
        r'\d+\.?\d*\s*(?:시간|분|초)',
        r'\d+\.?\d*\s*(?:년|월|일)'
    ]
    
    # 모든 패턴 제거
    filtered_text = text
    for pattern in patterns:
        filtered_text = re.sub(pattern, '', filtered_text, flags=re.IGNORECASE)
    
    return filtered_text.strip()
   

# 카테고리 정의
CATEGORIES = {
    "식품": {
        "과일": ["사과", "바나나", "오렌지", "포도", "감귤", "망고"],
        "채소": ["상추", "양파", "당근", "오이", "토마토", "고추"],
        "육류": ["소고기", "돼지고기", "닭고기", "양고기"],
        "수산물": ["생선", "새우", "오징어", "문어", "게"],
        "유제품": ["우유", "치즈", "요구르트", "버터"],
        "가공식품": ["라면", "과자", "빵", "햄", "소시지"]
    }
}
#하나도 포함되지 않는 경우 기타 
def categorize_product(matched_name):
    for main_category, sub_categories in CATEGORIES.items():
        for sub_category, keywords in sub_categories.items():
            for keyword in keywords:
                if keyword in matched_name:
                    return main_category, sub_category
    return "기타", "기타"

#DB와 연결

def filter_products_fuzzy(product_names):
    print("7-1. filter_products_fuzzy 진입, 상품명 리스트:", product_names)
    conn = get_db_connection()
    if conn is None:
        print("7-1-4. DB 연결이 None입니다! 연결 실패!")
        return []
    print("7-2. DB 연결 성공")
    filtered_products = []
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT ai_ingredient_name FROM ai_ingredients')
        db_names = [row[0] for row in cursor.fetchall()]
        print("7-3. DB 상품명 리스트:", db_names)
        for name in product_names:
            cleaned_name = clean_product_name(name)
            print("7-4. 정제된 상품명:", cleaned_name)
            if not cleaned_name:
                continue
            match, score, _ = process.extractOne(cleaned_name, db_names, scorer=fuzz.ratio)
            print(f"7-5. 유사도 매칭: {cleaned_name} vs {match} (score: {score})")
            if score >= 70:  # 0~100, 70 이상이면 유사하다고 판단
                main_category, sub_category = categorize_product(match)
                filtered_products.append({
                    "original_name": name,
                    "matched_name": match,
                    "similarity": score,
                    "main_category": main_category,
                    "sub_category": sub_category
                })
        print("7-6. for문 종료, 필터링 결과:", filtered_products)
    finally:
        cursor.close()
        conn.close()
        print("7-7. 커서/커넥션 종료")
    return filtered_products


@app.route('/ocr', methods=['POST'])
def process_ocr():
    print("====== 1.요청 받음 =====")
    try:
        # 파일 업로드 확인
        if 'file' not in request.files:
            print("=====2. 파일 없음======")
            return jsonify({"error": "이미지 파일이 필요합니다."}), 400

        file = request.files['file']
        if file.filename == '':
            print("=====3. 파일 이름 없음=====")
            return jsonify({"error": "파일 이름이 비어 있습니다."}), 400

        # 임시 파일로 저장
        print("=====4. 파일 저장 시작=====")
        temp_dir = tempfile.mkdtemp()
        image_path = os.path.join(temp_dir, file.filename)
        file.save(image_path)

        preprocessor = ImagePreprocessor()
        preprocessed_path = preprocessor.preprocess_image(image_path)
        result = ocr.ocr(preprocessed_path, cls=True)

        if not result or not result[0] or not isinstance(result[0], list):
            raise ValueError("OCR 결과가 비어 있습니다.")

        texts = [line[1][0] for line in result[0] if len(line) > 1 and len(line[1]) > 0]

        # 품목 추출
        items = []
        i = 0
        while i < len(texts):
            logger.info(f"Line {i}: {texts[i]}")
            if texts[i] == "상품":
                if i + 3 < len(texts):  # i + 3만 확인하면 됨 (이름만 필요하므로)
                    filtered_name = filter_quantity_and_units(texts[i + 3].strip())
                    item = {
                        "name": texts[i + 3].strip() if i + 3 < len(texts) else ''
                    }
                    items.append(item)
                    i += 7  # 다음 상품으로 이동
                else:
                    i += 1
            else:
                i += 1

        # 상품 이름만 추출
        product_names = [item["name"] for item in items if item["name"]]
        
        #불용어처리
        stopwords = ["소스", "행사", "통조림"]
        nouns_list = []
        for name in product_names:
            nouns = extract_nouns(name)
            print(f"상품명: {name} → 명사 추출: {nouns}")
            filtered = [noun for noun in nouns if noun not in stopwords]
            print(f"불용어 제거 후: {filtered}")
            nouns_list.extend(filtered) 

        # 만약 "상품" 키워드가 없어 상품명이 하나도 없다면, 추정 로직으로 대체
        if not nouns_list:
            exclude_keywords = [
                "합계", "총액", "금액", "부가세", "포인트", "결제", "현금", "카드", "승인", "거절", "고객", "영수증",
                "국내산", "번호", "전화", "환불", "할인", "잔액", "NO", "소계"
            ]
            product_candidates = []
            for text in texts:
                # 한글만 포함되며, 숫자나 날짜 형식이 아니고, 제외 키워드도 포함하지 않는 경우
                if (
                    re.match(r'^[가-힣A-Za-z0-9\s\-\+]{2,}$', text) and
                    not any(keyword in text for keyword in exclude_keywords)
                ):
                    only_korean = re.sub(r'[^가-힣]', '', text)
                    if only_korean:  # 한글이 하나라도 있으면 추가
                        product_candidates.append(only_korean)

            product_names = product_candidates

             # 대체된 상품명으로 다시 명사 추출 및 불용어 제거
            for name in product_names:
                nouns = extract_nouns(name)
                filtered = [noun for noun in nouns if noun not in stopwords]
                nouns_list.extend(filtered)

        print("6. OCR 완료")
        print("7. DB 필터링 시작")

        #==== 필터링 시작 ====#
        filtered_products = filter_products_fuzzy(nouns_list)
        print("8. DB 필터링 완료")

        # 임시 파일 및 디렉토리 삭제
        shutil.rmtree(temp_dir, ignore_errors=True)

        return jsonify({
            "product_names": product_names,
            "nouns_list": nouns_list,
            "filtered_products": filtered_products
        })

    except Exception as e:
        print("9. 예외 발생:", e)
        logger.error(f"OCR 처리 중 오류 발생: {str(e)}")
        # 예외 발생 시에도 임시 파일 삭제
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({"error": str(e)}), 500
        

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)  # 개발 중 debug=True 추천