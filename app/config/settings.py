from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

# 환경별 .env 파일 로드
env_file = ".env.local" if os.path.exists(".env.local") else ".env"
load_dotenv(env_file)

class Settings(BaseSettings):
    # OpenSearch 설정 (recipe-ai-project 호환)
    opensearch_host: str = os.getenv("OPENSEARCH_HOST", "localhost")
    opensearch_port: int = int(os.getenv("OPENSEARCH_PORT", "9201"))
    opensearch_username: str = os.getenv("OPENSEARCH_USERNAME", "")
    opensearch_password: str = os.getenv("OPENSEARCH_PASSWORD", "")
    opensearch_use_ssl: bool = os.getenv("OPENSEARCH_USE_SSL", "false").lower() == "true"
    
    # OpenAI 설정
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Google Cloud Vision 설정
    google_application_credentials: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    
    # 날씨 API 설정
    weather_api_key: str = os.getenv("WEATHER_API_KEY", "")
    
    # 제철 식재료 API 설정
    seasonal_api_key: str = os.getenv("SEASONAL_API_KEY", "")
    
    # 서버 설정
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "production")
    
    # 벡터 임베딩 설정 (recipe-ai-project와 일치)
    vector_dimension: int = 1536  # OpenAI text-embedding-3-small
    vector_embedding_max_retries: int = 3
    vector_embedding_request_delay: float = 0.5
    
    # 인덱스 설정 (recipe-ai-project와 일치)
    recipes_index: str = "recipes"
    ingredients_index: str = "ingredients"
    
    # CORS 설정
    allowed_origins: list = ["*"]  # 개발용, 운영환경에서는 특정 도메인으로 제한
    
    # 로깅 설정
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = env_file
        case_sensitive = False

    def is_local_environment(self) -> bool:
        """로컬 개발 환경인지 확인"""
        return (
            self.environment == "development" or 
            self.opensearch_host in ["localhost", "127.0.0.1"]
        )
    
    def get_opensearch_config(self) -> dict:
        """OpenSearch 연결 설정 반환"""
        if self.is_local_environment():
            return {
                "hosts": [{"host": self.opensearch_host, "port": self.opensearch_port}],
                "use_ssl": False,
                "verify_certs": False,
                "http_auth": None
            }
        else:
            return {
                "hosts": [{"host": self.opensearch_host, "port": 443}],
                "use_ssl": True,
                "verify_certs": True,
                "http_auth": (self.opensearch_username, self.opensearch_password) if self.opensearch_username else None
            }

@lru_cache()
def get_settings() -> Settings:
    return Settings()
