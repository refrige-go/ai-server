from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..models.schemas import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    RecipeSearchResult,
    IngredientSearchResult
)
# script_score 전용 서비스 사용
from app.services.enhanced_search_service_script import EnhancedSearchService
from app.clients.opensearch_client import opensearch_client
from app.clients.openai_client import openai_client

router = APIRouter()

@router.get("/search/test")
async def test_search():
    """
    기본적인 OpenSearch 연결 테스트
    """
    try:
        # 간단한 텍스트 검색으로 테스트
        search_body = {
            "size": 5,
            "query": {
                "match_all": {}
            }
        }
        
        # 레시피 검색 테스트
        recipe_response = await opensearch_client.search(
            index="recipes",
            body=search_body
        )
        
        # 재료 검색 테스트
        ingredient_response = await opensearch_client.search(
            index="ingredients", 
            body=search_body
        )
        
        return {
            "status": "success",
            "recipe_count": len(recipe_response["hits"]["hits"]),
            "ingredient_count": len(ingredient_response["hits"]["hits"]),
            "sample_recipes": [hit["_source"] for hit in recipe_response["hits"]["hits"][:2]],
            "sample_ingredients": [hit["_source"] for hit in ingredient_response["hits"]["hits"][:2]]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.post("/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    """
    시맨틱 검색 API - script_score 벡터 검색 사용
    
    - 레시피와 식재료를 동시에 검색
    - 검색어의 의미를 이해하여 관련성 높은 결과 반환
    - 검색 결과는 관련성 점수로 정렬
    """
    try:
        # 입력 검증
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="검색어가 필요합니다")
        
        search_service = EnhancedSearchService()
        results = await search_service.semantic_search(
            query=request.query.strip(),
            search_type=request.search_type,
            limit=request.limit
        )
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"시맨틱 검색 오류: {str(e)}"
        print(f"Semantic search error: {error_detail}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)

@router.get("/search/recipes")
async def search_recipes(
    query: str = Query(..., description="검색할 레시피명 또는 키워드"),
    limit: int = Query(10, ge=1, le=50, description="반환할 결과 수")
):
    """
    레시피 텍스트 검색 API
    
    - 레시피명, 재료, 카테고리로 검색
    - 텍스트 매칭 기반 검색
    """
    try:
        # 호환성을 위한 다중 필드 검색
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"name": {"query": query, "boost": 3}}},
                        {"match": {"ingredients": {"query": query, "boost": 2}}},
                        {"match": {"category": {"query": query, "boost": 1}}},
                        {"match": {"cooking_method": {"query": query, "boost": 1}}}
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": limit
        }
        
        response = await opensearch_client.search(
            index="recipes",
            body=search_body
        )
        
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            results.append({
                "rcp_seq": str(source.get("recipe_id", "")),
                "name": source.get("name", ""),
                "category": source.get("category", ""),
                "cooking_method": source.get("cooking_method", ""),
                "ingredients": str(source.get("ingredients", "")),
                "score": hit["_score"]
            })
        
        return {
            "query": query,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"레시피 검색 오류: {str(e)}")

@router.get("/search/ingredients")
async def search_ingredients(
    query: str = Query(..., description="검색할 재료명"),
    limit: int = Query(10, ge=1, le=50, description="반환할 결과 수")
):
    """
    재료 텍스트 검색 API
    
    - 재료명, 카테고리로 검색
    - 동의어 매칭 포함
    """
    try:
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"name": {"query": query, "boost": 3}}},
                        {"match": {"category": {"query": query, "boost": 1}}},
                        {"match": {"aliases": {"query": query, "boost": 2}}}
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": limit
        }
        
        response = await opensearch_client.search(
            index="ingredients",
            body=search_body
        )
        
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            results.append({
                "ingredient_id": source.get("ingredient_id", 0),
                "name": source.get("name", ""),
                "category": source.get("category", ""),
                "score": hit["_score"]
            })
        
        return {
            "query": query,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"재료 검색 오류: {str(e)}")

@router.post("/search/vector")
async def vector_search(
    request: dict
):
    """
    벡터 유사도 검색 API - Java 백엔드 완전 호환 (안전한 파싱)
    
    - OpenAI 임베딩을 사용한 의미 기반 검색
    - test_vector_search_fixed.py와 동일한 script_score 방식 사용
    - Java RecipeSearchResultDTO 형식 완전 호환
    """
    try:
        query = request.get("query", "")
        limit = request.get("limit", 10)
        
        print(f"벡터 검색 요청: query='{query}', limit={limit}")
        
        if not query:
            return {
                "query": "",
                "results": [],
                "total": 0,
                "searchMethod": "no_query"
            }
        
        # OpenAI로 쿼리 임베딩 생성
        try:
            print("OpenAI 임베딩 생성 중...")
            query_embedding = await openai_client.get_embedding(query)
            print(f"임베딩 생성 완료: {len(query_embedding)}차원")
        except Exception as e:
            print(f"OpenAI API 오류: {e}")
            return {
                "query": query,
                "results": [],
                "total": 0,
                "searchMethod": "openai_error"
            }
        
        # script_score 방식으로 벡터 검색
        try:
            print("벡터 검색 실행 중...")
            vector_results = await opensearch_client.search_recipes_by_ingredients(
                [query_embedding], 
                limit
            )
            print(f"벡터 검색 완료: {len(vector_results)}개 결과")
            
            if not vector_results:
                print("벡터 검색 결과 없음")
                return {
                    "query": query,
                    "results": [],
                    "total": 0,
                    "searchMethod": "no_results"
                }
            
            results = []
            for i, result in enumerate(vector_results):
                try:
                    print(f"결과 {i+1} 처리 중: {result.get('name', 'N/A')}")
                    
                    # 기본값으로 안전하게 가져오기
                    recipe_id = str(result.get("recipe_id", ""))
                    name = str(result.get("name", ""))
                    category = str(result.get("category", ""))
                    cooking_method = str(result.get("cooking_method", ""))
                    score = float(result.get("score", 0.0))
                    ingredients_text = str(result.get("ingredients", ""))
                    
                    # ingredients를 RecipeIngredientDTO 리스트로 안전하게 변환
                    ingredient_dtos = []
                    if ingredients_text and ingredients_text.strip():
                        try:
                            ingredient_names = [name.strip() for name in ingredients_text.split(",")]
                            for idx, ingredient_name in enumerate(ingredient_names[:10]):  # 최대 10개
                                if ingredient_name:
                                    ingredient_dtos.append({
                                        "ingredient_id": int(idx + 1),  # Java에서 기대하는 필드명
                                        "name": str(ingredient_name).strip(),
                                        "is_main_ingredient": bool(idx < 3)  # Java에서 기대하는 필드명
                                    })
                        except Exception as ingredient_error:
                            print(f"재료 파싱 오류: {ingredient_error}")
                            ingredient_dtos = []
                    
                    # Java 백엔드 RecipeSearchResultDTO 형식
                    recipe_dto = {
                        "rcp_seq": recipe_id,  # Java에서 기대하는 필드명
                        "rcp_nm": name,  # Java에서 기대하는 필드명
                        "rcp_category": category,  # Java에서 기대하는 필드명
                        "rcp_way2": cooking_method,  # Java에서 기대하는 필드명
                        "score": score,
                        "match_reason": "벡터 유사도 검색",  # Java에서 기대하는 필드명
                        "ingredients": ingredient_dtos
                    }
                    
                    results.append(recipe_dto)
                    print(f"결과 {i+1} 변환 완료")
                    
                except Exception as result_error:
                    print(f"결과 {i+1} 처리 오류: {result_error}")
                    continue  # 이 결과는 건너뛰고 다음으로
            
            final_response = {
                "query": query,
                "results": results,
                "total": len(results),
                "searchMethod": "script_score"
            }
            
            print(f"최종 응답: {len(results)}개 결과")
            return final_response
            
        except Exception as search_error:
            print(f"벡터 검색 실패: {search_error}")
            import traceback
            print(f"상세 오류: {traceback.format_exc()}")
            return {
                "query": query,
                "results": [],
                "total": 0,
                "searchMethod": "search_error"
            }
        
    except Exception as e:
        print(f"벡터 검색 전체 오류: {e}")
        import traceback
        print(f"전체 오류 상세: {traceback.format_exc()}")
        return {
            "query": request.get("query", ""),
            "results": [],
            "total": 0,
            "searchMethod": "total_error"
        }
        
@router.get("/search/debug/{index_name}")
async def debug_index(index_name: str):
    """
    특정 인덱스 디버그 정보 조회
    """
    try:
        # 인덱스 존재 확인
        exists = opensearch_client.client.indices.exists(index=index_name)
        if not exists:
            return {"error": f"인덱스 '{index_name}'가 존재하지 않습니다"}
        
        # 매핑 정보
        mapping = opensearch_client.client.indices.get_mapping(index=index_name)
        
        # 문서 개수
        count = opensearch_client.client.count(index=index_name)
        
        # 샘플 문서
        sample = opensearch_client.client.search(
            index=index_name,
            body={"size": 2, "query": {"match_all": {}}}
        )
        
        return {
            "index": index_name,
            "exists": exists,
            "document_count": count["count"],
            "fields": list(mapping[index_name]["mappings"]["properties"].keys()),
            "sample_documents": [hit["_source"] for hit in sample["hits"]["hits"]]
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/search/test-vector")
async def test_vector_search():
    """
    벡터 검색 테스트 - test_vector_search_fixed.py 방식
    """
    try:
        # 1. 샘플 재료 임베딩 가져오기
        sample_ingredient = opensearch_client.client.search(
            index="ingredients",
            body={
                "size": 1,
                "query": {"exists": {"field": "embedding"}},
                "_source": ["ingredient_id", "name", "embedding"]
            }
        )
        
        if not sample_ingredient["hits"]["hits"]:
            return {"error": "임베딩이 있는 재료를 찾을 수 없습니다"}
        
        ingredient_doc = sample_ingredient["hits"]["hits"][0]["_source"]
        ingredient_name = ingredient_doc.get('name', 'N/A')
        ingredient_embedding = ingredient_doc.get('embedding', [])
        
        # 2. script_score 방식으로 레시피 검색
        vector_results = await opensearch_client.search_recipes_by_ingredients(
            [ingredient_embedding], 
            limit=5
        )
        
        # 3. 재료 벡터 검색
        ingredient_results = await opensearch_client.vector_search_ingredients(
            ingredient_embedding, 
            limit=5
        )
        
        return {
            "test_ingredient": ingredient_name,
            "embedding_dimension": len(ingredient_embedding),
            "recipe_results": len(vector_results),
            "ingredient_results": len(ingredient_results),
            "sample_recipes": [r.get("name", "") for r in vector_results[:3]],
            "sample_ingredients": [r.get("name", "") for r in ingredient_results[:3]],
            "status": "success"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

@router.get("/search/test-java-format")
async def test_java_format():
    """
    Java 백엔드 호환성 테스트 - 응답 형식 확인
    """
    try:
        # 김치찌개 텍스트 검색
        search_body = {
            "query": {
                "match": {"name": "김치찌개"}
            },
            "size": 3
        }
        
        response = await opensearch_client.search(
            index="recipes",
            body=search_body
        )
        
        # Java 백엔드 형식으로 변환
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            
            results.append({
                "recipe_id": str(source.get("recipe_id", "")),
                "name": source.get("name", ""),
                "category": source.get("category", ""),
                "ingredients": str(source.get("ingredients", "")),  # 반드시 String
                "score": hit["_score"],
                "cooking_method": source.get("cooking_method", "")
            })
        
        return {
            "query": "김치찌개",
            "results": results,
            "total": len(results),
            "search_method": "text_for_java_test"
        }
        
    except Exception as e:
        return {"error": str(e)}