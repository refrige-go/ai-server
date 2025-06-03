import re
import logging
from app.config.db import find_in_database

# 불필요한 단어/기호 리스트 (필요시 추가)
REMOVE_WORDS = [
    '내용량', '식품', '유형', '가공품', '원재료', '품목', '보고', '번호',
    '포장', '재질', '보관', '방법', '반품', '문의', '구입처', '이용', '개봉', '후에', '서늘한', '곳에',
    '하세요', '비율', '섞어서', '기호', '따라', '제품', '원료', '하는', '설탕', '가미', '해서', '드세요',
    '시설', '에서', '하고', '있습니다', '소비자', '분쟁', '해결', '기준', '의거', '교환', '또는', '보상',
    '받으실수', '있습니다', '부정', '불량', '신고', '국번', '없이', '마을', '기업', '업소명', '및', '소재지',
    '농업', '회사', '법인', '사랑', '전북', '정읍시', '칠보면', '촌길', '싸리재', '고객', '센터', '홈페이지',
    'www.ssarijai.com', '백태', '국산', '폴리에틸렌', '상온'
]

def extract_product_section(full_text: str) -> list:
    """
    영수증 전체 텍스트에서 상품명(메뉴) 부분만 추출하는 함수
    """
    lines = full_text.split('\n')
    products = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 상품명+수량+금액 패턴 (예: 크라운산도딸기 1 2,500)
        if re.search(r'[가-힣a-zA-Z0-9]+.*\d+[,\.]?\d*$', line):
            products.append(line)
    return products

def clean_text(text: str) -> str:
    text = text.strip()
    # 한글/영문/숫자만 남기기
    text = re.sub(r'[^가-힣a-zA-Z0-9]', '', text)
    if not text or len(text) < 2:
        return ''
    # 불필요한 단어가 포함되어 있으면 제거
    if any(word in text for word in REMOVE_WORDS):
        return ''
    return text

def clean_ocr_results(ocr_results: list) -> list:
    """OCR 결과 리스트를 정제하는 함수"""
    cleaned_words = set()  # 중복 방지를 위해 set 사용

    # 1. 첫 번째 요소(전체 텍스트) 처리
    if ocr_results and isinstance(ocr_results[0], str):
        first_text = ocr_results[0]
        words = re.split(r'[\n\s,()\[\]<>*•|:·%]+', first_text)
        for word in words:
            cleaned = clean_text(word)
            if cleaned:
                cleaned_words.add(cleaned)

    # 2. 나머지 요소들 처리
    for word in ocr_results[1:]:
        if isinstance(word, str):
            cleaned = clean_text(word)
            if cleaned:
                cleaned_words.add(cleaned)

    return list(cleaned_words)

# 상품명 패턴 필터 함수
def is_product_name(text):
    # 한글로 시작하고, 한글/영문/숫자 조합, 길이 3~20자
    return bool(re.match(r'^[가-힣][가-힣a-zA-Z0-9]{2,20}$', text))