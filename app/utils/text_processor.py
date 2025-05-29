"""
텍스트 처리 유틸리티

이 파일은 OCR 결과 텍스트를 정제하는 유틸리티 함수들을 제공합니다.
주요 기능:
1. 텍스트 정규화
2. 불필요한 문자 제거
3. 공백 처리
"""

import re

def clean_text(text: str) -> str:
    """
    OCR 결과 텍스트를 정제합니다.
    
    Args:
        text: 정제할 텍스트
        
    Returns:
        str: 정제된 텍스트
    """
    if not text:
        return ""
        
    # 소문자 변환
    text = text.lower()
    
    # 특수문자 제거 (단, 한글, 영문, 숫자, 공백은 유지)
    text = re.sub(r'[^\w\s가-힣]', '', text)
    
    # 연속된 공백을 하나로 통일
    text = re.sub(r'\s+', ' ', text)
    
    # 앞뒤 공백 제거
    text = text.strip()
    
    return text 