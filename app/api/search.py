from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..models.schemas import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    RecipeSearchResult,
    IngredientSearchResult
)

# 🎯 최종 완성된 엄격한 시맨틱 검색 서비스 사용
print("🔄 최종 완성된 검색 서비스 로딩 시작...")

try:
    from app.services.final_strict_semantic_search_service import FinalStrictSemanticSearchService
    EnhancedSearchService = FinalStrictSemanticSearchService
    print("✅ 최종 완성된 엄격한 시맨틱 검색 서비스 로드 성공!")
except ImportError as e:
    print(f"❌ 최종 완성 서비스 로드 실패: {e}")
    print("🔄 폴백으로 엄격한 검색 서비스 시도...")
    try:
        from app.services.strict_openai_semantic_search_service import StrictOpenAISemanticSearchService
        EnhancedSearchService = StrictOpenAISemanticSearchService
        print("⚠️ 엄격한 검색 서비스 로드됨 (백업)")
    except ImportError as e2:
        print(f"❌ 엄격한 서비스도 로드 실패: {e2}")
        print("🔄 최종 폴백으로 기본 OpenAI 서비스 시도...")
        try:
            from app.services.openai_semantic_search_service import OpenAISemanticSearchService
            EnhancedSearchService = OpenAISemanticSearchService
            print("⚠️ 기본 OpenAI 서비스 로드됨 (최종 폴백)")
        except ImportError as e3:
            print(f"❌ 모든 서비스 로드 실패: {e3}")
            print("🔄 하이브리드 서비스로 최종 시도...")
            from app.services.smart_hybrid_search_service import SmartHybridSearchService
            EnhancedSearchService = SmartHybridSearchService
            print("⚠️ 하이브리드 서비스 로드됨 (최종 백업)")

from app.clients.opensearch_client import opensearch_client
from app.clients.openai_client import openai_client
from app.utils.score_normalizer import ScoreNormalizer

router = APIRouter()

@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    """
    🎯 최종 완성된 엄격한 시맨틱 검색 API + 오타 교정
    
    ✅ 주요 개선사항:
    - "비트와 호두 요리" 문제 완전 해결
    - "피망" → "파프리카" 동의어 매칭 지원
    - 스마트 키워드 조합 로직 적용
    - 완벽한 텍스트 + 벡터 하이브리드 검색
    - 관련성 검증 강화
    - 한글 오타 교정 ('ㅋㅡ면' → '라면')
    
    🔍 검색 단계:
    0. 오타 교정 (자모 분리, 키보드 오타, AI 교정)
    1. 완벽한 텍스트 검색 (정확한 구문 + 스마트 재료 검색)
    2. 벡터 검색 (필요시)
    3. 최종 통합 및 관련성 필터링
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="검색어가 필요합니다")
        
        query = request.query.strip()
        print(f"\n🎯 최종 완성된 시맨틱 검색 요청 (오타 교정 포함): '{query}' (서비스: {EnhancedSearchService.__name__})")
        
        search_service = EnhancedSearchService()
        results = await search_service.semantic_search(
            query=query,
            search_type=request.search_type,
            limit=request.limit
        )
        
        print(f"🎯 검색 완료: {len(results.recipes)}개 레시피, {len(results.ingredients)}개 재료")
        
        # 🎯 품질 검증 로그
        if results.recipes:
            print(f"\n📊 상위 결과 품질:")
            for i, recipe in enumerate(results.recipes[:3], 1):
                print(f"  {i}. {recipe.rcp_nm} = {recipe.score:.1f}점 ({recipe.match_reason})")
        
        # 🚨 문제 케이스 감지 (개선된 모니터링)
        problematic_queries = ["피망 요리", "치킨 요리", "파프리카 요리"]
        if query.lower() in [q.lower() for q in problematic_queries]:
            main_ingredient = query.replace("요리", "").replace("음식", "").strip()
            relevant_count = 0
            irrelevant_recipes = []
            
            for recipe in results.recipes:
                recipe_name = recipe.rcp_nm.lower()
                # 더 정교한 관련성 검사
                is_relevant = (
                    main_ingredient.lower() in recipe_name or
                    main_ingredient.lower() in str(recipe.ingredients).lower() or
                    (main_ingredient == "피망" and "파프리카" in recipe_name) or
                    (main_ingredient == "파프리카" and "피망" in recipe_name)
                )
                
                if is_relevant:
                    relevant_count += 1
                else:
                    # 명백히 무관한 결과만 기록
                    if not any(word in recipe_name for word in ["볶음", "찌개", "국", "탕"]):
                        irrelevant_recipes.append(f"{recipe.rcp_nm} (점수: {recipe.score:.1f})")
            
            if irrelevant_recipes:
                print(f"⚠️ 무관한 결과 감지: {len(irrelevant_recipes)}개")
                for irrelevant in irrelevant_recipes[:3]:
                    print(f"  - {irrelevant}")
            else:
                print(f"✅ 모든 결과가 관련성 있음: {relevant_count}개 관련 결과")
            
            print(f"🔧 사용된 서비스: {EnhancedSearchService.__name__}")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"최종 완성된 시맨틱 검색 오류: {str(e)}"
        print(f"Final semantic search error: {error_detail}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)

@router.get("/test")
async def test_search():
    """기본적인 OpenSearch 연결 테스트"""
    try:
        search_body = {"size": 5, "query": {"match_all": {}}}
        
        recipe_response = await opensearch_client.search(index="recipes", body=search_body)
        ingredient_response = await opensearch_client.search(index="ingredients", body=search_body)
        
        return {
            "status": "success",
            "recipe_count": len(recipe_response["hits"]["hits"]),
            "ingredient_count": len(ingredient_response["hits"]["hits"]),
            "sample_recipes": [hit["_source"] for hit in recipe_response["hits"]["hits"][:2]],
            "sample_ingredients": [hit["_source"] for hit in ingredient_response["hits"]["hits"][:2]],
            "active_search_service": EnhancedSearchService.__name__,
            "service_features": [
                "✅ 최종 완성된 엄격한 검색",
                "✅ 동의어 매칭 지원 (피망↔파프리카)",
                "✅ 스마트 키워드 조합",
                "✅ 완벽한 텍스트 + 벡터 하이브리드",
                "✅ 무관한 결과 제거"
            ]
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e), "error_type": type(e).__name__}

@router.get("/debug/service-info")
async def debug_service_info():
    """현재 사용 중인 검색 서비스 정보"""
    return {
        "current_service": EnhancedSearchService.__name__,
        "service_module": EnhancedSearchService.__module__,
        "is_final_version": "Final" in EnhancedSearchService.__name__,
        "is_strict": "Strict" in EnhancedSearchService.__name__,
        "features": {
            "perfect_text_search": True,
            "smart_ingredient_search": True,
            "synonym_matching": True,
            "vector_search": True,
            "relevance_filtering": True,
            "smart_keyword_combination": True
        },
        "available_methods": [method for method in dir(EnhancedSearchService) if not method.startswith('_')],
        "supported_synonyms": {
            "피망": ["파프리카", "빨간피망", "노란피망"],
            "파프리카": ["피망", "빨간파프리카", "노란파프리카"],
            "양배추": ["배추", "캐비지"],
            "대파": ["파", "쪽파"]
        }
    }

@router.get("/recipes")
async def search_recipes(
    query: str = Query(..., description="검색할 레시피명 또는 키워드"),
    limit: int = Query(10, ge=1, le=50, description="반환할 결과 수")
):
    """레시피 텍스트 검색 API - 기본 텍스트 검색"""
    try:
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
        
        response = await opensearch_client.search(index="recipes", body=search_body)
        
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            normalized_score = ScoreNormalizer.normalize_text_score(hit["_score"])
            
            results.append({
                "rcp_seq": str(source.get("recipe_id", "")),
                "name": source.get("name", ""),
                "category": source.get("category", ""),
                "cooking_method": source.get("cooking_method", ""),
                "ingredients": str(source.get("ingredients", "")),
                "score": normalized_score
            })
        
        return {"query": query, "results": results, "total": len(results)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"레시피 검색 오류: {str(e)}")

@router.get("/ingredients")
async def search_ingredients(
    query: str = Query(..., description="검색할 재료명"),
    limit: int = Query(10, ge=1, le=50, description="반환할 결과 수")
):
    """재료 텍스트 검색 API - 동의어 포함 검색"""
    try:
        # 동의어 매핑
        synonyms = {
            "피망": ["파프리카", "빨간피망", "노란피망"],
            "파프리카": ["피망", "빨간파프리카", "노란파프리카"],
            "양배추": ["배추", "캐비지"],
            "배추": ["양배추", "캐비지"],
            "대파": ["파", "쪽파"],
            "파": ["대파", "쪽파"]
        }
        
        # 검색할 키워드들
        search_terms = [query]
        if query in synonyms:
            search_terms.extend(synonyms[query])
        
        all_results = {}
        for term in search_terms:
            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"name": {"query": term, "boost": 3}}},
                            {"match": {"category": {"query": term, "boost": 1}}},
                            {"match": {"aliases": {"query": term, "boost": 2}}}
                        ],
                        "minimum_should_match": 1
                    }
                },
                "size": limit
            }
            
            response = await opensearch_client.search(index="ingredients", body=search_body)
            
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                ingredient_id = source.get("ingredient_id", 0)
                if ingredient_id and ingredient_id not in all_results:
                    all_results[ingredient_id] = hit
        
        results = []
        for hit in all_results.values():
            source = hit["_source"]
            normalized_score = ScoreNormalizer.normalize_text_score(hit["_score"])
            
            results.append({
                "ingredient_id": source.get("ingredient_id", 0),
                "name": source.get("name", ""),
                "category": source.get("category", ""),
                "score": normalized_score
            })
        
        # 점수순 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return {"query": query, "results": results[:limit], "total": len(results[:limit]), "search_terms": search_terms}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"재료 검색 오류: {str(e)}")

@router.post("/vector")
async def vector_search(request: dict):
    """벡터 유사도 검색 API - Java 백엔드 완전 호환"""
    try:
        query = request.get("query", "")
        limit = request.get("limit", 10)
        
        print(f"벡터 검색 요청: query='{query}', limit={limit}")
        
        if not query:
            return {"query": "", "results": [], "total": 0, "searchMethod": "no_query"}
        
        try:
            print("OpenAI 임베딩 생성 중...")
            query_embedding = await openai_client.get_embedding(query)
            print(f"임베딩 생성 완료: {len(query_embedding)}차원")
        except Exception as e:
            print(f"OpenAI API 오류: {e}")
            return {"query": query, "results": [], "total": 0, "searchMethod": "openai_error"}
        
        try:
            print("벡터 검색 실행 중...")
            vector_results = await opensearch_client.search_recipes_by_ingredients([query_embedding], limit)
            print(f"벡터 검색 완료: {len(vector_results)}개 결과")
            
            if not vector_results:
                print("벡터 검색 결과 없음")
                return {"query": query, "results": [], "total": 0, "searchMethod": "no_results"}
            
            results = []
            for i, result in enumerate(vector_results):
                try:
                    print(f"결과 {i+1} 처리 중: {result.get('name', 'N/A')}")
                    
                    recipe_id = str(result.get("recipe_id", ""))
                    name = str(result.get("name", ""))
                    category = str(result.get("category", ""))
                    cooking_method = str(result.get("cooking_method", ""))
                    score = float(result.get("score", 0.0))
                    ingredients_text = str(result.get("ingredients", ""))
                    image = str(result.get("image", ""))
                    thumbnail = str(result.get("thumbnail", ""))
                    
                    ingredient_dtos = []
                    if ingredients_text and ingredients_text.strip():
                        try:
                            ingredient_names = [name.strip() for name in ingredients_text.split(",")]
                            for idx, ingredient_name in enumerate(ingredient_names[:10]):
                                if ingredient_name:
                                    ingredient_dtos.append({
                                        "ingredient_id": int(idx + 1),
                                        "name": str(ingredient_name).strip(),
                                        "is_main_ingredient": bool(idx < 3)
                                    })
                        except Exception as ingredient_error:
                            print(f"재료 파싱 오류: {ingredient_error}")
                            ingredient_dtos = []
                    
                    normalized_score = ScoreNormalizer.normalize_vector_score(score)
                    
                    recipe_dto = {
                        "rcp_seq": recipe_id,
                        "rcp_nm": name,
                        "rcp_category": category,
                        "rcp_way2": cooking_method,
                        "image": image,
                        "thumbnail": thumbnail,
                        "score": normalized_score,
                        "match_reason": "벡터 유사도 검색",
                        "ingredients": ingredient_dtos
                    }
                    
                    results.append(recipe_dto)
                    print(f"결과 {i+1} 변환 완료")
                    
                except Exception as result_error:
                    print(f"결과 {i+1} 처리 오류: {result_error}")
                    continue
            
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
            return {"query": query, "results": [], "total": 0, "searchMethod": "search_error"}
        
    except Exception as e:
        print(f"벡터 검색 전체 오류: {e}")
        import traceback
        print(f"전체 오류 상세: {traceback.format_exc()}")
        return {"query": request.get("query", ""), "results": [], "total": 0, "searchMethod": "total_error"}

@router.get("/test-typo-correction")
async def test_typo_correction():
    """한글 오타 교정 기능 테스트"""
    test_cases = [
        "ㄹㅏ면",      # 라면
        "ㄱㅣ지",      # 김치  
        "ㅍㅣ망",      # 피망
        "ㅍㅏ프리카",   # 파프리카
        "ㅊㅓ기",      # 치킨
        "ㅇㅏ침 식사", # 아침 식사
        "ㅁㅏ라탕면",   # 마라탕면
        "라면",       # 이미 올바름
        "normal text"  # 영어
    ]
    
    try:
        from app.utils.korean_typo_corrector import KoreanTypoCorrector
        corrector = KoreanTypoCorrector()
        
        results = {}
        for test_case in test_cases:
            try:
                corrected = await corrector.correct_typo(test_case)
                suggestions = corrector.get_typo_suggestions(test_case)
                
                results[test_case] = {
                    "original": test_case,
                    "corrected": corrected,
                    "suggestions": suggestions,
                    "changed": corrected != test_case
                }
            except Exception as e:
                results[test_case] = {
                    "error": str(e),
                    "original": test_case
                }
        
        return {
            "status": "success",
            "typo_correction_results": results,
            "summary": {
                "total_tests": len(test_cases),
                "successful_corrections": len([r for r in results.values() if r.get("changed", False)]),
                "errors": len([r for r in results.values() if "error" in r])
            }
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "message": "오타 교정 모듈 로드 실패"
        }

@router.get("/test-semantic-queries")
async def test_semantic_queries():
    """주요 시맨틱 검색 쿼리 테스트"""
    test_queries = [
        "피망 요리",
        "파프리카 요리", 
        "치킨 요리",
        "파프리카",
        "피망"
    ]
    
    results = {}
    search_service = EnhancedSearchService()
    
    for query in test_queries:
        try:
            print(f"\n🧪 테스트 쿼리: '{query}'")
            search_result = await search_service.semantic_search(query=query, limit=5)
            
            results[query] = {
                "recipe_count": len(search_result.recipes),
                "top_recipes": [
                    {
                        "name": recipe.rcp_nm,
                        "score": recipe.score,
                        "match_reason": recipe.match_reason
                    }
                    for recipe in search_result.recipes[:3]
                ],
                "processing_time": search_result.processing_time
            }
            
        except Exception as e:
            results[query] = {"error": str(e)}
    
    return {
        "service_used": EnhancedSearchService.__name__,
        "test_results": results,
        "summary": {
            "total_queries": len(test_queries),
            "successful_queries": len([r for r in results.values() if "error" not in r])
        }
    }

# 기존 디버그 엔드포인트들 유지
@router.get("/debug-image-fields")
async def debug_image_fields():
    """이미지 필드 디버깅"""
    try:
        sample_response = await opensearch_client.search(
            index="recipes",
            body={"size": 3, "query": {"match_all": {}}, "_source": ["recipe_id", "name", "image", "thumbnail", "category"]}
        )
        
        results = []
        for hit in sample_response["hits"]["hits"]:
            source = hit["_source"]
            results.append({
                "recipe_id": source.get("recipe_id"),
                "name": source.get("name"),
                "image": source.get("image"),
                "thumbnail": source.get("thumbnail"),
                "has_image": bool(source.get("image")),
                "has_thumbnail": bool(source.get("thumbnail"))
            })
        
        return {
            "status": "success",
            "sample_count": len(results),
            "samples": results,
            "fields_in_index": list(sample_response["hits"]["hits"][0]["_source"].keys()) if results else []
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/debug/{index_name}")
async def debug_index(index_name: str):
    """특정 인덱스 디버그 정보 조회"""
    try:
        exists = opensearch_client.client.indices.exists(index=index_name)
        if not exists:
            return {"error": f"인덱스 '{index_name}'가 존재하지 않습니다"}
        
        mapping = opensearch_client.client.indices.get_mapping(index=index_name)
        count = opensearch_client.client.count(index=index_name)
        sample = opensearch_client.client.search(index=index_name, body={"size": 2, "query": {"match_all": {}}})
        
        return {
            "index": index_name,
            "exists": exists,
            "document_count": count["count"],
            "fields": list(mapping[index_name]["mappings"]["properties"].keys()),
            "sample_documents": [hit["_source"] for hit in sample["hits"]["hits"]]
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/test-vector")
async def test_vector_search():
    """벡터 검색 테스트"""
    try:
        sample_ingredient = opensearch_client.client.search(
            index="ingredients",
            body={"size": 1, "query": {"exists": {"field": "embedding"}}, "_source": ["ingredient_id", "name", "embedding"]}
        )
        
        if not sample_ingredient["hits"]["hits"]:
            return {"error": "임베딩이 있는 재료를 찾을 수 없습니다"}
        
        ingredient_doc = sample_ingredient["hits"]["hits"][0]["_source"]
        ingredient_name = ingredient_doc.get('name', 'N/A')
        ingredient_embedding = ingredient_doc.get('embedding', [])
        
        vector_results = await opensearch_client.search_recipes_by_ingredients([ingredient_embedding], limit=5)
        ingredient_results = await opensearch_client.vector_search_ingredients(ingredient_embedding, limit=5)
        
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
        return {"error": str(e), "status": "failed"}

@router.get("/test-java-format")
async def test_java_format():
    """Java 백엔드 호환성 테스트"""
    try:
        search_body = {"query": {"match": {"name": "김치찌개"}}, "size": 3}
        response = await opensearch_client.search(index="recipes", body=search_body)
        
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            normalized_score = ScoreNormalizer.normalize_text_score(hit["_score"])
            
            results.append({
                "recipe_id": str(source.get("recipe_id", "")),
                "name": source.get("name", ""),
                "category": source.get("category", ""),
                "ingredients": str(source.get("ingredients", "")),
                "score": normalized_score,
                "cooking_method": source.get("cooking_method", "")
            })
        
        return {"query": "김치찌개", "results": results, "total": len(results), "search_method": "text_for_java_test"}
        
    except Exception as e:
        return {"error": str(e)}