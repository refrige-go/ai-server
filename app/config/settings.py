from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # OpenSearch 설정 (업로드 스크립트와 통일)
    opensearch_host: str = os.getenv("OPENSEARCH_HOST")
    opensearch_username: str = os.getenv("OPENSEARCH_USERNAME")  # USER → USERNAME
    opensearch_password: str = os.getenv("OPENSEARCH_PASSWORD")
    
    # OpenAI 설정
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    
    # Google Cloud Vision 설정
    google_application_credentials: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # 날씨 API 설정
    weather_api_key: str = os.getenv("WEATHER_API_KEY")
    
    # 제철 식재료 API 설정
    seasonal_api_key: str = os.getenv("SEASONAL_API_KEY")
    
    # 서버 설정
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 벡터 임베딩 설정 (업로드된 데이터와 일치)
    vector_dimension: int = 1536  # OpenAI text-embedding-3-small
    vector_embedding_max_retries: int = 3
    vector_embedding_request_delay: float = 0.5

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()