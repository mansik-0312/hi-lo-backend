"""
Module: schemas.wallet.wallet_schema

Description:
    Request and response schemas for wallet APIs.
"""

from decimal import Decimal
from typing import Any

from pydantic import (
    BaseModel,
    Field,
)


class BalanceResponse(BaseModel):
    """
    Response returned when retrieving
    a player's wallet balance.
    """

    player_id: str

    currency: str

    balance: Decimal


class DebitRequest(BaseModel):
    """
    Request schema for debiting funds
    from a player's wallet.
    """

    player_id: str = Field(
        ...,
        min_length=1,
    )

    amount: Decimal = Field(
        ...,
        gt=0,
    )

    currency: str = Field(
        ...,
        min_length=1,
    )

    transaction_id: str = Field(
        ...,
        min_length=1,
    )


class WalletTransactionResponse(BaseModel):
    """
    Response returned after a wallet
    transaction.
    """

    transaction_id: str

    player_id: str

    currency: str

    amount: Decimal

    balance: Decimal

    status: str


class WalletRollbackRequest(BaseModel):

    player_id: str

    amount: Decimal

    currency: str

    transaction_id: str

    original_transaction_id: str