"""
OpenAI 클라이언트

<<<<<<< HEAD
이 파일은 OpenAI API와의 통신을 담당합니다.
주요 기능:
1. 텍스트 임베딩 생성
2. API 응답 파싱
3. 에러 처리
4. 요청 제한 관리

구현 시 고려사항:
- API 키 관리
- 요청 제한 처리
- 에러 처리 및 재시도
- 비용 최적화
=======
OpenAI API와의 통신을 담당합니다.
업로드된 임베딩과 동일한 모델을 사용합니다.
>>>>>>> dev
"""

from openai import AsyncOpenAI
from app.config.settings import get_settings
from typing import List
import logging
<<<<<<< HEAD
import time
=======
import asyncio
>>>>>>> dev

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
<<<<<<< HEAD
        self.model = "text-embedding-ada-002"
=======
        # 업로드된 임베딩과 동일한 모델 사용
        self.model = "text-embedding-3-small"
>>>>>>> dev
        self.max_retries = self.settings.vector_embedding_max_retries
        self.request_delay = self.settings.vector_embedding_request_delay

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 목록의 임베딩을 생성합니다.
        
        Args:
            texts: 임베딩을 생성할 텍스트 목록
            
        Returns:
<<<<<<< HEAD
            List[List[float]]: 임베딩 목록
            
        Raises:
            Exception: API 호출 실패 시
        """
        try:
            # 1. API 호출
            response = await self._call_embedding_api(texts)
            
            # 2. 응답 파싱
=======
            List[List[float]]: 임베딩 목록 (1536차원)
        """
        try:
            # 단일 텍스트인 경우 리스트로 변환
            if isinstance(texts, str):
                texts = [texts]
            
            # API 호출
            response = await self._call_embedding_api(texts)
            
            # 응답 파싱
>>>>>>> dev
            return self._parse_embedding_response(response)
            
        except Exception as e:
            logger.error(f"Error in get_embeddings: {str(e)}")
            raise

<<<<<<< HEAD
    async def _call_embedding_api(
        self,
        texts: List[str]
    ) -> dict:
        """
        OpenAI 임베딩 API를 호출합니다.
        
        Args:
            texts: 임베딩을 생성할 텍스트 목록
            
        Returns:
            dict: API 응답
            
        Raises:
            Exception: API 호출 실패 시
=======
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

    async def _call_embedding_api(self, texts: List[str]) -> dict:
        """
        OpenAI 임베딩 API를 호출합니다.
>>>>>>> dev
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
<<<<<<< HEAD
                time.sleep(self.request_delay)

    def _parse_embedding_response(
        self,
        response: dict
    ) -> List[List[float]]:
        """
        임베딩 API 응답을 파싱합니다.
        
        Args:
            response: API 응답
            
        Returns:
            List[List[float]]: 임베딩 목록
        """
        return [data.embedding for data in response.data] 
=======
                await asyncio.sleep(self.request_delay)

    def _parse_embedding_response(self, response: dict) -> List[List[float]]:
        """
        임베딩 API 응답을 파싱합니다.
        """
        return [data.embedding for data in response.data]
>>>>>>> dev
