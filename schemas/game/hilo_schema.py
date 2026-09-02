"""
Module: schemas.game.hilo_schema

Description:
    Pydantic request and response schemas for the Hi-Lo game APIs.

This module contains API contracts only.
Business logic and database operations must not be implemented here.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class HiLoPrediction(str):
    """
    Supported Hi-Lo player predictions.
    """

    HIGHER = "higher"
    LOWER = "lower"

class StartGameRequest(BaseModel):
    """
    Request schema for starting a new Hi-Lo game.
    """

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=10,
    )

class CardResponse(BaseModel):
    """
    Public representation of a playing card.

    The backend exposes only information that the frontend needs
    to render the card.
    """

    rank: str
    suit: str
    value: int


class StartGameResponse(BaseModel):
    """
    Response returned when a Hi-Lo game is started.
    """

    game_id: str

    status: str

    current_card: CardResponse

    balance: Decimal


class PlaceBetRequest(BaseModel):
    """
    Request schema for placing a Hi-Lo prediction.

    Attributes:
        bet_amount:
            Amount wagered by the player.

        prediction:
            Prediction for the next card.
            Must be either "higher" or "lower".
    """

    bet_amount: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
    )

    prediction: str

    @field_validator("prediction")
    @classmethod
    def validate_prediction(
        cls,
        value: str,
    ) -> str:
        """
        Validate the player's Higher/Lower prediction.
        """

        value = value.lower().strip()

        allowed_predictions = {
            "higher",
            "lower",
        }

        if value not in allowed_predictions:
            raise ValueError(
                "Prediction must be either 'higher' or 'lower'."
            )

        return value


class RoundResponse(BaseModel):
    """
    Public response representation of a completed or pending round.
    """

    round_id: str

    game_id: str

    round_number: int

    bet_amount: Decimal

    prediction: Optional[str] = None

    previous_card: Optional[CardResponse] = None

    next_card: Optional[CardResponse] = None

    result: Optional[str] = None

    payout: Decimal

    status: str


class PlayRoundResponse(BaseModel):
    """
    Response returned after the player makes a Higher/Lower prediction.
    """

    game_id: str

    round: RoundResponse

    current_card: CardResponse

    balance: Decimal

    game_status: str


class GameStateResponse(BaseModel):
    """
    Response containing the current state of a Hi-Lo game.
    """

    game_id: str

    status: str

    current_card: Optional[CardResponse] = None

    balance: Decimal

    current_round_id: Optional[str] = None


class RoundHistoryResponse(BaseModel):
    """
    Response containing the player's Hi-Lo round history.
    """

    rounds: List[RoundResponse]

    total: int

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, List

from pydantic import BaseModel


class RoundResponse(BaseModel):
    round_id: str
    game_id: str
    player_id: str
    round_number: int
    bet_amount: Decimal
    prediction: Optional[str] = None
    previous_card: Optional[Dict[str, Any]] = None
    next_card: Optional[Dict[str, Any]] = None
    result: Optional[str] = None
    payout: Decimal
    status: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class GameRoundsResponse(BaseModel):
    game_id: str
    rounds: List[RoundResponse]
    total: int


class PlayerRoundsResponse(BaseModel):
    player_id: str
    rounds: List[RoundResponse]
    total: int