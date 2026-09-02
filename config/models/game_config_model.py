"""
Module: config.models.game_config_model

Description:
    Persistence model and repository operations for Hi-Lo game
    configuration.

The game configuration is maintained per operator and game code.
This allows the same Hi-Lo game engine to be deployed across
multiple casino/iGaming operators without changing application code.

Responsibilities:
    - Define the persisted game configuration structure.
    - Store and retrieve operator-specific game configuration.
    - Update configuration records.
    - Provide database-level lookup operations.

Business rules such as:
    - Bet validation.
    - Win/loss calculation.
    - Payout calculation.
    - Higher/lower card comparison.
    - Tie handling.
    - Deck management.

must remain in the service/engine layer.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from config.db_config import game_config_collection


class GameConfigurationModel(BaseModel):
    """
    Represents the complete configuration of a game for an operator.

    A separate configuration document is maintained for each
    operator/game combination. This allows the same game engine
    to support different casino operators with different rules.

    Attributes:
        id:
            MongoDB document identifier.

        game_code:
            Unique identifier of the game.

        operator_id:
            Identifier of the casino/operator using the game.

        currency:
            Default currency supported by this configuration.

        min_bet:
            Minimum amount a player can bet.

        max_bet:
            Maximum amount a player can bet.

        payout_multiplier:
            Multiplier applied when the player wins.

        allow_equal:
            Determines whether equal-rank cards are permitted.

        equal_card_result:
            Result when the next card has the same rank.

        deck_type:
            Type of deck used by the game.

        cards_per_deck:
            Number of cards contained in one deck.

        decks_count:
            Number of decks used for a game session.

        reshuffle_threshold:
            Percentage/threshold at which the deck should be
            reshuffled.

        allow_higher:
            Whether the Higher prediction is enabled.

        allow_lower:
            Whether the Lower prediction is enabled.

        house_edge:
            Configurable house edge for future payout calculations.

        max_payout:
            Maximum payout permitted for a winning round.

        configuration:
            Additional operator-specific configuration.

        ui_configuration:
            Frontend/game presentation configuration.

        status:
            Configuration status.

        version:
            Configuration version. Useful when configurations
            change while historical games must remain auditable.

        created_at:
            Configuration creation timestamp.

        updated_at:
            Last configuration update timestamp.
    """

    id: Optional[str] = None

    game_code: str = "hi_lo"

    operator_id: str

    currency: str

    # ------------------------------------------------------------------
    # Betting configuration
    # ------------------------------------------------------------------

    min_bet: Decimal

    max_bet: Decimal

    payout_multiplier: Decimal = Decimal("2.00")

    max_payout: Optional[Decimal] = None

    house_edge: Decimal = Decimal("0.00")

    # ------------------------------------------------------------------
    # Hi-Lo game rules
    # ------------------------------------------------------------------

    allow_higher: bool = True

    allow_lower: bool = True

    allow_equal: bool = True

    equal_card_result: str = "push"

    # ------------------------------------------------------------------
    # Deck configuration
    # ------------------------------------------------------------------

    deck_type: str = "standard_52"

    cards_per_deck: int = 52

    decks_count: int = 1

    reshuffle_threshold: int = 5

    # ------------------------------------------------------------------
    # Generic game configuration
    # ------------------------------------------------------------------

    configuration: Dict[str, Any] = Field(
        default_factory=dict
    )

    # ------------------------------------------------------------------
    # Frontend/UI configuration
    #
    # This is intentionally generic so casino-specific branding,
    # labels, colors, sounds, animations, etc. can be configured
    # without changing backend code.
    # ------------------------------------------------------------------

    ui_configuration: Dict[str, Any] = Field(
        default_factory=dict
    )

    # ------------------------------------------------------------------
    # Configuration lifecycle
    # ------------------------------------------------------------------

    status: str = "active"

    version: int = 1

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class GameConfigurationRepository:
    """
    Repository responsible for Hi-Lo game configuration persistence.

    This class contains MongoDB-specific operations only.

    Business logic must not be implemented here.
    """

    @staticmethod
    async def create(
        data: Dict[str, Any],
    ) -> str:
        """
        Create a new game configuration.

        Args:
            data:
                Game configuration document.

        Returns:
            str:
                MongoDB identifier of the created configuration.
        """

        now = datetime.now(timezone.utc)

        data["created_at"] = now
        data["updated_at"] = now

        result = await game_config_collection.insert_one(
            data
        )

        return str(result.inserted_id)

    @staticmethod
    async def get_by_id(
        configuration_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a game configuration by MongoDB ID.

        Args:
            configuration_id:
                MongoDB ObjectId represented as a string.

        Returns:
            Optional[Dict[str, Any]]:
                Configuration document if found, otherwise None.
        """

        if not ObjectId.is_valid(configuration_id):
            return None

        return await game_config_collection.find_one(
            {
                "_id": ObjectId(configuration_id)
            }
        )

    @staticmethod
    async def get_for_operator(
        operator_id: str,
        game_code: str = "hi_lo",
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve the active configuration for an operator and game.

        Args:
            operator_id:
                Operator identifier.

            game_code:
                Game identifier.

        Returns:
            Optional[Dict[str, Any]]:
                Active configuration if found, otherwise None.
        """

        return await game_config_collection.find_one(
            {
                "operator_id": operator_id,
                "game_code": game_code,
                "status": "active",
            }
        )

    @staticmethod
    async def get_all_for_operator(
        operator_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all game configurations belonging to an operator.

        Args:
            operator_id:
                Operator identifier.

        Returns:
            List[Dict[str, Any]]:
                List of configuration documents.
        """

        cursor = game_config_collection.find(
            {
                "operator_id": operator_id
            }
        ).sort(
            "created_at",
            -1,
        )

        return await cursor.to_list(
            length=None
        )

    @staticmethod
    async def get_active_by_game_code(
        game_code: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve active configurations for a game across operators.

        Args:
            game_code:
                Game identifier.

        Returns:
            List[Dict[str, Any]]:
                Active configurations.
        """

        cursor = game_config_collection.find(
            {
                "game_code": game_code,
                "status": "active",
            }
        )

        return await cursor.to_list(
            length=None
        )

    @staticmethod
    async def update(
        configuration_id: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Update an existing game configuration.

        Args:
            configuration_id:
                MongoDB ObjectId represented as a string.

            data:
                Fields that should be updated.

        Returns:
            bool:
                True if the document was modified,
                otherwise False.
        """

        if not ObjectId.is_valid(configuration_id):
            return False

        data["updated_at"] = datetime.now(
            timezone.utc
        )

        result = await game_config_collection.update_one(
            {
                "_id": ObjectId(configuration_id)
            },
            {
                "$set": data
            },
        )

        return result.modified_count > 0

    @staticmethod
    async def activate(
        configuration_id: str,
    ) -> bool:
        """
        Activate a game configuration.

        Args:
            configuration_id:
                Configuration identifier.

        Returns:
            bool:
                True if the configuration was activated.
        """

        return await GameConfigurationRepository.update(
            configuration_id,
            {
                "status": "active"
            },
        )

    @staticmethod
    async def deactivate(
        configuration_id: str,
    ) -> bool:
        """
        Deactivate a game configuration.

        Args:
            configuration_id:
                Configuration identifier.

        Returns:
            bool:
                True if the configuration was deactivated.
        """

        return await GameConfigurationRepository.update(
            configuration_id,
            {
                "status": "inactive"
            },
        )