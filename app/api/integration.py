"""
recipe-ai-project 통합 API 엔드포인트

recipe-ai-project의 OpenSearch와 연동하여 레시피 추천과 재료 검색 기능을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from app.clients.opensearch_client import opensearch_client
from app.clients.openai_client import OpenAIClient
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# 요청/응답 모델
class IngredientSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10

class RecipeSearchRequest(BaseModel):
    ingredients: List[str]
    limit: Optional[int] = 10
    method: Optional[str] = "vector"  # "vector" or "text"

class VectorSearchResponse(BaseModel):
    results: List[dict]
    total: int
    method: str
    processing_time: float

@router.get("/recipes/search/text")
async def search_recipes_by_text(
    q: str = Query(..., description="검색할 텍스트"),
    limit: int = Query(10, description="결과 개수")
):
    """
    텍스트로 레시피 검색 (한국어 지원)
    """
    try:
        results = await opensearch_client.search_recipes_by_text(q, limit)
        
        return {
            "query": q,
            "results": results,
            "total": len(results),
            "method": "text_search"
        }
        
    except Exception as e:
        logger.error(f"Error in search_recipes_by_text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ingredients/search/text")
async def search_ingredients_by_text(
    q: str = Query(..., description="검색할 재료명"),
    limit: int = Query(10, description="결과 개수")
):
    """
    텍스트로 재료 검색 (동의어 지원)
    """
    try:
        results = await opensearch_client.search_ingredients_by_text(q, limit)
        
        return {
            "query": q,
            "results": results,
            "total": len(results),
            "method": "text_search"
        }
        
    except Exception as e:
        logger.error(f"Error in search_ingredients_by_text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recipes/recommend/vector")
async def recommend_recipes_by_vector(request: RecipeSearchRequest):
    """
    벡터 검색을 통한 레시피 추천
    사용자의 재료를 임베딩으로 변환하여 유사한 레시피를 찾습니다.
    """
    import time
    start_time = time.time()
    
    try:
        # OpenAI로 재료 임베딩 생성
        openai_client = OpenAIClient()
        
        # 재료 텍스트 조합
        ingredients_text = ", ".join(request.ingredients)
        
        # 임베딩 생성
        embeddings = await openai_client.get_embeddings([ingredients_text])
        user_embedding = embeddings[0]
        
        # OpenSearch에서 벡터 검색
        results = await opensearch_client.search_recipes_by_ingredients(
            [user_embedding], 
            request.limit
        )
        
        processing_time = time.time() - start_time
        
        return VectorSearchResponse(
            results=results,
            total=len(results),
            method="vector_search",
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in recommend_recipes_by_vector: {str(e)}")
        
        # 백업: 텍스트 검색으로 대체
        try:
            logger.info("벡터 검색 실패, 텍스트 검색으로 대체...")
            
            search_query = " ".join(request.ingredients)
            results = await opensearch_client.search_recipes_by_text(
                search_query, 
                request.limit
            )
            
            processing_time = time.time() - start_time
            
            return VectorSearchResponse(
                results=results,
                total=len(results),
                method="text_search_fallback",
                processing_time=processing_time
            )
            
        except Exception as backup_error:
            logger.error(f"Backup search also failed: {str(backup_error)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Both vector and text search failed: {str(e)}"
            )

@router.post("/ingredients/search/vector")
async def search_ingredients_by_vector(
    query: str = Query(..., description="검색할 재료명"),
    limit: int = Query(10, description="결과 개수")
):
    """
    벡터 검색을 통한 재료 검색
    """
    import time
    start_time = time.time()
    
    try:
        # OpenAI로 쿼리 임베딩 생성
        openai_client = OpenAIClient()
        embeddings = await openai_client.get_embeddings([query])
        query_embedding = embeddings[0]
        
        # OpenSearch에서 벡터 검색
        results = await opensearch_client.vector_search_ingredients(
            query_embedding, 
            limit
        )
        
        processing_time = time.time() - start_time
        
        return VectorSearchResponse(
            results=results,
            total=len(results),
            method="vector_search",
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in search_ingredients_by_vector: {str(e)}")
        
        # 백업: 텍스트 검색으로 대체
        try:
            results = await opensearch_client.search_ingredients_by_text(query, limit)
            processing_time = time.time() - start_time
            
            return VectorSearchResponse(
                results=results,
                total=len(results),
                method="text_search_fallback",
                processing_time=processing_time
            )
            
        except Exception as backup_error:
            logger.error(f"Backup search also failed: {str(backup_error)}")
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/recipes/{recipe_id}")
async def get_recipe_by_id(recipe_id: str):
    """
    레시피 ID로 특정 레시피 상세 조회
    """
    try:
        recipe = await opensearch_client.get_recipe_by_id(recipe_id)
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
            
        return {
            "recipe": recipe,
            "recipe_id": recipe_id
        }
        
    except Exception as e:
        logger.error(f"Error in get_recipe_by_id: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ingredients/{ingredient_id}")
async def get_ingredient_by_id(ingredient_id: int):
    """
    재료 ID로 특정 재료 상세 조회
    """
    try:
        ingredient = await opensearch_client.get_ingredient_by_id(ingredient_id)
        
        if not ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found")
            
        return {
            "ingredient": ingredient,
            "ingredient_id": ingredient_id
        }
        
    except Exception as e:
        logger.error(f"Error in get_ingredient_by_id: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_database_stats():
    """
    데이터베이스 통계 정보 조회
    """
    try:
        stats = await opensearch_client.get_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error in get_database_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test/connection")
async def test_opensearch_connection():
    """
    OpenSearch 연결 테스트
    """
    try:
        connection_ok = await opensearch_client.test_connection()
        stats = await opensearch_client.get_stats() if connection_ok else {}
        
        return {
            "connected": connection_ok,
            "stats": stats,
            "message": "OpenSearch connection successful" if connection_ok else "OpenSearch connection failed"
        }
        
    except Exception as e:
        logger.error(f"Error in test_opensearch_connection: {str(e)}")
        return {
            "connected": False,
            "error": str(e),
            "message": "OpenSearch connection test failed"
        }
