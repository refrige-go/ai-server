import re
import logging
from app.config.db import find_in_database
from app.utils.ocr_head_noun_extractor import extract_head_noun

# 불필요한 단어/기호 리스트 (필요시 추가)
REMOVE_WORDS = [
    '내용량', '식품', '유형', '가공품', '원재료', '품목', '보고', '번호',
    '포장', '재질', '보관', '방법', '반품', '문의', '구입처', '이용', '개봉', '후에', '서늘한', '곳에',
    '하세요', '비율', '섞어서', '기호', '따라', '제품', '원료', '하는', '설탕', '가미', '해서', '드세요',
    '시설', '에서', '하고', '있습니다', '소비자', '분쟁', '해결', '기준', '의거', '교환', '또는', '보상',
    '받으실수', '있습니다', '부정', '불량', '신고', '국번', '없이', '마을', '기업', '업소명', '및', '소재지',
    '농업', '회사', '법인', '사랑', '전북', '정읍시', '칠보면', '촌길', '싸리재', '고객', '센터', '홈페이지',
    'www.ssarijai.com', '백태', '국산', '폴리에틸렌', '상온',"영수증", "카드", "결제", "편의점", "고객센터", "구매일자", "합계", "매출", "부가세",
    "금액", "주소", "전화", "환불", "안내", "플랫폼", "대한민국 1등", "수산물판매", "균일가", "판매", "대리", '소공점', '빌딩', '수량', '단가', 
    '합계', '매출', '결제', '카드', '현금', '고객', '센터', '주소', '전화', '환불', '안내', '영수증', '매장', '점포', '편의점', '마트', '백화점', '지점',
    "공급가액", "거스름돈"
]

def is_not_ingredient(text: str) -> bool:
    # 주소/매장명/안내문구 패턴
    if any(word in text for word in REMOVE_WORDS):
        return True
    if len(text) > 10:  # 너무 긴 문장(식재료명은 보통 짧음)
        return True
    if re.search(r'(시|구|동|로|길|층)', text):  # 주소 패턴
        return True
    if re.search(r'(점|매장|지점|센터|빌딩)$', text):  # 매장명 패턴
        return True
    return False

def extract_product_section(full_text: str) -> list:
    lines = full_text.split('\n')
    products = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 불필요한 단어가 포함된 줄은 제외
        if any(word in line for word in REMOVE_WORDS):
            continue
        # 상품명 후보: 한글/영문 포함된 줄만
        if re.search(r'[가-힣a-zA-Z]', line):
            # 각 상품명에 핵심 명사 추출 적용
            head_noun_result = extract_head_noun(line)
            processed_product = head_noun_result.head_noun
            if processed_product:  # 추출된 핵심 명사가 있으면 추가
                products.append(processed_product)
    return products

def clean_text(text: str) -> str:
    text = text.strip()
    
    # 1. 괄호 및 괄호 안 내용 제거
    text = re.sub(r'\([^)]*\)', '', text)

    # 2. 숫자+영어(단위) 제거 (예: 16.9도, 400g, 1L, 32462, B 등)
    text = re.sub(r'[0-9]+[a-zA-Z가-힣]*', '', text)

    # 3. 영어만 남은 경우 제거
    text = re.sub(r'[a-zA-Z]', '', text)

    # 1. 숫자 + 단위 패턴 제거 (예: 300G, 1L, 500ml, 3,900)
    text = re.sub(r'\d+[A-Za-z]*', '', text)  # 숫자+단위 제거
    text = re.sub(r'\d+', '', text)  # 남은 숫자들 제거
    
    # 2. 특수문자 제거 (한글/영문만 남기기)
    text = re.sub(r'[^가-힣a-zA-Z]', '', text)
    
    if not text or len(text) < 2:
        return ''
    
    # 3. 불필요한 단어가 포함되어 있으면 제거
    if any(word in text for word in REMOVE_WORDS):
        return ''
    
    # 4. 핵심 명사 추출 적용 (복합명사구인 경우)
    if len(text.split()) > 1:  # 공백으로 구분된 복합명사구
        head_noun_result = extract_head_noun(text)
        return head_noun_result.head_noun
    
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