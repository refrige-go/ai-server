"""
OpenSearch 클라이언트

recipe-ai-project의 로컬 OpenSearch와 호환되도록 수정된 클라이언트입니다.
"""

from opensearchpy import OpenSearch
from app.config.settings import get_settings
from typing import List, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class OpenSearchClient:
    def __init__(self):
        self.settings = get_settings()
        
        # 로컬/AWS 환경에 따른 설정 분기
        opensearch_host = self.settings.opensearch_host
        opensearch_port = getattr(self.settings, 'opensearch_port', 9200)
        
        # 환경별 인증 설정
        if opensearch_host in ['localhost', '127.0.0.1']:
            # 로컬 환경 (recipe-ai-project OpenSearch)
            auth = None
            use_ssl = False
            verify_certs = False
            port = opensearch_port
        else:
            # AWS 환경
            auth = (self.settings.opensearch_username, self.settings.opensearch_password) if self.settings.opensearch_username else None
            use_ssl = True
            verify_certs = True
            port = 443
        
        self.client = OpenSearch(
            hosts=[{'host': opensearch_host, 'port': port}],
            http_auth=auth,
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            timeout=30,  # int로 설정
            max_retries=3,
            retry_on_timeout=True
        )
        
        # recipe-ai-project와 동일한 인덱스명 사용
        self.recipes_index = "recipes"
        self.ingredients_index = "ingredients"
        
        # 테스트용 인덱스 (없을 경우)
        self.recipes_index_fallback = "recipes_index" 
        self.ingredients_index_fallback = "ingredients_index"
        
        logger.info(f"OpenSearch 클라이언트 초기화: {opensearch_host}:{port}")

    async def test_connection(self) -> bool:
        """
        OpenSearch 연결 테스트
        """
        try:
            info = self.client.info()
            logger.info(f"OpenSearch 연결 성공: {info['version']['number']}")
            return True
        except Exception as e:
            logger.error(f"OpenSearch 연결 실패: {str(e)}")
            return False

    async def search_recipes_by_ingredients(
        self,
        ingredient_embeddings: List[List[float]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        재료 임베딩을 기반으로 레시피를 검색합니다.
        recipe-ai-project와 호환되는 script_score 방식으로 수정
        """
        try:
            # 여러 재료의 평균 임베딩 계산
            if len(ingredient_embeddings) > 1:
                import numpy as np
                combined_embedding = np.mean(ingredient_embeddings, axis=0)
                # 벡터 정규화 (recipe-ai-project와 동일)
                normalized_vector = combined_embedding / np.linalg.norm(combined_embedding)
            else:
                import numpy as np
                normalized_vector = np.array(ingredient_embeddings[0])
                normalized_vector = normalized_vector / np.linalg.norm(normalized_vector)

            # script_score 쿼리 사용 (recipe-ai-project와 동일)
            query = {
                "size": limit,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, doc['embedding']) + 1.0",
                            "params": {"query_vector": list(map(float, normalized_vector))}
                        }
                    }
                },
                "_source": {
                    "excludes": ["embedding"]  # 응답에서 임베딩 제외 (크기 절약)
                }
            }
            
            response = self.client.search(
                index=self.recipes_index,
                body=query
            )
            
            return self._parse_search_results(response)
            
        except Exception as e:
            logger.error(f"Error in search_recipes_by_ingredients (script_score): {str(e)}")
            # 백업: 텍스트 검색으로 대체
            logger.info("텍스트 검색으로 대체 시도...")
            return await self.search_recipes_by_text("재료", limit)

    async def search_ingredients_by_text(
        self,
        query_text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        텍스트로 재료를 검색합니다.
        """
        try:
            query = {
                "size": limit,
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["name^3", "aliases^2"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "_source": {
                    "excludes": ["embedding"]
                }
            }
            
            response = self.client.search(
                index=self.ingredients_index,
                body=query
            )
            
            return self._parse_search_results(response)
            
        except Exception as e:
            logger.error(f"Error in search_ingredients_by_text: {str(e)}")
            raise

    async def vector_search_ingredients(
        self,
        vector: List[float],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        재료에 대한 벡터 검색 수행 - script_score 쿼리 사용
        """
        try:
            import numpy as np
            # 벡터 정규화 (recipe-ai-project와 동일)
            normalized_vector = np.array(vector) / np.linalg.norm(vector)
            
            # script_score 쿼리 사용 (recipe-ai-project와 동일)
            query = {
                "size": limit,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, doc['embedding']) + 1.0",
                            "params": {"query_vector": list(map(float, normalized_vector))}
                        }
                    }
                },
                "_source": {
                    "excludes": ["embedding"]
                }
            }
            
            response = self.client.search(
                index=self.ingredients_index,
                body=query
            )
            
            return self._parse_search_results(response)
            
        except Exception as e:
            logger.error(f"Error in vector_search_ingredients (script_score): {str(e)}")
            # 백업: 텍스트 검색으로 대체
            return await self.search_ingredients_by_text("재료", limit)

    async def search_recipes_by_text(
        self,
        query_text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        텍스트로 레시피를 검색합니다.
        """
        try:
            query = {
                "size": limit,
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["name^3", "ingredients^2", "hashtag"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "_source": {
                    "excludes": ["embedding"]
                }
            }
            
            response = self.client.search(
                index=self.recipes_index,
                body=query
            )
            
            return self._parse_search_results(response)
            
        except Exception as e:
            logger.error(f"Error in search_recipes_by_text: {str(e)}")
            raise

    async def search_recipes_by_category(
        self,
        category: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        카테고리로 레시피 검색
        """
        try:
            query = {
                "size": limit,
                "query": {
                    "term": {
                        "category": category
                    }
                },
                "_source": {
                    "excludes": ["embedding"]
                }
            }
            
            response = self.client.search(
                index=self.recipes_index,
                body=query
            )
            
            return self._parse_search_results(response)
            
        except Exception as e:
            logger.error(f"Error in search_recipes_by_category: {str(e)}")
            raise

    async def get_recipe_by_id(self, recipe_id: str) -> Dict[str, Any]:
        """
        레시피 ID로 특정 레시피를 조회합니다.
        """
        try:
            response = self.client.get(
                index=self.recipes_index,
                id=recipe_id,
                _source_excludes=["embedding"]
            )
            return response["_source"]
        except Exception as e:
            logger.error(f"Error in get_recipe_by_id: {str(e)}")
            return None

    async def get_ingredient_by_id(self, ingredient_id: int) -> Dict[str, Any]:
        """
        재료 ID로 특정 재료를 조회합니다.
        """
        try:
            response = self.client.get(
                index=self.ingredients_index,
                id=str(ingredient_id),
                _source_excludes=["embedding"]
            )
            return response["_source"]
        except Exception as e:
            logger.error(f"Error in get_ingredient_by_id: {str(e)}")
            return None

    async def get_stats(self) -> Dict[str, Any]:
        """
        인덱스 통계 정보 조회
        """
        try:
            recipe_count = self.client.count(index=self.recipes_index)["count"]
            ingredient_count = self.client.count(index=self.ingredients_index)["count"]
            
            return {
                "recipes_count": recipe_count,
                "ingredients_count": ingredient_count,
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"Error in get_stats: {str(e)}")
            return {
                "recipes_count": 0,
                "ingredients_count": 0,
                "status": "error",
                "error": str(e)
            }

    def _parse_search_results(
        self,
        response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        검색 결과를 파싱합니다.
        """
        results = []
        for hit in response["hits"]["hits"]:
            result = hit["_source"]
            result["score"] = hit["_score"]
            # ID 정보 추가
            result["_id"] = hit["_id"]
            results.append(result)
        return results

    async def search(self, index: str, body: dict) -> Dict[str, Any]:
        """
        일반적인 OpenSearch 검색 메서드 - 개선된 오류 처리
        """
        try:
            # body에서 _source 필드 검증 및 수정
            if "_source" in body:
                # _source가 dict인 경우
                if isinstance(body["_source"], dict):
                    # excludes 또는 includes만 허용
                    if "excludes" not in body["_source"] and "includes" not in body["_source"]:
                        # 잘못된 _source 구조면 기본값으로 설정
                        body["_source"] = {"excludes": ["embedding"]}
                # _source가 list인 경우는 유지
                elif not isinstance(body["_source"], list):
                    # 잘못된 타입이면 기본값으로 설정
                    body["_source"] = {"excludes": ["embedding"]}
            
            # OpenSearch 검색 실행
            response = self.client.search(index=index, body=body)
            return response
            
        except Exception as e:
            logger.error(f"OpenSearch 검색 오류 (인덱스: {index}): {str(e)}")
            logger.error(f"검색 쿼리: {body}")
            
            # 빈 결과 반환
            return {
                "hits": {
                    "hits": [],
                    "total": {"value": 0}
                }
            }

    def close(self):
        """
        OpenSearch 클라이언트 연결을 종료합니다.
        """
        try:
            if hasattr(self.client, 'close'):
                self.client.close()
                logger.info("OpenSearch 클라이언트 연결 종료")
        except Exception as e:
            logger.error(f"OpenSearch 클라이언트 종료 중 오류: {str(e)}")

# 싱글톤 인스턴스
opensearch_client = OpenSearchClient()