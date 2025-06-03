# 임시 테스트용 AI 서버 실행 스크립트
# OpenSearch 없이 엔드포인트만 테스트

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "ai_server_connected": False,
        "message": "OpenSearch 연결 필요"
    }

@app.post("/api/search/search/semantic")
async def semantic_search(request: dict):
    return {
        "recipes": [
            {
                "rcpSeq": "test1",
                "rcpNm": "테스트 김치찌개",
                "rcpCategory": "한식",
                "rcpWay2": "끓이기",
                "score": 0.95,
                "matchReason": "테스트 응답",
                "ingredients": []
            }
        ],
        "ingredients": [],
        "totalMatches": 1,
        "processingTime": 0.1
    }

@app.post("/api/search/search/vector")
async def vector_search(request: dict):
    return {
        "query": request.get("query", ""),
        "results": [
            {
                "recipe_id": "test1",
                "name": "테스트 " + request.get("query", "레시피"),
                "category": "한식",
                "ingredients": "테스트 재료",
                "score": 0.9,
                "cooking_method": "끓이기"
            }
        ],
        "total": 1,
        "search_method": "test"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
