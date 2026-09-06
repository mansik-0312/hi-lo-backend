"""
Module: config.models.idempotency_model

Description:
    Persistence model and repository for idempotent API operations.

Idempotency prevents duplicate financial operations when an external
operator retries the same request.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from config.db_config import idempotency_collection
from config.models.enums import IdempotencyStatus


class IdempotencyModel(BaseModel):
    """
    Represents an idempotent request.
    """

    id: Optional[str] = None

    operator_id: str

    idempotency_key: str

    status: IdempotencyStatus

    response_data: Optional[Dict[str, Any]] = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    completed_at: Optional[datetime] = None


class IdempotencyRepository:
    """
    Repository responsible for idempotency records.
    """

    @staticmethod
    async def create(
        data: Dict[str, Any],
    ) -> str:
        """
        Create an idempotency record.
        """

        data["created_at"] = datetime.now(timezone.utc)

        result = await idempotency_collection.insert_one(
            data
        )

        return str(result.inserted_id)

    @staticmethod
    async def get(
        operator_id: str,
        idempotency_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an existing idempotency record.
        """

        return await idempotency_collection.find_one(
            {
                "operator_id": operator_id,
                "idempotency_key": idempotency_key,
            }
        )

    @staticmethod
    async def update(
        operator_id: str,
        idempotency_key: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Update an idempotency record.
        """

        result = await idempotency_collection.update_one(
            {
                "operator_id": operator_id,
                "idempotency_key": idempotency_key,
            },
            {
                "$set": data,
            },
        )

        return result.modified_count > 0