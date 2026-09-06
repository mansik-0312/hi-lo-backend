"""
Module: api.controller.wallet.wallet_controller

Description:
    Controller layer for wallet APIs.
"""

import logging

from fastapi import (
    HTTPException,
    status,
)

from schemas.wallet.wallet_schema import (
    BalanceResponse,
    DebitRequest,
    WalletTransactionResponse,
)

from services.wallet.wallet_service import (
    WalletService,
)


logger = logging.getLogger(__name__)


async def get_wallet_balance(
    operator_id: str,
    player_id: str,
    currency: str,
) -> BalanceResponse:
    """
    Retrieve a player's wallet balance.
    """

    try:
        result = await WalletService.get_balance(
            operator_id=operator_id,
            player_id=player_id,
            currency=currency,
        )

        return BalanceResponse(
            **result
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception:

        logger.exception(
            "Unexpected error while retrieving wallet balance."
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to retrieve wallet balance."
            ),
        )


async def debit_wallet(
    operator_id: str,
    payload: DebitRequest,
) -> WalletTransactionResponse:
    """
    Debit funds from a player's wallet.
    """

    try:
        result = await WalletService.debit(
            operator_id=operator_id,
            player_id=payload.player_id,
            amount=payload.amount,
            currency=payload.currency,
            transaction_id=payload.transaction_id,
        )

        return WalletTransactionResponse(
            **result
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception:

        logger.exception(
            "Unexpected error while debiting wallet."
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to debit wallet."
            ),
        )