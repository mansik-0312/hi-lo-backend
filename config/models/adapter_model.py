"""
Module: config.models.adapter_model

Description:
    Persistence model and repository operations for operator adapter
    configurations.

An adapter represents the integration configuration between an operator
and an external service such as:

    - Wallet service.
    - Balance service.
    - Debit service.
    - Credit service.
    - Rollback service.

The adapter layer allows the Hi-Lo game to remain independent from
operator-specific wallet implementations.

Security:
    - Secrets must never be stored directly in source code.
    - Secrets must never be returned through API responses.
    - Sensitive credentials should be stored in a secure secret store
      and referenced using `secret_reference`.

Business logic must remain in:
    services/adapter/adapter_service.py
    services/adapter/adapter_factory.py

Database operations must remain in this module.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId
from pydantic import BaseModel, Field

from config.db_config import adapter_collection
from config.models.enums import AdapterStatus, AdapterType


# ============================================================================
# ADAPTER MODEL
# ============================================================================


class AdapterModel(BaseModel):
    """
    Persistence model representing an operator adapter configuration.

    An adapter belongs to exactly one operator.

    The adapter does not implement wallet behavior itself. It only stores
    the configuration required by the adapter implementation selected by
    the application.

    Example:

        Operator
            |
            +-- HTTP Wallet Adapter
            |
            +-- Mock Wallet Adapter
            |
            +-- Future Wallet Adapter

    Attributes:
        id:
            Internal MongoDB adapter identifier.

        operator_id:
            Internal identifier of the operator owning the adapter.

        adapter_type:
            Type of adapter implementation to use.

        name:
            Human-readable adapter name.

        status:
            Current adapter lifecycle status.

        base_url:
            Base URL of an external service for HTTP adapters.

        authentication_type:
            Authentication mechanism used by the external service.

        endpoints:
            Endpoint mapping used by the adapter.

        configuration:
            Non-sensitive adapter configuration.

        secret_reference:
            Reference to credentials stored in a secure secret store.

        timeout_seconds:
            HTTP/network timeout used by the adapter.

        retry_count:
            Number of retries allowed for recoverable integration failures.

        metadata:
            Additional non-sensitive adapter metadata.

        created_at:
            Timestamp when the adapter was created.

        updated_at:
            Timestamp when the adapter was last updated.
    """

    id: Optional[str] = Field(
        default=None,
        description="Internal MongoDB adapter identifier.",
    )

    operator_id: str = Field(
        ...,
        min_length=1,
        description="Internal operator identifier.",
    )

    adapter_type: AdapterType = Field(
        ...,
        description="Adapter implementation type.",
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Human-readable adapter name.",
    )

    status: AdapterStatus = Field(
        default=AdapterStatus.ACTIVE,
        description="Current adapter lifecycle status.",
    )

    # ------------------------------------------------------------------------
    # External service configuration
    # ------------------------------------------------------------------------

    base_url: Optional[str] = Field(
        default=None,
        description="Base URL for an external integration.",
    )

    authentication_type: Optional[str] = Field(
        default=None,
        description="Authentication mechanism used by the integration.",
    )

    endpoints: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Logical endpoint mapping used by the adapter."
        ),
    )

    # ------------------------------------------------------------------------
    # Adapter configuration
    # ------------------------------------------------------------------------

    configuration: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Non-sensitive adapter-specific configuration."
        ),
    )

    # ------------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------------

    secret_reference: Optional[str] = Field(
        default=None,
        description=(
            "Reference to credentials stored outside MongoDB."
        ),
    )

    # ------------------------------------------------------------------------
    # Network reliability
    # ------------------------------------------------------------------------

    timeout_seconds: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Maximum network request timeout in seconds.",
    )

    retry_count: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Number of retry attempts for recoverable failures.",
    )

    # ------------------------------------------------------------------------
    # Additional metadata
    # ------------------------------------------------------------------------

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional non-sensitive adapter metadata.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ============================================================================
# ADAPTER REPOSITORY
# ============================================================================


class AdapterRepository:
    """
    Repository responsible for adapter persistence.

    This repository contains MongoDB operations only.

    It must not contain:

        - Wallet business logic.
        - HTTP request execution.
        - Authentication handling.
        - Transaction processing.
        - Adapter selection rules.
        - Betting logic.
        - Game logic.
    """

    # ========================================================================
    # CREATE
    # ========================================================================

    @staticmethod
    async def create(
        data: Dict[str, Any],
    ) -> str:
        """
        Create a new adapter configuration.

        Args:
            data:
                Adapter document to persist.

        Returns:
            str:
                MongoDB ObjectId of the created adapter.
        """

        now = datetime.now(timezone.utc)

        data["created_at"] = now
        data["updated_at"] = now

        result = await adapter_collection.insert_one(data)

        return str(result.inserted_id)

    # ========================================================================
    # GET BY ID
    # ========================================================================

    @staticmethod
    async def get_by_id(
        adapter_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an adapter using its MongoDB identifier.

        Args:
            adapter_id:
                MongoDB ObjectId represented as a string.

        Returns:
            Optional[Dict[str, Any]]:
                Adapter document if found, otherwise None.
        """

        if not ObjectId.is_valid(adapter_id):
            return None

        return await adapter_collection.find_one(
            {
                "_id": ObjectId(adapter_id),
            }
        )

    # ========================================================================
    # GET ACTIVE ADAPTER FOR OPERATOR
    # ========================================================================

    @staticmethod
    async def get_active_for_operator(
        operator_id: str,
        adapter_type: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an active adapter of a specific type
        for an operator.
        """

        return await adapter_collection.find_one(
            {
                "operator_id": operator_id,
                "adapter_type": adapter_type,
                "status": AdapterStatus.ACTIVE.value,
            }
        )
    
    # ========================================================================
    # GET ALL ADAPTERS FOR OPERATOR
    # ========================================================================

    @staticmethod
    async def get_by_operator(
        operator_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve adapters belonging to an operator.

        Args:
            operator_id:
                Internal operator identifier.

            skip:
                Number of records to skip.

            limit:
                Maximum number of records to return.

        Returns:
            Tuple[List[Dict[str, Any]], int]:
                Adapter documents and total matching count.
        """

        condition = {
            "operator_id": operator_id,
        }

        cursor = (
            adapter_collection
            .find(condition)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        adapters = await cursor.to_list(
            length=limit
        )

        total = await adapter_collection.count_documents(
            condition
        )

        return adapters, total

    # ========================================================================
    # UPDATE
    # ========================================================================

    @staticmethod
    async def update(
        adapter_id: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Update an adapter configuration.

        Args:
            adapter_id:
                MongoDB adapter identifier.

            data:
                Fields that should be updated.

        Returns:
            bool:
                True when the adapter was modified,
                otherwise False.
        """

        if not ObjectId.is_valid(adapter_id):
            return False

        data["updated_at"] = datetime.now(
            timezone.utc
        )

        result = await adapter_collection.update_one(
            {
                "_id": ObjectId(adapter_id),
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
        adapter_id: str,
        status: AdapterStatus,
    ) -> bool:
        """
        Update only the lifecycle status of an adapter.

        Args:
            adapter_id:
                MongoDB adapter identifier.

            status:
                New adapter status.

        Returns:
            bool:
                True when the adapter status was modified,
                otherwise False.
        """

        if not ObjectId.is_valid(adapter_id):
            return False

        result = await adapter_collection.update_one(
            {
                "_id": ObjectId(adapter_id),
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
    # EXISTS
    # ========================================================================

    @staticmethod
    async def exists(
        operator_id: str,
        name: str,
    ) -> bool:
        """
        Check whether an adapter with the specified name exists
        for an operator.

        Args:
            operator_id:
                Internal operator identifier.

            name:
                Adapter name.

        Returns:
            bool:
                True if the adapter exists, otherwise False.
        """

        adapter = await adapter_collection.find_one(
            {
                "operator_id": operator_id,
                "name": name,
            },
            {
                "_id": 1,
            },
        )

        return adapter is not None

    # ========================================================================
    # DELETE
    # ========================================================================

    @staticmethod
    async def delete(
        adapter_id: str,
    ) -> bool:
        """
        Permanently delete an adapter configuration.

        In production, deactivation should generally be preferred over
        deletion so historical transaction and audit records remain
        traceable.

        Args:
            adapter_id:
                MongoDB adapter identifier.

        Returns:
            bool:
                True when the adapter was deleted,
                otherwise False.
        """

        if not ObjectId.is_valid(adapter_id):
            return False

        result = await adapter_collection.delete_one(
            {
                "_id": ObjectId(adapter_id),
            }
        )

        return result.deleted_count > 0

    @staticmethod
    async def get_active_by_operator(
        operator_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve the active adapter for an operator.
        """

        return await adapter_collection.find_one(
            {
                "operator_id": operator_id,
                "status": AdapterStatus.ACTIVE.value,
            }
        )