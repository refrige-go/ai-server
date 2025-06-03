from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api import recommendation, search, integration
# OCR과 외부 API는 선택적 기능으로 필요시 활성화
# from app.api import ocr, external
from app.config.settings import get_settings
from app.clients.opensearch_client import opensearch_client
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 설정 로드
settings = get_settings()

app = FastAPI(
    title="Refrige-Go AI Server",
    description="식재료 기반 레시피 추천 AI 서버 (recipe-ai-project OpenSearch 연동)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 (핵심 기능만)
app.include_router(integration.router, prefix="/api/integration", tags=["Integration"])
app.include_router(recommendation.router, prefix="/api/recommend", tags=["Recommendation"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Refrige-Go AI Server",
        "version": "1.0.0",
        "description": "식재료 기반 레시피 추천 AI 서버",
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    try:
        # OpenSearch 연결 테스트
        opensearch_status = await opensearch_client.test_connection()
        
        # 인덱스 통계 가져오기
        stats = await opensearch_client.get_stats()
        
        return {
            "status": "healthy" if opensearch_status else "unhealthy",
            "version": "1.0.0",
            "environment": settings.environment,
            "opensearch": {
                "connected": opensearch_status,
                "host": settings.opensearch_host,
                "port": settings.opensearch_port,
                "recipes_count": stats.get("recipes_count", 0),
                "ingredients_count": stats.get("ingredients_count", 0)
            },
            "features": {
                "vector_search": opensearch_status,
                "text_search": opensearch_status,
                "recipe_recommendation": opensearch_status,
                "ingredient_matching": bool(settings.openai_api_key)
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail={
            "status": "unhealthy",
            "error": str(e),
            "suggestion": "recipe-ai-project OpenSearch가 실행 중인지 확인해주세요"
        })

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    logger.info("🚀 Refrige-Go AI Server 시작")
    logger.info(f"환경: {settings.environment}")
    logger.info(f"OpenSearch: {settings.opensearch_host}:{settings.opensearch_port}")
    
    # OpenSearch 연결 테스트
    try:
        connection_ok = await opensearch_client.test_connection()
        if connection_ok:
            logger.info("✅ OpenSearch 연결 성공")
            
            # 통계 정보 로깅
            stats = await opensearch_client.get_stats()
            logger.info(f"📊 레시피: {stats.get('recipes_count', 0)}개")
            logger.info(f"📊 재료: {stats.get('ingredients_count', 0)}개")
        else:
            logger.warning("⚠️ OpenSearch 연결 실패")
            logger.warning("recipe-ai-project OpenSearch 실행 필요")
            
    except Exception as e:
        logger.error(f"❌ 시작 중 오류: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    logger.info("🛑 AI Server 종료")
    
    try:
        opensearch_client.close()
        logger.info("✅ OpenSearch 연결 종료")
    except Exception as e:
        logger.error(f"⚠️ 종료 중 오류: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
