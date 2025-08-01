"""
OpenAI 클라이언트

OpenAI API와의 통신을 담당합니다.
업로드된 임베딩과 동일한 모델을 사용합니다.
"""

from openai import AsyncOpenAI
from app.config.settings import get_settings
from typing import List
import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        self.settings = get_settings()
        
        # httpx 클라이언트 호환성을 위한 설정
        try:
            # 최신 방식으로 초기화 시도
            self.client = AsyncOpenAI(
                api_key=self.settings.openai_api_key,
                timeout=30.0
            )
        except TypeError:
            # 구버전 호환성을 위한 대안
            import httpx
            http_client = httpx.AsyncClient(timeout=30.0)
            self.client = AsyncOpenAI(
                api_key=self.settings.openai_api_key,
                http_client=http_client
            )
        
        # 업로드된 임베딩과 동일한 모델 사용
        self.model = "text-embedding-3-small"
        self.max_retries = self.settings.vector_embedding_max_retries
        self.request_delay = self.settings.vector_embedding_request_delay

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 목록의 임베딩을 생성합니다.
        
        Args:
            texts: 임베딩을 생성할 텍스트 목록
            
        Returns:
            List[List[float]]: 임베딩 목록 (1536차원)
        """
        try:
            # 단일 텍스트인 경우 리스트로 변환
            if isinstance(texts, str):
                texts = [texts]
            
            # API 호출
            response = await self._call_embedding_api(texts)
            
            # 응답 파싱
            return self._parse_embedding_response(response)
            
        except Exception as e:
            logger.error(f"Error in get_embeddings: {str(e)}")
            raise

    async def get_embedding(self, text: str) -> List[float]:
        """
        단일 텍스트의 임베딩을 생성합니다.
        
        Args:
            text: 임베딩을 생성할 텍스트
            
        Returns:
            List[float]: 임베딩 벡터 (1536차원)
        """
        embeddings = await self.get_embeddings([text])
        return embeddings[0]

    async def infer_ingredient_from_ocr(self, ocr_text: str, context: str = "") -> str:
        """
        OCR 텍스트에서 핵심 식재료명을 추출하거나 비식재료는 None을 반환
        """
        
        prompt = f"""당신은 한국 마트 상품명에서 실제 식재료를 추출하는 전문가입니다.

    입력된 상품명: "{ocr_text}"

    분석 과정:
    1. 상품 카테고리 판단
    A. 식품/식재료 카테고리 (추출 대상)
        - 기본 식재료: 고기류, 해산물, 채소, 과일, 곡물, 유제품 등
        - 조미료/소스: 간장, 된장, 고추장, 각종 소스류, 식용유, 참기름 등
        - 가공식품: 라면, 과자, 음료, 즉석식품, 냉동식품 등
        - 반조리/즉석식품: 만두, 피자, 냉동밥, 죽 등
    
    B. 비식품 카테고리 (제외 대상)
        - 생활용품: 세제, 비누, 화장지, 샴푸, 치약 등
        - 주방용품: 냄비, 프라이팬, 주방도구, 일회용품 등
        - 화장품/미용: 로션, 크림, 마스크팩 등
        - 문구/사무: 노트, 펜, 테이프 등
        - 청소용품: 청소기, 수세미, 장갑 등

    2. 제외해야 할 요소
    - 브랜드명: 청정원, 해피바스, CJ, 풀무원 등
    - 수식어: 신선한, 맛있는, 바삭한 등
    - 용량/규격: 1kg, 300g, 대/중/소 등
    - 행사/광고 문구: 특가, 세일, 1+1, 행사 등
    - 포장 형태: 박스, 봉지, 팩 등

    3. 정확한 명칭 추출 규칙
    - 복합어는 의미 단위로 띄어쓰기
    - 고유명사는 붙여쓰기
    - 외래어는 표준 표기법 준수
    
    올바른 예시:
    - "냉동왕교자만두" → "냉동 왕교자 만두"
    - "로제파스타소스" → "로제 파스타 소스"
    - "찌개용두부" → "두부"
    - "구운김밥김" → "김"

    4. 판단 기준
    - 실제 섭취/조리 가능한 식품인가?
    - 식재료의 본질적 형태를 유지하는가?
    - 브랜드나 포장 형태가 아닌 실제 내용물인가?

    답변 형식:
    - 식품/식재료인 경우: 정확한 띄어쓰기가 된 식품/식재료명만 답변
    - 식품/식재료가 아닌 경우: "NOT_INGREDIENT"

    주의사항:
    1. 브랜드명이나 수식어는 제거
    2. 실제 식재료/식품 성분만 추출
    3. 비식품은 반드시 제외
    4. 행사/광고 문구 포함된 경우 제외
    5. 의심스러운 경우 "NOT_INGREDIENT" 반환

    답변:"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 마트 상품명에서 핵심 식재료를 추출하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=20
            )
            
            # 결과 정제 강화
            result = response.choices[0].message.content.strip()
            result = result.replace('"', '').replace("'", "")
            
            # 화살표나 추가 설명이 있는 경우 첫 번째 단어만 사용
            if "→" in result:
                result = result.split("→")[0].strip()
            if " " in result:  # 스페이스로 구분된 경우 첫 단어만
                result = result.split()[0].strip()

            if result == "NOT_INGREDIENT":
                logger.info(f"🚫 비식재료 제외: '{ocr_text}'")
                return None
                
            logger.info(f"✅ 식재료 추출: '{ocr_text}' → '{result}'")
            return result
                
        except Exception as e:
            logger.error(f"AI 추론 오류: {e}")
            return ocr_text


    async def _call_embedding_api(self, texts: List[str]) -> dict:
        """
        OpenAI 임베딩 API를 호출합니다.
        """
        for attempt in range(self.max_retries):
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
                return response
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(
                    f"Retry {attempt + 1}/{self.max_retries} "
                    f"after error: {str(e)}"
                )
                await asyncio.sleep(self.request_delay)

    def _parse_embedding_response(self, response: dict) -> List[List[float]]:
        """
        임베딩 API 응답을 파싱합니다.
        """
        return [data.embedding for data in response.data]

# 싱글톤 인스턴스
openai_client = OpenAIClient()