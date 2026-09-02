"""
Module: config.models.hilo_round_model

Description:
    MongoDB persistence model and repository operations for individual
    Hi-Lo game rounds.

A round represents one betting decision within a Hi-Lo game.

A round records:

    - Operator.
    - Player.
    - Game.
    - Round number.
    - Bet amount.
    - Currency.
    - Player prediction.
    - Previous card.
    - Next/revealed card.
    - Result.
    - Payout.
    - Wallet transaction references.
    - Idempotency information.
    - Round lifecycle timestamps.

Responsibilities:
    - Define the Hi-Lo round data structure.
    - Create round records.
    - Retrieve round records.
    - Update round records.
    - Complete rounds.
    - Retrieve game round history.
    - Retrieve player round history.
    - Retrieve operator round history.

Business rules and card calculations must remain in:

    services/game/hilo_engine.py
    services/game/hilo_service.py

Wallet and transaction processing must remain in:

    services/wallet/wallet_service.py
    services/wallet/transaction_service.py

MongoDB-specific operations must remain in this module.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from bson import ObjectId
from bson.decimal128 import Decimal128
from pydantic import BaseModel, Field

from config.db_config import hilo_round_collection
from config.models.enums import (
    Prediction,
    RoundResult,
    RoundStatus,
)


# ============================================================================
# HI-LO ROUND MODEL
# ============================================================================


class HiLoRoundModel(BaseModel):
    """
    Persistence model representing one Hi-Lo betting round.

    A round belongs to exactly one operator, player, and game.

    The complete round result is persisted so historical rounds can be
    audited without depending on transient application state.

    Attributes:
        id:
            Internal MongoDB round identifier.

        operator_id:
            Operator associated with the round.

        game_id:
            Game session associated with the round.

        player_id:
            Player associated with the round.

        round_number:
            Sequential round number inside the game.

        bet_amount:
            Amount wagered by the player.

        currency:
            Currency used for the round.

        prediction:
            Player prediction for the next card.

        previous_card:
            Card visible before the player prediction.

        next_card:
            Card revealed after the prediction.

        result:
            Final result of the round.

        payout:
            Amount credited to the player as winnings.

        status:
            Current lifecycle state of the round.

        bet_transaction_id:
            Transaction created for the bet/debit.

        payout_transaction_id:
            Transaction created for the winnings/credit.

        rollback_transaction_id:
            Transaction created when a previous transaction is reversed.

        idempotency_key:
            Unique request identifier used to prevent duplicate processing.

        metadata:
            Additional non-sensitive round information.

        created_at:
            Timestamp when the round was created.

        completed_at:
            Timestamp when the round completed.

        updated_at:
            Timestamp when the round was last updated.
    """

    id: Optional[str] = Field(
        default=None,
        description="Internal MongoDB round identifier.",
    )

    operator_id: str = Field(
        ...,
        min_length=1,
        description="Operator associated with the round.",
    )

    game_id: str = Field(
        ...,
        min_length=1,
        description="Game session associated with the round.",
    )

    player_id: str = Field(
        ...,
        min_length=1,
        description="Player associated with the round.",
    )

    round_number: int = Field(
        ...,
        ge=1,
        description="Sequential round number inside the game.",
    )

    # ------------------------------------------------------------------------
    # BET
    # ------------------------------------------------------------------------

    bet_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        description="Amount wagered by the player.",
    )

    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=10,
        description="Currency used for the round.",
    )

    # ------------------------------------------------------------------------
    # PREDICTION
    # ------------------------------------------------------------------------

    prediction: Optional[Prediction] = Field(
        default=None,
        description="Player prediction: higher or lower.",
    )

    # ------------------------------------------------------------------------
    # CARDS
    # ------------------------------------------------------------------------

    previous_card: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Card shown before the prediction.",
    )

    next_card: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Card revealed after the prediction.",
    )

    # ------------------------------------------------------------------------
    # RESULT
    # ------------------------------------------------------------------------

    result: Optional[RoundResult] = Field(
        default=None,
        description="Final round result.",
    )

    payout: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        description="Amount paid to the player.",
    )

    status: RoundStatus = Field(
        default=RoundStatus.PENDING,
        description="Current round lifecycle status.",
    )

    # ------------------------------------------------------------------------
    # TRANSACTION REFERENCES
    # ------------------------------------------------------------------------

    bet_transaction_id: Optional[str] = Field(
        default=None,
        description="Transaction ID for the bet debit.",
    )

    payout_transaction_id: Optional[str] = Field(
        default=None,
        description="Transaction ID for the winnings credit.",
    )

    rollback_transaction_id: Optional[str] = Field(
        default=None,
        description="Transaction ID for a rollback.",
    )

    # ------------------------------------------------------------------------
    # IDEMPOTENCY
    # ------------------------------------------------------------------------

    idempotency_key: Optional[str] = Field(
        default=None,
        description="Unique key used to prevent duplicate round processing.",
    )

    # ------------------------------------------------------------------------
    # ADDITIONAL INFORMATION
    # ------------------------------------------------------------------------

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional non-sensitive round metadata.",
    )

    # ------------------------------------------------------------------------
    # TIMESTAMPS
    # ------------------------------------------------------------------------

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    completed_at: Optional[datetime] = None

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    wallet_debit_transaction_id: Optional[str] = None

# ============================================================================
# HI-LO ROUND REPOSITORY
# ============================================================================


class HiLoRoundRepository:
    """
    Repository responsible for Hi-Lo round persistence.

    This repository contains database operations only.

    It must not contain:

        - Card generation.
        - Higher/lower calculations.
        - Win/loss calculations.
        - Payout calculations.
        - Wallet calls.
        - Transaction processing.
        - Adapter selection.
        - Operator business rules.
        - Authentication logic.
    """

    # ========================================================================
    # MONGO SERIALIZATION
    # ========================================================================

    @staticmethod
    def _decimal_to_decimal128(
        value: Any,
    ) -> Any:
        """
        Convert a Python Decimal to MongoDB Decimal128.

        Args:
            value:
                Value to convert.

        Returns:
            Decimal128 for Decimal values, otherwise the original value.
        """

        if isinstance(value, Decimal):
            return Decimal128(str(value))

        return value

    @classmethod
    def _prepare_value(
        cls,
        value: Any,
    ) -> Any:
        """
        Recursively prepare a value for MongoDB.

        Decimal values are converted to Decimal128.

        Args:
            value:
                Value to prepare.

        Returns:
            MongoDB-compatible value.
        """

        if isinstance(value, Decimal):
            return Decimal128(str(value))

        if isinstance(value, dict):
            return {
                key: cls._prepare_value(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [
                cls._prepare_value(item)
                for item in value
            ]

        return value

    @classmethod
    def _prepare_for_mongo(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Prepare a dictionary for MongoDB persistence.

        Args:
            data:
                Dictionary to prepare.

        Returns:
            MongoDB-compatible dictionary.
        """

        return {
            key: cls._prepare_value(value)
            for key, value in data.items()
        }

    @classmethod
    def _deserialize_value(
        cls,
        value: Any,
    ) -> Any:
        """
        Recursively convert MongoDB values into Python values.

        Args:
            value:
                MongoDB value.

        Returns:
            Deserialized Python value.
        """

        if isinstance(value, Decimal128):
            return value.to_decimal()

        if isinstance(value, dict):
            return {
                key: cls._deserialize_value(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [
                cls._deserialize_value(item)
                for item in value
            ]

        return value

    @classmethod
    def _deserialize_document(
        cls,
        document: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Convert a MongoDB document into an application-friendly dictionary.

        Args:
            document:
                MongoDB document.

        Returns:
            Deserialized document or None.
        """

        if not document:
            return None

        document = cls._deserialize_value(
            document.copy()
        )

        if "_id" in document:
            document["round_id"] = str(
                document.pop("_id")
            )

        return document

    # ========================================================================
    # CREATE
    # ========================================================================

    @classmethod
    async def create_round(
        cls,
        round_data: Dict[str, Any],
    ) -> str:
        """
        Create a new Hi-Lo round.

        Args:
            round_data:
                Round document to persist.

        Returns:
            str:
                Created round MongoDB identifier.
        """

        now = datetime.now(timezone.utc)

        round_data = round_data.copy()

        round_data.setdefault(
            "created_at",
            now,
        )

        round_data.setdefault(
            "updated_at",
            now,
        )

        round_data = cls._prepare_for_mongo(
            round_data
        )

        result = await hilo_round_collection.insert_one(
            round_data
        )

        return str(result.inserted_id)

    # ========================================================================
    # GET BY ID
    # ========================================================================

    @classmethod
    async def get_round_by_id(
        cls,
        round_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a round by ID.

        Args:
            round_id:
                MongoDB round identifier.

        Returns:
            Round document if found, otherwise None.
        """

        if not ObjectId.is_valid(round_id):
            return None

        document = await hilo_round_collection.find_one(
            {
                "_id": ObjectId(round_id)
            }
        )

        return cls._deserialize_document(
            document
        )

    # ========================================================================
    # GET GAME ROUND
    # ========================================================================

    @classmethod
    async def get_game_round(
        cls,
        round_id: str,
        game_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a round belonging to a specific game.

        Args:
            round_id:
                Round identifier.

            game_id:
                Game identifier.

        Returns:
            Round document if found, otherwise None.
        """

        if not ObjectId.is_valid(round_id):
            return None

        document = await hilo_round_collection.find_one(
            {
                "_id": ObjectId(round_id),
                "game_id": game_id,
            }
        )

        return cls._deserialize_document(
            document
        )

    # ========================================================================
    # GET GAME ROUNDS
    # ========================================================================

    @classmethod
    async def get_game_rounds(
        cls,
        game_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all rounds belonging to a game.

        Rounds are returned newest first.

        Args:
            game_id:
                Game identifier.

        Returns:
            List of round documents.
        """

        cursor = (
            hilo_round_collection
            .find(
                {
                    "game_id": game_id,
                }
            )
            .sort(
                "round_number",
                -1,
            )
        )

        documents = await cursor.to_list(
            length=None
        )

        return [
            cls._deserialize_document(document)
            for document in documents
        ]

    # ========================================================================
    # GET PLAYER ROUNDS
    # ========================================================================

    @classmethod
    async def get_player_rounds(
        cls,
        player_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve paginated round history for a player.

        Args:
            player_id:
                Player identifier.

            skip:
                Number of records to skip.

            limit:
                Maximum number of records.

        Returns:
            Tuple containing:
                - Round history.
                - Total number of matching rounds.
        """

        condition = {
            "player_id": player_id,
        }

        cursor = (
            hilo_round_collection
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

        total = await hilo_round_collection.count_documents(
            condition
        )

        rounds = [
            cls._deserialize_document(document)
            for document in documents
        ]

        return rounds, total

    # ========================================================================
    # GET OPERATOR ROUNDS
    # ========================================================================

    @classmethod
    async def get_operator_rounds(
        cls,
        operator_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve paginated round history for an operator.

        Args:
            operator_id:
                Operator identifier.

            skip:
                Number of records to skip.

            limit:
                Maximum number of records.

        Returns:
            Tuple containing:
                - Round history.
                - Total number of matching rounds.
        """

        condition = {
            "operator_id": operator_id,
        }

        cursor = (
            hilo_round_collection
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

        total = await hilo_round_collection.count_documents(
            condition
        )

        rounds = [
            cls._deserialize_document(document)
            for document in documents
        ]

        return rounds, total

    # ========================================================================
    # GET ACTIVE ROUND
    # ========================================================================

    @classmethod
    async def get_active_round(
        cls,
        game_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve the currently active round for a game.

        Args:
            game_id:
                Game identifier.

        Returns:
            Active round if one exists, otherwise None.
        """

        document = await hilo_round_collection.find_one(
            {
                "game_id": game_id,
                "status": {
                    "$in": [
                        RoundStatus.PENDING.value,
                        RoundStatus.ACTIVE.value,
                    ]
                },
            },
            sort=[
                ("created_at", -1),
            ],
        )

        return cls._deserialize_document(
            document
        )

    # ========================================================================
    # GET BY IDEMPOTENCY KEY
    # ========================================================================

    @classmethod
    async def get_by_idempotency_key(
        cls,
        idempotency_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an existing round by its idempotency key.

        This prevents duplicate processing when the same game request
        is retried by an operator or client.

        Args:
            idempotency_key:
                Unique request identifier.

        Returns:
            Existing round if found, otherwise None.
        """

        document = await hilo_round_collection.find_one(
            {
                "idempotency_key": idempotency_key,
            }
        )

        return cls._deserialize_document(
            document
        )

    # ========================================================================
    # UPDATE ROUND
    # ========================================================================

    @classmethod
    async def update_round(
        cls,
        round_id: str,
        update_data: Dict[str, Any],
    ) -> bool:
        """
        Update an existing round.

        Args:
            round_id:
                MongoDB round identifier.

            update_data:
                Fields to update.

        Returns:
            True if the document was modified,
            otherwise False.
        """

        if not ObjectId.is_valid(round_id):
            return False

        update_data = update_data.copy()

        update_data["updated_at"] = (
            datetime.now(timezone.utc)
        )

        update_data = cls._prepare_for_mongo(
            update_data
        )

        result = await hilo_round_collection.update_one(
            {
                "_id": ObjectId(round_id),
            },
            {
                "$set": update_data,
            },
        )

        return result.modified_count > 0

    # ========================================================================
    # COMPLETE ROUND
    # ========================================================================

    @classmethod
    async def complete_round(
        cls,
        round_id: str,
        update_data: Dict[str, Any],
    ) -> bool:
        """
        Complete a Hi-Lo round.

        The repository does not calculate the result. The service layer
        must provide the final status, result, payout, and card data.

        The conditional status query prevents an already-completed round
        from being processed again.

        Args:
            round_id:
                MongoDB round identifier.

            update_data:
                Final round data.

        Returns:
            True if the round was successfully completed.
        """

        if not ObjectId.is_valid(round_id):
            return False

        update_data = update_data.copy()

        now = datetime.now(timezone.utc)

        update_data["completed_at"] = now
        update_data["updated_at"] = now

        update_data = cls._prepare_for_mongo(
            update_data
        )

        result = await hilo_round_collection.update_one(
            {
                "_id": ObjectId(round_id),
                "status": {
                    "$in": [
                        RoundStatus.PENDING.value,
                        RoundStatus.ACTIVE.value,
                    ]
                },
            },
            {
                "$set": update_data,
            },
        )

        return result.modified_count > 0

    # ========================================================================
    # UPDATE RESULT
    # ========================================================================

    @classmethod
    async def update_result(
        cls,
        round_id: str,
        result: RoundResult,
        payout: Decimal,
        next_card: Dict[str, Any],
        status: RoundStatus,
        payout_transaction_id: Optional[str] = None,
    ) -> bool:
        """
        Persist the calculated result of a round.

        The service layer is responsible for calculating whether the
        player won/lost/pushed and determining the payout.

        This method only persists that result.

        Args:
            round_id:
                Round identifier.

            result:
                Calculated round result.

            payout:
                Calculated payout.

            next_card:
                Revealed next card.

            status:
                Final round status.

            payout_transaction_id:
                Optional payout transaction identifier.

        Returns:
            True if the round was updated.
        """

        if not ObjectId.is_valid(round_id):
            return False

        now = datetime.now(timezone.utc)

        update_data: Dict[str, Any] = {
            "result": result.value,
            "payout": payout,
            "next_card": next_card,
            "status": status.value,
            "completed_at": now,
            "updated_at": now,
        }

        if payout_transaction_id:
            update_data[
                "payout_transaction_id"
            ] = payout_transaction_id

        update_data = cls._prepare_for_mongo(
            update_data
        )

        result_update = await hilo_round_collection.update_one(
            {
                "_id": ObjectId(round_id),
                "status": {
                    "$in": [
                        RoundStatus.PENDING.value,
                        RoundStatus.ACTIVE.value,
                    ]
                },
            },
            {
                "$set": update_data,
            },
        )

        return result_update.modified_count > 0