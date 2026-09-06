from motor.motor_asyncio import AsyncIOMotorClient
import os
from config.basic_config import settings
from urllib.parse import quote_plus
from core.utils.logging_config import logging

logger = logging.getLogger(__name__)


# Use full MongoDB URI if provided (recommended for MongoDB Atlas)
MONGODB_URI = os.getenv("MONGODB_URI")

if MONGODB_URI:
    uri = MONGODB_URI
    logger.info("Using MongoDB URI")

elif settings.MONGO_USER and settings.MONGO_PASSWORD:
    username = quote_plus(settings.MONGO_USER)
    password = quote_plus(settings.MONGO_PASSWORD)

    uri = (
        f"mongodb://{username}:{password}"
        f"@{settings.MONGO_HOST}:{settings.MONGO_PORT}"
        f"/{settings.MONGO_DATABASE}"
    )

else:
    uri = f"mongodb://{settings.MONGO_HOST}:{settings.MONGO_PORT}"


client = AsyncIOMotorClient(
    uri,
    maxPoolSize=20,
    minPoolSize=5,
    maxIdleTimeMS=30000,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    socketTimeoutMS=30000,
    retryWrites=True,
    retryReads=True,
    compressors="zlib",
    waitQueueTimeoutMS=5000,
    maxConnecting=10
)


# Use the actual database name
db = client[settings.MONGO_DATABASE]

user_collection = db["users"]
token_collection = db["tokens"]