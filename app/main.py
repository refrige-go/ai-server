from fastapi import FastAPI
from app.api import endpoints

app = FastAPI(title="AI 재료 매칭 시스템")

app.include_router(endpoints.router)