"""
Module: config.db_config

Description:
    MongoDB database configuration for the Hi-Lo platform.
"""

import logging
from urllib.parse import quote_plus

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING

from config.basic_config import settings


logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE URL
# ============================================================================

if settings.MONGO_AUTH_ENABLED:

    if not settings.MONGO_USER:
        raise ValueError(
            "MONGO_USER is required when "
            "MONGO_AUTH_ENABLED=true"
        )

    if not settings.MONGO_PASSWORD:
        raise ValueError(
            "MONGO_PASSWORD is required when "
            "MONGO_AUTH_ENABLED=true"
        )

    mongo_user = quote_plus(
        settings.MONGO_USER
    )

    mongo_password = quote_plus(
        settings.MONGO_PASSWORD
    )

    MONGODB_URL = (
        f"mongodb://{mongo_user}:{mongo_password}"
        f"@{settings.MONGO_HOST}:{settings.MONGO_PORT}"
        f"/{settings.MONGO_DATABASE}"
        f"?authSource={settings.MONGO_AUTH_SOURCE}"
    )

else:

    MONGODB_URL = (
        f"mongodb://"
        f"{settings.MONGO_HOST}:"
        f"{settings.MONGO_PORT}"
        f"/{settings.MONGO_DATABASE}"
    )


# ============================================================================
# MONGODB CLIENT
# ============================================================================

mongo_client = AsyncIOMotorClient(
    MONGODB_URL
)


database = mongo_client[
    settings.MONGO_DATABASE
]


# ============================================================================
# COLLECTIONS
# ============================================================================

operator_collection = database[
    "operators"
]

player_collection = database[
    "players"
]

adapter_collection = database[
    "adapters"
]

game_config_collection = database[
    "game_configurations"
]

hilo_game_collection = database[
    "hilo_games"
]

hilo_round_collection = database[
    "hilo_rounds"
]

transaction_collection = database[
    "transactions"
]

audit_log_collection = database[
    "audit_logs"
]

user_collection = database[
    "users"
]

token_collection = database[
    "tokens"
]

file_collection = database[
    "files"
]

admin_collection = database[
    "Admin"
]

notification_collection = database[
    "notifications"
]

fcm_device_tokens_collection = database[
    "fcm_device_tokens"
]

wallet_operation_collection = database[
    "wallet_operations"
]

idempotency_collection = database[
    "idempotency_keys"
]


# ============================================================================
# DATABASE INDEXES
# ============================================================================

async def create_indexes() -> bool:
    """
    Create indexes required by the Hi-Lo platform.
    """

    try:

        # ====================================================================
        # OPERATORS
        # ====================================================================

        await operator_collection.create_index(
            [
                ("operator_code", ASCENDING),
            ],
            unique=True,
        )

        await operator_collection.create_index(
            [
                ("status", ASCENDING),
            ],
        )


        # ====================================================================
        # PLAYERS
        # ====================================================================

        await player_collection.create_index(
            [
                ("operator_id", ASCENDING),
                ("external_player_id", ASCENDING),
            ],
            unique=True,
        )


        # ====================================================================
        # ADAPTERS
        # ====================================================================

        await adapter_collection.create_index(
            [
                ("operator_id", ASCENDING),
                ("adapter_type", ASCENDING),
            ],
        )


        # ====================================================================
        # GAME CONFIGURATIONS
        # ====================================================================

        await game_config_collection.create_index(
            [
                ("operator_id", ASCENDING),
                ("game_code", ASCENDING),
            ],
            unique=True,
        )

        await game_config_collection.create_index(
            [
                ("operator_id", ASCENDING),
                ("game_code", ASCENDING),
                ("status", ASCENDING),
            ],
        )


        # ====================================================================
        # GAMES
        # ====================================================================

        await hilo_game_collection.create_index(
            [
                ("operator_id", ASCENDING),
                ("player_id", ASCENDING),
                ("created_at", DESCENDING),
            ],
        )

        await hilo_game_collection.create_index(
            [
                ("status", ASCENDING),
            ],
        )


        # ====================================================================
        # ROUNDS
        # ====================================================================

        await hilo_round_collection.create_index(
            [
                ("game_id", ASCENDING),
                ("created_at", DESCENDING),
            ],
        )

        await hilo_round_collection.create_index(
            [
                ("player_id", ASCENDING),
                ("created_at", DESCENDING),
            ],
        )


        # ====================================================================
        # TRANSACTIONS
        # ====================================================================

        await transaction_collection.create_index(
            [
                ("transaction_id", ASCENDING),
            ],
            unique=True,
        )

        await transaction_collection.create_index(
            [
                ("operator_id", ASCENDING),
                ("idempotency_key", ASCENDING),
            ],
            unique=True,
            sparse=True,
        )

        await transaction_collection.create_index(
            [
                ("operator_id", ASCENDING),
                ("external_transaction_id", ASCENDING),
            ],
            sparse=True,
        )

        await transaction_collection.create_index(
            [
                ("operator_id", ASCENDING),
                ("player_id", ASCENDING),
                ("created_at", DESCENDING),
            ],
        )

        await transaction_collection.create_index(
            [
                ("game_id", ASCENDING),
                ("created_at", DESCENDING),
            ],
        )

        await transaction_collection.create_index(
            [
                ("round_id", ASCENDING),
                ("created_at", ASCENDING),
            ],
        )


        # ====================================================================
        # WALLET OPERATIONS
        # ====================================================================

        await wallet_operation_collection.create_index(
            [
                ("transaction_id", ASCENDING),
            ],
        )


        # ====================================================================
        # AUDIT LOGS
        # ====================================================================

        await audit_log_collection.create_index(
            [
                ("request_id", ASCENDING),
                ("created_at", ASCENDING),
            ],
        )

        await audit_log_collection.create_index(
            [
                ("operator_id", ASCENDING),
                ("created_at", DESCENDING),
            ],
        )

        await audit_log_collection.create_index(
            [
                ("player_id", ASCENDING),
                ("created_at", DESCENDING),
            ],
        )

        await audit_log_collection.create_index(
            [
                ("game_id", ASCENDING),
                ("created_at", ASCENDING),
            ],
        )

        await audit_log_collection.create_index(
            [
                ("round_id", ASCENDING),
                ("created_at", ASCENDING),
            ],
        )

        await audit_log_collection.create_index(
            [
                ("transaction_id", ASCENDING),
                ("created_at", ASCENDING),
            ],
        )


        # ====================================================================
        # IDEMPOTENCY
        # ====================================================================

        await idempotency_collection.create_index(
            [
                ("operator_id", ASCENDING),
                ("idempotency_key", ASCENDING),
            ],
            unique=True,
        )


        logger.info(
            "MongoDB indexes created successfully."
        )

        return True

    except Exception as exc:

        logger.error(
            "Error creating database indexes: %s",
            exc,
        )

        return False


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

async def initialize_database() -> bool:
    """
    Initialize and verify the MongoDB connection.
    """

    try:

        await mongo_client.admin.command(
            "ping"
        )

        logger.info(
            "MongoDB ping successful."
        )

        indexes_created = await create_indexes()

        if not indexes_created:

            logger.error(
                "MongoDB connected, "
                "but index creation failed."
            )

            return False

        logger.info(
            "MongoDB initialized successfully."
        )

        return True

    except Exception as exc:

        logger.error(
            "Database initialization failed: %s",
            exc,
        )

        return False


# ============================================================================
# DATABASE SHUTDOWN
# ============================================================================

async def close_database() -> None:
    """
    Close MongoDB connection during application shutdown.
    """

    try:

        mongo_client.close()

        logger.info(
            "MongoDB connection closed successfully."
        )

    except Exception as exc:

        logger.error(
            "Error closing MongoDB connection: %s",
            exc,
        )