"""
Module: config.models.operator_model

Description:
    Persistence model and repository operations for
    operator configurations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from config.db_config import operator_collection
from config.models.enums import OperatorStatus


class OperatorModel(BaseModel):
    """
    Represents an operator/casino configuration.
    """

    id: Optional[str] = None

    operator_code: str

    name: str

    status: OperatorStatus = OperatorStatus.ACTIVE

    default_currency: str

    configuration: Dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


class OperatorRepository:
    """
    Repository responsible for operator persistence.
    """

    @staticmethod
    async def create(
        data: Dict[str, Any],
    ) -> str:
        """
        Create an operator configuration.
        """

        now = datetime.now(timezone.utc)

        # Ensure default values are persisted.
        data.setdefault(
            "status",
            OperatorStatus.ACTIVE.value,
        )

        data.setdefault(
            "configuration",
            {},
        )

        data["created_at"] = now
        data["updated_at"] = now

        result = await operator_collection.insert_one(
            data
        )

        return str(result.inserted_id)

    @staticmethod
    async def get_by_id(
        operator_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an operator by ID.
        """

        if not ObjectId.is_valid(operator_id):
            return None

        return await operator_collection.find_one(
            {
                "_id": ObjectId(operator_id),
            }
        )

    @staticmethod
    async def get_by_code(
        operator_code: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an operator by operator code.
        """

        return await operator_collection.find_one(
            {
                "operator_code": operator_code,
            }
        )

    @staticmethod
    async def update(
        operator_id: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Update an operator configuration.
        """

        if not ObjectId.is_valid(operator_id):
            return False

        data["updated_at"] = datetime.now(
            timezone.utc
        )

        result = await operator_collection.update_one(
            {
                "_id": ObjectId(operator_id),
            },
            {
                "$set": data,
            },
        )

        return result.modified_count > 0

    # ========================================================================
    # UPDATE STATUS
    # ========================================================================

    @staticmethod
    async def update_status(
        operator_id: str,
        status: OperatorStatus,
    ) -> bool:
        """
        Update only the lifecycle status of an operator.

        Args:
            operator_id:
                MongoDB ObjectId represented as a string.

            status:
                New operator status.

        Returns:
            bool:
                True when the record was modified,
                otherwise False.
        """

        if not ObjectId.is_valid(operator_id):
            return False

        result = await operator_collection.update_one(
            {
                "_id": ObjectId(operator_id),
            },
            {
                "$set": {
                    "status": status.value,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        return result.modified_count > 0

    # ========================================================================
    # DELETE
    # ========================================================================

    @staticmethod
    async def delete(
        operator_id: str,
    ) -> bool:
        """
        Delete an operator from MongoDB.

        This operation should normally be avoided in production.
        Operator deactivation should generally be preferred so that
        historical games and transactions remain traceable.

        Args:
            operator_id:
                MongoDB ObjectId represented as a string.

        Returns:
            bool:
                True when the operator was deleted,
                otherwise False.
        """

        if not ObjectId.is_valid(operator_id):
            return False

        result = await operator_collection.delete_one(
            {
                "_id": ObjectId(operator_id),
            }
        )

        return result.deleted_count > 0

    # ========================================================================
    # EXISTS
    # ========================================================================

    @staticmethod
    async def exists_by_code(
        operator_code: str,
    ) -> bool:
        """
        Check whether an operator code already exists.

        Args:
            operator_code:
                Operator code to check.

        Returns:
            bool:
                True if the operator exists, otherwise False.
        """

        operator = await operator_collection.find_one(
            {
                "operator_code": operator_code,
            },
            {
                "_id": 1,
            },
        )

        return operator is not None