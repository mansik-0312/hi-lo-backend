# from pymongo.mongo_client import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient  #for the cron job to query in scheuler
from config.basic_config import settings
from urllib.parse import quote_plus
from pymongo import ASCENDING, DESCENDING
import asyncio
from core.utils.logging_config import logging

logger = logging.getLogger(__name__)
#uri = "mongodb://localhost:27017/"

# Construct MongoDB URI using settings variables
if settings.MONGO_USER and settings.MONGO_PASSWORD:
    username = quote_plus(settings.MONGO_USER)
    password = quote_plus(settings.MONGO_PASSWORD)
    uri = f"mongodb://{username}:{password}@{settings.MONGO_HOST}:{settings.MONGO_PORT}/{settings.MONGO_DATABASE}"
    logger.info('db compass url dev-----------------------',uri)

else:
    uri = f"mongodb://{settings.MONGO_HOST}:{settings.MONGO_PORT}"
    logger.info('db compass url local-----------------------',uri)

# Singleton MongoDB client with optimized connection pooling
class MongoDBClient:
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._client = AsyncIOMotorClient(
                uri,
                maxPoolSize=100,  # Increased from 50 for better performance
                minPoolSize=20,   # Increased from 10 for better performance
                maxIdleTimeMS=30000,  # Close connections after 30 seconds of inactivity
                serverSelectionTimeoutMS=5000,  # Timeout for server selection
                connectTimeoutMS=10000,  # Connection timeout
                # socketTimeoutMS=30000,  # Socket timeout
                 socketTimeoutMS=300000,  # Socket timeout
                retryWrites=True,  # Enable retry for write operations
                retryReads=True,  # Enable retry for read operations
                compressors="zlib",  # Enable compression
                waitQueueTimeoutMS=5000,  # Wait queue timeout
                maxConnecting=10  # Maximum concurrent connection attempts
            )
    
    @property
    def client(self):
        return self._client
    
    async def close(self):
        """Close MongoDB connections properly"""
        if self._client:
            self._client.close()
    
    async def ping(self):
        """Test database connectivity"""
        try:
            await self._client.admin.command('ping')
            return True
        except Exception as e:
            return False

# Create singleton instance
mongodb_client = MongoDBClient()
client = mongodb_client.client
db = client[settings.MONGO_DATABASE]

# Collection definitions
user_collection = db["users"]
token_collection = db["tokens"]
file_collection = db["files"]
admin_collection = db["Admin"]
notification_collection = db["notifications"]
fcm_device_tokens_collection = db["fcm_device_tokens"]

async def create_indexes():
    """
    Placeholder for database indexes.
    Currently no indexes are created.
    """
    try:
        # No indexes to create at the moment
        return True
    except Exception as e:
        logger.error(f"------------Error creating indexes: {e}")
        return False

        
async def initialize_database():
    """Initialize database connection and test connectivity"""
    try:
        # Test the connection during startup
        is_connected = await mongodb_client.ping()
        if is_connected:
            return True
        else:
            return False
    except Exception as e:
        return False

async def close_database():
    """Close database connections properly"""
    try:
        await mongodb_client.close()
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")

        