from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import ocr, recommendation, external, search

app = FastAPI(
    title="AI Recipe Server",
    description="레시피 AI 서버 - OCR, 추천, 날씨 기반 추천 기능 제공",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 특정 도메인만 허용하도록 수정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR"])
app.include_router(recommendation.router, prefix="/api/v1/recipes", tags=["Recommendation"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(external.router, prefix="/api/v1/external", tags=["External"])

@app.get("/")
async def root():
    return {"message": "AI Recipe Server is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}