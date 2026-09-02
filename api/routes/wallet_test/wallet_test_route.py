from fastapi import APIRouter

from services.adapter.adapter_factory import (
    AdapterFactory,
)


router = APIRouter(
    prefix="/wallet-test",
    tags=["Wallet Test"],
)


@router.get(
    "/{operator_id}/balance/{player_id}",
)
async def get_balance(
    operator_id: str,
    player_id: str,
):
    wallet_adapter = (
        await AdapterFactory.get_wallet_adapter(
            operator_id
        )
    )

    return await wallet_adapter.get_balance(
        player_id=player_id,
        currency="INR",
    )

@router.post(
    "/{operator_id}/debit",
)
async def debit_wallet(
    operator_id: str,
    player_id: str,
    amount: float,
):
    wallet_adapter = (
        await AdapterFactory.get_wallet_adapter(
            operator_id
        )
    )

    return await wallet_adapter.debit(
        player_id=player_id,
        amount=amount,
        currency="INR",
        transaction_id="test_transaction_001",
    )

