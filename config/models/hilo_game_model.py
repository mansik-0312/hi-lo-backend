"""
Module: config.models.hilo_game_model

Description:
    MongoDB persistence model and database operations for Hi-Lo games.

The model is responsible only for:
    - Defining the Hi-Lo game data structure.
    - Creating game records.
    - Fetching game records.
    - Updating game records.
    - Managing game persistence in MongoDB.

Business logic must remain in the Hi-Lo service layer.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from bson import ObjectId
from bson.decimal128 import Decimal128
from pydantic import BaseModel, Field

from config.db_config import hilo_game_collection


class HiLoGameModel(BaseModel):
    """
    Data model representing a Hi-Lo game session.
    """

    id: Optional[str] = Field(default=None)

    player_id: str

    status: str = "active"

    current_card: Optional[Dict[str, Any]] = None

    balance: Decimal = Decimal("0.00")

    current_round_id: Optional[str] = None

    round_number: int = 0

    remaining_deck: list[Dict[str, Any]] = Field(
        default_factory=list
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Config:
        arbitrary_types_allowed = True


class HiLoGameRepository:
    """
    Repository responsible for Hi-Lo game persistence.
    """

    # ============================================================
    # INTERNAL SERIALIZATION HELPERS
    # ============================================================

    @staticmethod
    def _prepare_value(
        value: Any,
    ) -> Any:
        """
        Recursively convert Python Decimal values
        to MongoDB Decimal128.
        """

        if isinstance(value, Decimal):
            return Decimal128(str(value))

        if isinstance(value, dict):
            return {
                key: HiLoGameRepository._prepare_value(
                    val
                )
                for key, val in value.items()
            }

        if isinstance(value, list):
            return [
                HiLoGameRepository._prepare_value(item)
                for item in value
            ]

        return value

    @staticmethod
    def _prepare_for_mongo(
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Recursively prepare dictionary data
        for MongoDB.
        """

        return {
            key: HiLoGameRepository._prepare_value(value)
            for key, value in data.items()
        }

    @staticmethod
    def _deserialize_value(
        value: Any,
    ) -> Any:
        """
        Recursively convert MongoDB Decimal128
        values back to Python Decimal.
        """

        if isinstance(value, Decimal128):
            return value.to_decimal()

        if isinstance(value, dict):
            return {
                key: HiLoGameRepository._deserialize_value(
                    val
                )
                for key, val in value.items()
            }

        if isinstance(value, list):
            return [
                HiLoGameRepository._deserialize_value(item)
                for item in value
            ]

        return value

    @staticmethod
    def _deserialize_document(
        document: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Convert a MongoDB document into an API-friendly
        dictionary.
        """

        if not document:
            return None

        document = {
            key: HiLoGameRepository._deserialize_value(value)
            for key, value in document.items()
        }

        if "_id" in document:
            document["game_id"] = str(
                document.pop("_id")
            )

        # Keep Decimal as string for JSON response.
        if isinstance(document.get("balance"), Decimal):
            document["balance"] = str(
                document["balance"]
            )

        return document

    # ============================================================
    # CREATE
    # ============================================================

    @staticmethod
    async def create_game(
        game_data: Dict[str, Any],
    ) -> str:
        """
        Create a new Hi-Lo game in MongoDB.
        """

        document = HiLoGameRepository._prepare_for_mongo(
            game_data.copy()
        )

        result = await hilo_game_collection.insert_one(
            document
        )

        return str(result.inserted_id)

    # ============================================================
    # GET BY ID
    # ============================================================

    @staticmethod
    async def get_game_by_id(
        game_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a Hi-Lo game by its identifier.
        """

        if not ObjectId.is_valid(game_id):
            return None

        document = await hilo_game_collection.find_one(
            {
                "_id": ObjectId(game_id),
            }
        )

        return HiLoGameRepository._deserialize_document(
            document
        )

    # ============================================================
    # GET PLAYER GAME
    # ============================================================

    @staticmethod
    async def get_player_game(
        game_id: str,
        player_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a game belonging to a specific player.
        """

        if not ObjectId.is_valid(game_id):
            return None

        document = await hilo_game_collection.find_one(
            {
                "_id": ObjectId(game_id),
                "player_id": player_id,
            }
        )

        return HiLoGameRepository._deserialize_document(
            document
        )

    # ============================================================
    # UPDATE GAME
    # ============================================================

    @staticmethod
    async def update_game(
        game_id: str,
        update_data: Dict[str, Any],
    ) -> bool:
        """
        Update an existing Hi-Lo game.

        All Decimal values are converted to MongoDB
        Decimal128 before persistence.
        """

        if not ObjectId.is_valid(game_id):
            return False

        update_data = update_data.copy()

        update_data["updated_at"] = datetime.now(
            timezone.utc
        )

        # IMPORTANT:
        # Convert Decimal -> Decimal128 recursively.
        update_data = (
            HiLoGameRepository._prepare_for_mongo(
                update_data
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

    # ============================================================
    # UPDATE GAME IF ACTIVE
    # ============================================================

    @staticmethod
    async def update_game_if_active(
        game_id: str,
        update_data: Dict[str, Any],
    ) -> bool:
        """
        Update a game only when it is currently active.
        """

        if not ObjectId.is_valid(game_id):
            return False

        update_data = update_data.copy()

        update_data["updated_at"] = datetime.now(
            timezone.utc
        )

        # IMPORTANT:
        # Convert Decimal -> Decimal128 recursively.
        update_data = (
            HiLoGameRepository._prepare_for_mongo(
                update_data
            )
        )

        result = await hilo_game_collection.update_one(
            {
                "_id": ObjectId(game_id),
                "status": "active",
            },
            {
                "$set": update_data,
            },
        )

        return result.modified_count > 0

    @staticmethod
    async def get_player_games(
        player_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Dict[str, Any]], int]:
        """
        Retrieve game history for a player.

        Args:
            player_id:
                Player identifier.

            skip:
                Number of records to skip.

            limit:
                Maximum number of records to return.

        Returns:
            A tuple containing:
                - list of game documents
                - total number of games
        """

        total = await hilo_game_collection.count_documents(
            {
                "player_id": player_id,
            }
        )

        cursor = (
            hilo_game_collection
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

        games = await cursor.to_list(
            length=limit
        )

        for game in games:
            game["game_id"] = str(
                game.pop("_id")
            )

            if isinstance(
                game.get("balance"),
                Decimal128,
            ):
                game["balance"] = str(
                    game["balance"]
                )

        return games, total