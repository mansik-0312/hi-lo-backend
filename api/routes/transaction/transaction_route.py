"""
Module: api.routes.transaction.transaction_route

Description:
    HTTP routes for transaction retrieval.
"""

from fastapi import APIRouter

from api.controller.transaction.transaction_controller import (
    get_transaction,
    get_game_transactions,
)

from schemas.transaction.transaction_schema import (
    TransactionResponse,
)


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
async def get_transaction_route(
    transaction_id: str,
):
    """
    Retrieve a transaction.
    """

    return await get_transaction(transaction_id)


@router.get(
    "/game/{game_id}",
    response_model=list[TransactionResponse],
)
async def get_game_transactions_route(
    game_id: str,
):
    """
    Retrieve transactions associated with a game.
    """

    return await get_game_transactions(game_id) 