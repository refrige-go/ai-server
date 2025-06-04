from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.utils.korean_spell_checker import spell_checker

router = APIRouter()

class SpellCheckRequest(BaseModel):
    query: str

class SpellCheckResponse(BaseModel):
    original: str
    corrected: str
    is_corrected: bool
    suggestions: Optional[List[str]] = None

@router.post("/spell-check", response_model=SpellCheckResponse)
async def correct_spelling(request: SpellCheckRequest):
    """
    한글 오타 교정 API
    
    - 자모 분리 오타 교정: 'ㄹㅏ면' → '라면'
    - OpenSearch 기반 유사 단어 검색
    - 퍼지 매칭으로 오타 허용
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="검색어가 필요합니다")
        
        original_query = request.query.strip()
        print(f"🔧 오타 교정 요청: '{original_query}'")
        
        # 오타 교정 실행
        corrected_query = await spell_checker.correct_typo(original_query)
        
        # 교정 후보들 생성
        suggestions = spell_checker.get_typo_suggestions(original_query)
        
        is_corrected = corrected_query != original_query
        
        if is_corrected:
            print(f"✅ 오타 교정 완료: '{original_query}' → '{corrected_query}'")
        else:
            print(f"ℹ️ 오타 교정 불필요: '{original_query}'")
        
        return SpellCheckResponse(
            original=original_query,
            corrected=corrected_query,
            is_corrected=is_corrected,
            suggestions=suggestions if suggestions else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 오타 교정 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"오타 교정 오류: {str(e)}")

@router.post("/spell-check-batch")
async def correct_spelling_batch(queries: List[str]):
    """
    여러 검색어 일괄 오타 교정
    """
    try:
        if not queries:
            raise HTTPException(status_code=400, detail="검색어 목록이 필요합니다")
        
        results = []
        
        for query in queries:
            if query and query.strip():
                original = query.strip()
                corrected = await spell_checker.correct_typo(original)
                suggestions = spell_checker.get_typo_suggestions(original)
                
                results.append({
                    "original": original,
                    "corrected": corrected,
                    "is_corrected": corrected != original,
                    "suggestions": suggestions
                })
            else:
                results.append({
                    "original": query,
                    "corrected": query,
                    "is_corrected": False,
                    "suggestions": []
                })
        
        return {
            "results": results,
            "total": len(results),
            "corrected_count": len([r for r in results if r["is_corrected"]])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 일괄 오타 교정 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일괄 오타 교정 오류: {str(e)}")

@router.get("/test-spell-check")
async def test_spell_check():
    """오타 교정 기능 테스트"""
    test_cases = [
        "ㄹㅏ면",      # 라면
        "ㄱㅣ지",      # 김치  
        "ㅍㅣ망",      # 피망
        "ㅍㅏ프리카",   # 파프리카
        "ㅊㅓ기",      # 치킨
        "ㅇㅏ침",      # 아침
        "ㅁㅏ라탕",    # 마라탕
        "라면",       # 이미 올바름
        "김치찌개",    # 이미 올바름
        "normal text" # 영어
    ]
    
    results = {}
    for test_case in test_cases:
        try:
            corrected = await spell_checker.correct_typo(test_case)
            suggestions = spell_checker.get_typo_suggestions(test_case)
            
            results[test_case] = {
                "original": test_case,
                "corrected": corrected,
                "suggestions": suggestions,
                "is_corrected": corrected != test_case
            }
        except Exception as e:
            results[test_case] = {
                "error": str(e),
                "original": test_case
            }
    
    return {
        "status": "success",
        "test_results": results,
        "summary": {
            "total_tests": len(test_cases),
            "successful_corrections": len([r for r in results.values() if r.get("is_corrected", False)]),
            "errors": len([r for r in results.values() if "error" in r])
        }
    }
