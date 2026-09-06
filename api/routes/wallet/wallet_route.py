"""
Module: api.routes.wallet.wallet_route

Description:
    HTTP routes for wallet operations.
"""

from fastapi import (
    APIRouter,
    Query,
)

from api.controller.wallet.wallet_controller import (
    debit_wallet,
    get_wallet_balance,
)

from schemas.wallet.wallet_schema import (
    BalanceResponse,
    DebitRequest,
    WalletTransactionResponse,
    WalletRollbackRequest
)

from services.wallet.wallet_service import (
    WalletService,
)

router = APIRouter(
    prefix="/wallets",
    tags=["Wallet"],
)


@router.get(
    "/{operator_id}/balance/{player_id}",
    response_model=BalanceResponse,
)
async def get_wallet_balance_route(
    operator_id: str,
    player_id: str,
    currency: str = Query(
        ...,
        min_length=1,
    ),
):
    """
    Retrieve player wallet balance.
    """

    return await get_wallet_balance(
        operator_id=operator_id,
        player_id=player_id,
        currency=currency,
    )


@router.post(
    "/{operator_id}/debit",
    response_model=WalletTransactionResponse,
)
async def debit_wallet_route(
    operator_id: str,
    payload: DebitRequest,
):
    """
    Debit funds from a player's wallet.
    """

    return await debit_wallet(
        operator_id=operator_id,
        payload=payload,
    )

@router.post(
    "/{operator_id}/rollback",
)
async def rollback_wallet(
    operator_id: str,
    payload: WalletRollbackRequest,
):
    return await WalletService.rollback(
        operator_id=operator_id,
        player_id=payload.player_id,
        amount=payload.amount,
        currency=payload.currency,
        transaction_id=payload.transaction_id,
        original_transaction_id=payload.original_transaction_id
    )