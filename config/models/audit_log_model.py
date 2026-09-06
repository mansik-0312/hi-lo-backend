"""
Module: config.models.audit_log_model

Description:
    Persistence model and repository operations for platform audit logs.

Audit logs provide an immutable trace of important platform events
across:

    - Operators.
    - Players.
    - Games.
    - Rounds.
    - Financial transactions.
    - Wallet adapters.
    - API requests.

Audit logs are intended for:

    - Debugging.
    - Operator support.
    - Financial investigation.
    - Transaction reconciliation.
    - Security investigation.
    - Game lifecycle tracing.
    - Integration monitoring.

Important:
    Audit logs are append-only.

    They must not be updated or deleted as part of normal application
    operations.

Business logic must remain in the service layer.

MongoDB-specific operations must remain in this module.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId
from pydantic import BaseModel, Field

from config.db_config import audit_log_collection


# ============================================================================
# AUDIT LOG MODEL
# ============================================================================


class AuditLogModel(BaseModel):
    """
    Represents an immutable auditable platform event.

    An audit event may belong to an operator, player, game, round,
    transaction, adapter, or API request.

    Attributes:
        id:
            Internal MongoDB audit log identifier.

        operator_id:
            Operator associated with the event.

        player_id:
            Player associated with the event.

        game_id:
            Game associated with the event.

        round_id:
            Round associated with the event.

        transaction_id:
            Financial transaction associated with the event.

        adapter_id:
            Adapter involved in the event.

        request_id:
            Unique request/correlation identifier.

        idempotency_key:
            Idempotency key associated with the request.

        action:
            Machine-readable action name.

        category:
            Category of the event.

        status:
            Result/status of the operation.

        source:
            Component that generated the audit event.

        message:
            Human-readable description of the event.

        metadata:
            Additional non-sensitive event information.

        created_at:
            Timestamp when the event occurred.
    """

    id: Optional[str] = Field(
        default=None,
        description="Internal MongoDB audit log identifier.",
    )

    # ------------------------------------------------------------------------
    # ENTITY REFERENCES
    # ------------------------------------------------------------------------

    operator_id: Optional[str] = Field(
        default=None,
        description="Operator associated with the event.",
    )

    player_id: Optional[str] = Field(
        default=None,
        description="Player associated with the event.",
    )

    game_id: Optional[str] = Field(
        default=None,
        description="Game associated with the event.",
    )

    round_id: Optional[str] = Field(
        default=None,
        description="Round associated with the event.",
    )

    transaction_id: Optional[str] = Field(
        default=None,
        description="Financial transaction associated with the event.",
    )

    adapter_id: Optional[str] = Field(
        default=None,
        description="Adapter associated with the event.",
    )

    # ------------------------------------------------------------------------
    # REQUEST CORRELATION
    # ------------------------------------------------------------------------

    request_id: Optional[str] = Field(
        default=None,
        description="Request/correlation identifier.",
    )

    idempotency_key: Optional[str] = Field(
        default=None,
        description="Idempotency key associated with the request.",
    )

    # ------------------------------------------------------------------------
    # EVENT INFORMATION
    # ------------------------------------------------------------------------

    action: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Machine-readable audit action.",
    )

    category: str = Field(
        default="system",
        max_length=50,
        description="Audit event category.",
    )

    status: str = Field(
        default="success",
        max_length=50,
        description="Status/result of the audited operation.",
    )

    source: str = Field(
        default="api",
        max_length=100,
        description="Application component generating the event.",
    )

    message: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Human-readable event description.",
    )

    # ------------------------------------------------------------------------
    # ADDITIONAL INFORMATION
    # ------------------------------------------------------------------------

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional non-sensitive audit information.",
    )

    # ------------------------------------------------------------------------
    # TIMESTAMP
    # ------------------------------------------------------------------------

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ============================================================================
# AUDIT LOG REPOSITORY
# ============================================================================


class AuditLogRepository:
    """
    Repository responsible for audit log persistence and retrieval.

    Audit logs are append-only.

    This repository intentionally does not provide update or delete
    operations.

    The repository must not contain business logic.
    """

    # ========================================================================
    # CREATE
    # ========================================================================

    @staticmethod
    async def create(
        data: Dict[str, Any],
    ) -> str:
        """
        Create an immutable audit log entry.

        Args:
            data:
                Audit event document.

        Returns:
            str:
                MongoDB identifier of the created audit event.
        """

        data = data.copy()

        data["created_at"] = datetime.now(
            timezone.utc
        )

        result = await audit_log_collection.insert_one(
            data
        )

        return str(result.inserted_id)

    # ========================================================================
    # GET BY ID
    # ========================================================================

    @staticmethod
    async def get_by_id(
        audit_log_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an audit log using its MongoDB identifier.

        Args:
            audit_log_id:
                MongoDB ObjectId represented as a string.

        Returns:
            Audit log document if found, otherwise None.
        """

        if not ObjectId.is_valid(audit_log_id):
            return None

        document = await audit_log_collection.find_one(
            {
                "_id": ObjectId(audit_log_id),
            }
        )

        if document and "_id" in document:
            document["id"] = str(
                document.pop("_id")
            )

        return document

    # ========================================================================
    # GET BY REQUEST ID
    # ========================================================================

    @staticmethod
    async def get_by_request_id(
        request_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all audit events associated with a request.

        Events are returned in chronological order.

        Args:
            request_id:
                Request/correlation identifier.

        Returns:
            List of audit events.
        """

        cursor = (
            audit_log_collection
            .find(
                {
                    "request_id": request_id,
                }
            )
            .sort(
                "created_at",
                1,
            )
        )

        documents = await cursor.to_list(
            length=None
        )

        for document in documents:
            if "_id" in document:
                document["id"] = str(
                    document.pop("_id")
                )

        return documents

    # ========================================================================
    # GET BY TRANSACTION
    # ========================================================================

    @staticmethod
    async def get_by_transaction_id(
        transaction_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all audit events associated with a transaction.

        Args:
            transaction_id:
                Internal transaction identifier.

        Returns:
            List of audit events.
        """

        cursor = (
            audit_log_collection
            .find(
                {
                    "transaction_id": transaction_id,
                }
            )
            .sort(
                "created_at",
                1,
            )
        )

        documents = await cursor.to_list(
            length=None
        )

        for document in documents:
            if "_id" in document:
                document["id"] = str(
                    document.pop("_id")
                )

        return documents

    # ========================================================================
    # GET BY ROUND
    # ========================================================================

    @staticmethod
    async def get_by_round_id(
        round_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all audit events associated with a game round.

        Args:
            round_id:
                Hi-Lo round identifier.

        Returns:
            List of audit events.
        """

        cursor = (
            audit_log_collection
            .find(
                {
                    "round_id": round_id,
                }
            )
            .sort(
                "created_at",
                1,
            )
        )

        documents = await cursor.to_list(
            length=None
        )

        for document in documents:
            if "_id" in document:
                document["id"] = str(
                    document.pop("_id")
                )

        return documents

    # ========================================================================
    # GET BY GAME
    # ========================================================================

    @staticmethod
    async def get_by_game_id(
        game_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all audit events associated with a game.

        Args:
            game_id:
                Game identifier.

        Returns:
            List of audit events.
        """

        cursor = (
            audit_log_collection
            .find(
                {
                    "game_id": game_id,
                }
            )
            .sort(
                "created_at",
                1,
            )
        )

        documents = await cursor.to_list(
            length=None
        )

        for document in documents:
            if "_id" in document:
                document["id"] = str(
                    document.pop("_id")
                )

        return documents

    # ========================================================================
    # GET BY PLAYER
    # ========================================================================

    @staticmethod
    async def get_by_player_id(
        player_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve paginated audit events for a player.

        Args:
            player_id:
                Player identifier.

            skip:
                Number of records to skip.

            limit:
                Maximum number of records to return.

        Returns:
            Tuple containing:
                - Audit events.
                - Total event count.
        """

        condition = {
            "player_id": player_id,
        }

        cursor = (
            audit_log_collection
            .find(condition)
            .sort(
                "created_at",
                -1,
            )
            .skip(skip)
            .limit(limit)
        )

        documents = await cursor.to_list(
            length=limit
        )

        total = await audit_log_collection.count_documents(
            condition
        )

        for document in documents:
            if "_id" in document:
                document["id"] = str(
                    document.pop("_id")
                )

        return documents, total

    # ========================================================================
    # GET BY OPERATOR
    # ========================================================================

    @staticmethod
    async def get_by_operator_id(
        operator_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve paginated audit events for an operator.

        Args:
            operator_id:
                Operator identifier.

            skip:
                Number of records to skip.

            limit:
                Maximum number of records to return.

        Returns:
            Tuple containing:
                - Audit events.
                - Total event count.
        """

        condition = {
            "operator_id": operator_id,
        }

        cursor = (
            audit_log_collection
            .find(condition)
            .sort(
                "created_at",
                -1,
            )
            .skip(skip)
            .limit(limit)
        )

        documents = await cursor.to_list(
            length=limit
        )

        total = await audit_log_collection.count_documents(
            condition
        )

        for document in documents:
            if "_id" in document:
                document["id"] = str(
                    document.pop("_id")
                )

        return documents, total

    # ========================================================================
    # GET BY ACTION
    # ========================================================================

    @staticmethod
    async def get_by_action(
        action: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve audit events by action.

        Args:
            action:
                Machine-readable action name.

            skip:
                Number of records to skip.

            limit:
                Maximum number of records.

        Returns:
            Tuple containing:
                - Audit events.
                - Total event count.
        """

        condition = {
            "action": action,
        }

        cursor = (
            audit_log_collection
            .find(condition)
            .sort(
                "created_at",
                -1,
            )
            .skip(skip)
            .limit(limit)
        )

        documents = await cursor.to_list(
            length=limit
        )

        total = await audit_log_collection.count_documents(
            condition
        )

        for document in documents:
            if "_id" in document:
                document["id"] = str(
                    document.pop("_id")
                )

        return documents, total