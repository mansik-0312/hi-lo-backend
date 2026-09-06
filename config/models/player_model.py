"""
Module: config.models.player_model

Description:
    Persistence model and repository operations for game players.

Players belong to an operator and are identified using the
operator's external player ID.

The game platform does not own the operator's complete user account.
It only maintains the minimum player information required for:

    - Game sessions.
    - Wallet transactions.
    - Game history.
    - Operator-level player isolation.
    - Auditing.
    - Currency validation.

Business logic must remain in:
    services/game/
    services/wallet/
    services/operator/

MongoDB-specific operations must remain in this module.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId
from pydantic import BaseModel, Field

from config.db_config import player_collection
from config.models.enums import PlayerStatus


# ============================================================================
# PLAYER MODEL
# ============================================================================


class PlayerModel(BaseModel):
    """
    Persistence model representing a player belonging to an operator.

    A player is scoped to an operator. The same external player ID may
    therefore exist under different operators without creating a conflict.

    Example:

        Operator A
            external_player_id = "player_123"

        Operator B
            external_player_id = "player_123"

    These represent two different platform player records because the
    operator context is different.

    Attributes:
        id:
            Internal MongoDB player identifier.

        operator_id:
            Internal identifier of the operator that owns the player.

        external_player_id:
            Player identifier supplied by the external operator.

        username:
            Optional display name supplied by the operator.

        currency:
            Player's active game currency.

        status:
            Current player status.

        metadata:
            Additional non-sensitive player information.

        created_at:
            Timestamp when the player record was created.

        updated_at:
            Timestamp when the player record was last updated.
    """

    id: Optional[str] = Field(
        default=None,
        description="Internal MongoDB player identifier.",
    )

    operator_id: str = Field(
        ...,
        min_length=1,
        description="Internal operator identifier.",
    )

    external_player_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Player identifier provided by the operator.",
    )

    username: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional player display name.",
    )

    currency: str = Field(
        ...,
        min_length=3,
        max_length=10,
        description="Currency used by the player.",
    )

    status: PlayerStatus = Field(
        default=PlayerStatus.ACTIVE,
        description="Current player status.",
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional non-sensitive player metadata.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ============================================================================
# PLAYER REPOSITORY
# ============================================================================


class PlayerRepository:
    """
    Repository responsible for player persistence.

    This class contains database operations only.

    It must not contain:

        - Wallet business logic.
        - Betting rules.
        - Game logic.
        - Transaction processing.
        - Adapter selection.
        - Operator validation rules.
        - Authentication logic.

    Those responsibilities belong to their respective service layers.
    """

    # ========================================================================
    # CREATE
    # ========================================================================

    @staticmethod
    async def create(
        data: Dict[str, Any],
    ) -> str:
        """
        Create a new player record.

        Args:
            data:
                Player document to persist.

        Returns:
            str:
                MongoDB ObjectId of the created player.
        """

        now = datetime.now(timezone.utc)

        data["created_at"] = now
        data["updated_at"] = now

        result = await player_collection.insert_one(data)

        return str(result.inserted_id)

    # ========================================================================
    # GET BY ID
    # ========================================================================

    @staticmethod
    async def get_by_id(
        player_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a player using the internal player ID.

        Args:
            player_id:
                MongoDB ObjectId represented as a string.

        Returns:
            Optional[Dict[str, Any]]:
                Player document if found, otherwise None.
        """

        if not ObjectId.is_valid(player_id):
            return None

        return await player_collection.find_one(
            {
                "_id": ObjectId(player_id),
            }
        )

    # ========================================================================
    # GET PLAYER BY OPERATOR + EXTERNAL ID
    # ========================================================================

    @staticmethod
    async def get_by_external_id(
        operator_id: str,
        external_player_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a player using the operator and external player ID.

        The operator ID is intentionally part of the query.

        This prevents the same external player identifier from being
        incorrectly resolved across different operators.

        Args:
            operator_id:
                Internal operator identifier.

            external_player_id:
                Player identifier supplied by the operator.

        Returns:
            Optional[Dict[str, Any]]:
                Player document if found, otherwise None.
        """

        return await player_collection.find_one(
            {
                "operator_id": operator_id,
                "external_player_id": external_player_id,
            }
        )

    # ========================================================================
    # LIST PLAYERS
    # ========================================================================

    @staticmethod
    async def get_list(
        condition: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve a paginated list of players.

        Args:
            condition:
                MongoDB filter condition.

            skip:
                Number of records to skip.

            limit:
                Maximum number of records to return.

        Returns:
            Tuple[List[Dict[str, Any]], int]:
                Player documents and total matching count.
        """

        condition = condition or {}

        cursor = (
            player_collection
            .find(condition)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        players = await cursor.to_list(
            length=limit
        )

        total = await player_collection.count_documents(
            condition
        )

        return players, total

    # ========================================================================
    # LIST PLAYERS BY OPERATOR
    # ========================================================================

    @staticmethod
    async def get_by_operator(
        operator_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve players belonging to a specific operator.

        Args:
            operator_id:
                Internal operator identifier.

            skip:
                Number of records to skip.

            limit:
                Maximum number of records to return.

        Returns:
            Tuple[List[Dict[str, Any]], int]:
                Players belonging to the operator and total count.
        """

        condition = {
            "operator_id": operator_id,
        }

        cursor = (
            player_collection
            .find(condition)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        players = await cursor.to_list(
            length=limit
        )

        total = await player_collection.count_documents(
            condition
        )

        return players, total

    # ========================================================================
    # UPDATE
    # ========================================================================

    @staticmethod
    async def update(
        player_id: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Update player information.

        Args:
            player_id:
                Internal MongoDB player identifier.

            data:
                Fields that should be updated.

        Returns:
            bool:
                True when the player was modified,
                otherwise False.
        """

        if not ObjectId.is_valid(player_id):
            return False

        data["updated_at"] = datetime.now(timezone.utc)

        result = await player_collection.update_one(
            {
                "_id": ObjectId(player_id),
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
        player_id: str,
        status: PlayerStatus,
    ) -> bool:
        """
        Update the lifecycle status of a player.

        Args:
            player_id:
                Internal MongoDB player identifier.

            status:
                New player status.

        Returns:
            bool:
                True when the status was modified,
                otherwise False.
        """

        if not ObjectId.is_valid(player_id):
            return False

        result = await player_collection.update_one(
            {
                "_id": ObjectId(player_id),
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
        external_player_id: str,
    ) -> bool:
        """
        Check whether a player already exists for an operator.

        Args:
            operator_id:
                Internal operator identifier.

            external_player_id:
                External player identifier.

        Returns:
            bool:
                True if the player exists, otherwise False.
        """

        player = await player_collection.find_one(
            {
                "operator_id": operator_id,
                "external_player_id": external_player_id,
            },
            {
                "_id": 1,
            },
        )

        return player is not None

    # ========================================================================
    # DELETE
    # ========================================================================

    @staticmethod
    async def delete(
        player_id: str,
    ) -> bool:
        """
        Delete a player record.

        In production, prefer deactivating the player instead of
        permanently deleting the record because historical games and
        transactions must remain traceable.

        Args:
            player_id:
                Internal MongoDB player identifier.

        Returns:
            bool:
                True when the player was deleted,
                otherwise False.
        """

        if not ObjectId.is_valid(player_id):
            return False

        result = await player_collection.delete_one(
            {
                "_id": ObjectId(player_id),
            }
        )

        return result.deleted_count > 0