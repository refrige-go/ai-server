from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
<<<<<<< HEAD
# from app.api import ocr, recommendation, external
from app.api import ocr  # OCR만 import
import logging
import sys # 로깅할 때 추가 
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정 수정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log', encoding='utf-8')  # UTF-8 인코딩 지정
    ]
)
logger = logging.getLogger(__name__)

# app = FastAPI(
#     title="AI Recipe Server",
#     description="레시피 AI 서버 - OCR, 추천, 날씨 기반 추천 기능 제공",
#     version="1.0.0"
# )

app = FastAPI()
=======
from app.api import ocr, recommendation, external, search

app = FastAPI(
    title="AI Recipe Server",
    description="레시피 AI 서버 - OCR, 추천, 날씨 기반 추천 기능 제공",
    version="1.0.0"
)
>>>>>>> dev

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
<<<<<<< HEAD
# app.include_router(recommendation.router, prefix="/api/v1/recipes", tags=["Recommendation"])
# app.include_router(external.router, prefix="/api/v1/external", tags=["External"])

@app.get("/")
async def root():
    return {"message": "AI Recipe Server is running"} 
=======
app.include_router(recommendation.router, prefix="/api/v1/recipes", tags=["Recommendation"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(external.router, prefix="/api/v1/external", tags=["External"])

@app.get("/")
async def root():
    return {"message": "AI Recipe Server is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
>>>>>>> dev
