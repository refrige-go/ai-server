"""
OpenSearch 클라이언트

이 파일은 OpenSearch와의 통신을 담당합니다.
주요 기능:
1. 레시피 검색
2. 벡터 검색
3. 인덱스 관리
4. 에러 처리

구현 시 고려사항:
- 연결 관리
- 에러 처리 및 재시도
- 성능 최적화
- 로깅
"""

from opensearchpy import AsyncOpenSearch, OpenSearch, helpers
from app.config.settings import get_settings
from typing import List, Dict, Any
import logging
import json
import numpy as np

logger = logging.getLogger(__name__)

class OpenSearchClient:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenSearch(
            hosts=[self.settings.opensearch_host],
            http_auth=(
                self.settings.opensearch_user,
                self.settings.opensearch_password
            ),
            use_ssl=True,
            verify_certs=False,
            ssl_show_warn=False
        )
        self.index_name = "recipes"
        self.vector_field = "ingredient_embedding"

    async def search_recipes(
        self,
        embeddings: List[List[float]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        벡터 기반 레시피 검색을 수행합니다.
        
        Args:
            embeddings: 재료 임베딩 목록
            limit: 검색 결과 제한
            
        Returns:
            List[Dict[str, Any]]: 검색된 레시피 목록
            
        Raises:
            Exception: 검색 실패 시
        """
        try:
            # 1. 검색 쿼리 구성
            query = self._build_search_query(embeddings, limit)
            
            # 2. 검색 실행
            response = self.client.search(
                index=self.index_name,
                body=query
            )
            
            # 3. 결과 파싱
            return self._parse_search_results(response)
            
        except Exception as e:
            logger.error(f"Error in search_recipes: {str(e)}")
            raise

    def _build_search_query(
        self,
        embeddings: List[List[float]],
        limit: int
    ) -> Dict[str, Any]:
        """
        검색 쿼리를 구성합니다.
        
        Args:
            embeddings: 재료 임베딩 목록
            limit: 검색 결과 제한
            
        Returns:
            Dict[str, Any]: 검색 쿼리
        """
        return {
            "size": limit,
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'ingredient_embedding') + 1.0",
                        "params": {"query_vector": embeddings[0]}
                    }
                }
            }
        }

    def _parse_search_results(
        self,
        response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        검색 결과를 파싱합니다.
        
        Args:
            response: OpenSearch 응답
            
        Returns:
            List[Dict[str, Any]]: 파싱된 레시피 목록
        """
        recipes = []
        for hit in response["hits"]["hits"]:
            recipe = hit["_source"]
            recipe["score"] = hit["_score"]
            recipes.append(recipe)
        return recipes

    async def vector_search(
        self,
        index: str,
        vector: List[float],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        벡터 검색 수행
        
        Args:
            index: 검색할 인덱스 이름
            vector: 검색 벡터
            limit: 반환할 결과 수
            
        Returns:
            검색 결과 리스트
        """
        query = {
            "size": limit,
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": vector}
                    }
                }
            }
        }
        
        response = self.client.search(
            index=index,
            body=query
        )
        
        return response["hits"]["hits"]

    async def index_document(
        self,
        index: str,
        document: Dict[str, Any],
        embedding: List[float]
    ) -> bool:
        """
        문서 인덱싱
        
        Args:
            index: 인덱스 이름
            document: 인덱싱할 문서
            embedding: 문서의 벡터 임베딩
            
        Returns:
            성공 여부
        """
        try:
            document["embedding"] = embedding
            self.client.index(
                index=index,
                body=document,
                id=document.get("id") or document.get("rcp_seq")
            )
            return True
        except Exception as e:
            print(f"Error indexing document: {e}")
            return False

    async def bulk_index(
        self,
        index: str,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> bool:
        """
        대량 문서 인덱싱
        
        Args:
            index: 인덱스 이름
            documents: 인덱싱할 문서 리스트
            embeddings: 문서들의 벡터 임베딩 리스트
            
        Returns:
            성공 여부
        """
        try:
            actions = []
            for doc, embedding in zip(documents, embeddings):
                doc["embedding"] = embedding
                action = {
                    "_index": index,
                    "_id": doc.get("id") or doc.get("rcp_seq"),
                    "_source": doc
                }
                actions.append(action)
            
            helpers.bulk(self.client, actions)
            return True
        except Exception as e:
            print(f"Error bulk indexing documents: {e}")
            return False

    async def close(self):
        """
        OpenSearch 클라이언트 연결을 종료합니다.
        """
        await self.client.close() 