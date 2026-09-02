"""
Module: schemas.game.game_config_schema

Description:
    API schemas for Hi-Lo game configuration.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class GameConfigurationCreateRequest(BaseModel):
    """
    Request schema for creating a game configuration.
    """

    operator_id: str

    game_code: str = "hi_lo"

    currency: str = Field(
        min_length=3,
        max_length=10,
    )

    min_bet: Decimal = Field(
        gt=0
    )

    max_bet: Decimal = Field(
        gt=0
    )

    payout_multiplier: Decimal = Field(
        gt=0
    )

    allow_equal: bool = True

    equal_card_result: str = "push"

    deck_type: str = "standard_52"

    cards_per_deck: int = Field(
        default=52,
        gt=0,
    )

    configuration: Dict[str, Any] = Field(
        default_factory=dict
    )


class GameConfigurationUpdateRequest(BaseModel):
    """
    Request schema for updating game configuration.
    """

    min_bet: Optional[Decimal] = Field(
        default=None,
        gt=0,
    )

    max_bet: Optional[Decimal] = Field(
        default=None,
        gt=0,
    )

    payout_multiplier: Optional[Decimal] = Field(
        default=None,
        gt=0,
    )

    allow_equal: Optional[bool] = None

    equal_card_result: Optional[str] = None

    deck_type: Optional[str] = None

    cards_per_deck: Optional[int] = Field(
        default=None,
        gt=0,
    )

    configuration: Optional[Dict[str, Any]] = None


class GameConfigurationResponse(BaseModel):
    """
    Game configuration response.
    """

    id: str

    operator_id: str

    game_code: str

    currency: str

    min_bet: Decimal

    max_bet: Decimal

    payout_multiplier: Decimal

    allow_equal: bool

    equal_card_result: str

    deck_type: str

    cards_per_deck: int

    configuration: Dict[str, Any]

    status: str

    created_at: datetime

    updated_at: datetime