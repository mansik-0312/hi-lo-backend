from pydantic_settings import BaseSettings
from fastapi import FastAPI
from typing import Optional
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os 
from dotenv import load_dotenv
from core.utils.logging_config import logging

logger = logging.getLogger(__name__)
# Load environment variables from .env
load_dotenv(override=True)  

#Define App
app = FastAPI()

# Get ALLOWED_HOSTS from the environment and split it into a list
allowed_hosts = os.getenv("ALLOWED_HOSTS")

logger.info('allowed---hosts',allowed_hosts)

class Settings(BaseSettings):

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    # ========================================================================
    # MongoDB
    # ========================================================================

    MONGO_AUTH_ENABLED: bool = False

    MONGO_USER: Optional[str] = None

    MONGO_PASSWORD: Optional[str] = None

    MONGO_HOST: str = "localhost"

    MONGO_PORT: int = 27017

    MONGO_DATABASE: str = "hilo_db"

    MONGO_AUTH_SOURCE: str = "admin"

    # ========================================================================

    CELERY_PREFIX: str = "fastapi"

    ADMIN_NAME: str
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str

    SECRET_ACCESS_KEY: str
    SECRET_REFRESH_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    ALGORITHM: str
    FIREBASE_CRED_PATH: str

    class Config:
        env_file = ".env"
        extra = "ignore"

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts,
)
    
settings = Settings()
