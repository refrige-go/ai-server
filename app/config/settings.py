from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # OpenSearch 설정
    OPENSEARCH_HOST: str = os.getenv("OPENSEARCH_HOST", "localhost")
    OPENSEARCH_USER: str = os.getenv("OPENSEARCH_USER", "admin")
    OPENSEARCH_PASSWORD: str = os.getenv("OPENSEARCH_PASSWORD", "admin")
    
    # OpenAI 설정
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    
    # Google Cloud Vision 설정
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # 날씨 API 설정
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY")
    
    # 제철 식재료 API 설정
    SEASONAL_API_KEY: str = os.getenv("SEASONAL_API_KEY")
    
    # 서버 설정
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 벡터 임베딩 설정
    VECTOR_DIMENSION: int = 1536  # OpenAI text-embedding-3-small
    MAX_RETRIES: int = 3
    REQUEST_DELAY: float = 0.5

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 