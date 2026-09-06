"""
Module: schemas.player.player_schema

Description:
    Pydantic schemas for player APIs.

The Hi-Lo platform does not own the complete player account.

The operator remains the source of truth for player identity.

The game platform stores the operator's external player identifier
and game-specific player information.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ============================================================================
# CREATE PLAYER
# ============================================================================


class PlayerCreateRequest(BaseModel):
    """
    Request schema for registering/synchronizing a player.
    """

    operator_id: str = Field(
        ...,
        min_length=1,
    )

    external_player_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Player ID supplied by the operator.",
    )

    username: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    currency: str = Field(
        ...,
        min_length=3,
        max_length=10,
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# UPDATE PLAYER
# ============================================================================


class PlayerUpdateRequest(BaseModel):
    """
    Request schema for updating player information.
    """

    username: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    currency: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=10,
    )

    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# PLAYER RESPONSE
# ============================================================================


class PlayerResponse(BaseModel):
    """
    Public player response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str

    operator_id: str

    external_player_id: str

    username: Optional[str] = None

    currency: str

    status: str

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime

    updated_at: datetime


# ============================================================================
# PLAYER BALANCE
# ============================================================================


class PlayerBalanceResponse(BaseModel):
    """
    Normalized player balance response.

    The balance is obtained from the configured operator wallet
    adapter rather than maintained as the authoritative balance by
    the Hi-Lo game.
    """

    player_id: str

    external_player_id: str

    currency: str

    balance: Decimal

    fetched_at: datetime