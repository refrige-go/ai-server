"""
OpenSearch 클라이언트

AWS OpenSearch와의 통신을 담당합니다.
업로드된 knn_vector 데이터와 호환되도록 구현되었습니다.
"""

from opensearchpy import OpenSearch
from app.config.settings import get_settings
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class OpenSearchClient:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenSearch(
            hosts=[{'host': self.settings.opensearch_host, 'port': 443}],
            http_auth=(
                self.settings.opensearch_username,
                self.settings.opensearch_password
            ),
            use_ssl=True,
            verify_certs=True,
            ssl_show_warn=False,
            timeout=60,
            max_retries=10,
            retry_on_timeout=True
        )
        # 업로드된 인덱스명과 일치
        self.recipes_index = "recipes"
        self.ingredients_index = "ingredients"

    async def search_recipes_by_ingredients(
        self,
        ingredient_embeddings: List[List[float]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        재료 임베딩을 기반으로 레시피를 검색합니다.
        """
        try:
            # 여러 재료의 평균 임베딩 계산
            if len(ingredient_embeddings) > 1:
                import numpy as np
                combined_embedding = np.mean(ingredient_embeddings, axis=0).tolist()
            else:
                combined_embedding = ingredient_embeddings[0]

            # kNN 벡터 검색 쿼리 (업로드된 데이터 형식에 맞음)
            query = {
                "size": limit,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": combined_embedding,
                            "k": limit
                        }
                    }
                }
            }
            
            response = self.client.search(
                index=self.recipes_index,
                body=query
            )
            
            return self._parse_search_results(response)
            
        except Exception as e:
            logger.error(f"Error in search_recipes_by_ingredients: {str(e)}")
            raise

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
                        "fields": ["name^2", "aliases"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
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

    async def vector_search(
        self,
        index: str,
        vector: List[float],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        벡터 검색 수행 (kNN 방식)
        """
        try:
            query = {
                "size": limit,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": vector,
                            "k": limit
                        }
                    }
                }
            }
            
            response = self.client.search(
                index=index,
                body=query
            )
            
            return response["hits"]["hits"]
            
        except Exception as e:
            logger.error(f"Error in vector_search: {str(e)}")
            raise

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
            results.append(result)
        return results

    async def get_recipe_by_id(self, recipe_id: str) -> Dict[str, Any]:
        """
        레시피 ID로 특정 레시피를 조회합니다.
        """
        try:
            response = self.client.get(
                index=self.recipes_index,
                id=recipe_id
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
                id=str(ingredient_id)
            )
            return response["_source"]
        except Exception as e:
            logger.error(f"Error in get_ingredient_by_id: {str(e)}")
            return None

    def close(self):
        """
        OpenSearch 클라이언트 연결을 종료합니다.
        """
        if hasattr(self.client, 'close'):
            self.client.close()