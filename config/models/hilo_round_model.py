"""
Module: config.models.hilo_round_model

Description:
    MongoDB persistence model and database operations for individual
    Hi-Lo game rounds.

Responsibilities:
    - Define the Hi-Lo round data structure.
    - Create round records.
    - Retrieve round records.
    - Update round records.
    - Retrieve round history.

Business rules and card calculation must remain in the
service/engine layers.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.decimal128 import Decimal128
from pydantic import BaseModel, Field

from config.db_config import hilo_round_collection
from config.models.hilo_game_model import HiLoGameRepository

from config.db_config import hilo_game_collection


class HiLoRoundModel(BaseModel):
    """
    Data model representing a single Hi-Lo game round.
    """

    id: Optional[str] = Field(default=None)

    game_id: str

    player_id: str

    round_number: int

    bet_amount: Decimal = Decimal("0.00")

    prediction: Optional[str] = None

    previous_card: Optional[Dict[str, Any]] = None

    next_card: Optional[Dict[str, Any]] = None

    result: Optional[str] = None

    payout: Decimal = Decimal("0.00")

    status: str = "pending"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    completed_at: Optional[datetime] = None


class HiLoRoundRepository:
    """
    Repository responsible for MongoDB persistence of Hi-Lo rounds.

    Decimal values are converted to MongoDB Decimal128 before writes.
    """

    # ---------------------------------------------------------
    # INTERNAL HELPERS
    # ---------------------------------------------------------

    @staticmethod
    def _decimal_to_decimal128(
        value: Any,
    ) -> Any:
        """
        Convert Python Decimal values to MongoDB Decimal128.

        Other values are returned unchanged.
        """

        if isinstance(value, Decimal):
            return Decimal128(str(value))

        return value

    @staticmethod
    def _decimal128_to_decimal(
        value: Any,
    ) -> Any:
        """
        Convert MongoDB Decimal128 values to Python Decimal.

        Other values are returned unchanged.
        """

        if isinstance(value, Decimal128):
            return value.to_decimal()

        return value

    @classmethod
    def _prepare_for_mongo(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Prepare a dictionary for MongoDB.

        Converts all Decimal values recursively to Decimal128.
        """

        prepared = {}

        for key, value in data.items():

            if isinstance(value, Decimal):
                prepared[key] = Decimal128(str(value))

            elif isinstance(value, dict):
                prepared[key] = cls._prepare_for_mongo(value)

            elif isinstance(value, list):
                prepared[key] = [
                    cls._prepare_value(item)
                    for item in value
                ]

            else:
                prepared[key] = value

        return prepared

    @classmethod
    def _prepare_value(
        cls,
        value: Any,
    ) -> Any:
        """
        Recursively prepare a value for MongoDB.
        """

        if isinstance(value, Decimal):
            return Decimal128(str(value))

        if isinstance(value, dict):
            return cls._prepare_for_mongo(value)

        if isinstance(value, list):
            return [
                cls._prepare_value(item)
                for item in value
            ]

        return value

    @classmethod
    def _deserialize_document(
        cls,
        document: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Convert MongoDB-specific values into API-friendly values.
        """

        if not document:
            return None

        document = document.copy()

        for key, value in document.items():

            if isinstance(value, Decimal128):
                document[key] = value.to_decimal()

            elif isinstance(value, dict):
                document[key] = cls._deserialize_document(
                    value
                )

            elif isinstance(value, list):
                document[key] = [
                    cls._deserialize_value(item)
                    for item in value
                ]

        if "_id" in document:
            document["round_id"] = str(
                document.pop("_id")
            )

        return document

    @classmethod
    def _deserialize_value(
        cls,
        value: Any,
    ) -> Any:

        if isinstance(value, Decimal128):
            return value.to_decimal()

        if isinstance(value, dict):
            return cls._deserialize_document(value)

        if isinstance(value, list):
            return [
                cls._deserialize_value(item)
                for item in value
            ]

        return value

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    @classmethod
    async def create_round(
        cls,
        round_data: Dict[str, Any],
    ) -> str:
        """
        Create a new Hi-Lo round.

        Decimal values are converted to Decimal128 before
        inserting into MongoDB.
        """

        round_data = cls._prepare_for_mongo(
            round_data.copy()
        )

        result = await hilo_round_collection.insert_one(
            round_data
        )

        return str(result.inserted_id)

    # ---------------------------------------------------------
    # GET BY ID
    # ---------------------------------------------------------

    @classmethod
    async def get_round_by_id(
        cls,
        round_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a round by its identifier.
        """

        if not ObjectId.is_valid(round_id):
            return None

        document = await hilo_round_collection.find_one(
            {
                "_id": ObjectId(round_id),
            }
        )

        return cls._deserialize_document(
            document
        )

    # ---------------------------------------------------------
    # GET GAME ROUND
    # ---------------------------------------------------------

    @classmethod
    async def get_game_round(
        cls,
        round_id: str,
        game_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a round belonging to a specific game.
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

    # ---------------------------------------------------------
    # GET GAME ROUNDS
    # ---------------------------------------------------------

    @classmethod
    async def get_game_rounds(
        cls,
        game_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all rounds belonging to a game.

        Newest rounds are returned first.
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

    # ---------------------------------------------------------
    # GET PLAYER ROUNDS
    # ---------------------------------------------------------

    @classmethod
    async def get_player_rounds(
        cls,
        player_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve round history for a player.
        """

        cursor = (
            hilo_round_collection
            .find(
                {
                    "player_id": player_id,
                }
            )
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

        return [
            cls._deserialize_document(document)
            for document in documents
        ]

    # ---------------------------------------------------------
    # UPDATE ROUND
    # ---------------------------------------------------------

    @staticmethod
    async def update_game(
        game_id: str,
        update_data: Dict[str, Any],
    ) -> bool:
        """
        Update a Hi-Lo game.

        Decimal values are converted to MongoDB Decimal128
        before persistence.
        """

        if not ObjectId.is_valid(game_id):
            return False

        update_data = (
            HiLoGameRepository._prepare_for_mongo(
                update_data.copy()
            )
        )

        result = await hilo_game_collection.update_one(
            {
                "_id": ObjectId(game_id),
            },
            {
                "$set": update_data,
            },
        )

        return result.modified_count > 0
    # ---------------------------------------------------------
    # COMPLETE ROUND
    # ---------------------------------------------------------

    @classmethod
    async def complete_round(
        cls,
        round_id: str,
        update_data: Dict[str, Any],
    ) -> bool:
        """
        Mark a round as completed.

        Decimal values are converted to Decimal128 before
        writing to MongoDB.
        """

        if not ObjectId.is_valid(round_id):
            return False

        update_data = update_data.copy()

        update_data["status"] = "completed"

        update_data["completed_at"] = (
            datetime.now(timezone.utc)
        )

        update_data = cls._prepare_for_mongo(
            update_data
        )

        result = await hilo_round_collection.update_one(
            {
                "_id": ObjectId(round_id),
                "status": "pending",
            },
            {
                "$set": update_data,
            },
        )

        return result.modified_count > 0

    # ---------------------------------------------------------
    # GET ACTIVE ROUND
    # ---------------------------------------------------------

    @classmethod
    async def get_active_round(
        cls,
        game_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve the currently pending round for a game.
        """

        document = await hilo_round_collection.find_one(
            {
                "game_id": game_id,
                "status": "pending",
            }
        )

        return cls._deserialize_document(
            document
        )