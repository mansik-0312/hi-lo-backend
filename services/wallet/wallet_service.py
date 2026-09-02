"""
Module: services.wallet.wallet_service

Description:
    Central service responsible for wallet operations.

The WalletService acts as an abstraction layer between
the game domain and operator-specific wallet adapters.

Game and round services must use WalletService instead
of directly interacting with wallet adapters.
"""

from decimal import Decimal
from typing import Any, Dict

from services.adapter.adapter_factory import (
    AdapterFactory,
)


class WalletService:
    """
    Service responsible for wallet operations.

    The WalletService acts as the bridge between
    game services and operator wallet adapters.
    """

    @staticmethod
    async def get_balance(
        operator_id: str,
        player_id: str,
        currency: str,
    ) -> Dict[str, Any]:
        """
        Retrieve the player's wallet balance.
        """

        adapter = (
            await AdapterFactory.get_wallet_adapter(
                operator_id=operator_id,
            )
        )

        return await adapter.get_balance(
            player_id=player_id,
            currency=currency,
        )

    @staticmethod
    async def debit(
        operator_id: str,
        player_id: str,
        amount: Decimal,
        currency: str,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Debit an amount from the player's wallet.
        """

        adapter = (
            await AdapterFactory.get_wallet_adapter(
                operator_id=operator_id,
            )
        )

        return await adapter.debit(
            player_id=player_id,
            amount=amount,
            currency=currency,
            transaction_id=transaction_id,
        )

    @staticmethod
    async def credit(
        operator_id: str,
        player_id: str,
        amount: Decimal,
        currency: str,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Credit winnings to the player's wallet.
        """

        adapter = (
            await AdapterFactory.get_wallet_adapter(
                operator_id=operator_id,
            )
        )

        return await adapter.credit(
            player_id=player_id,
            amount=amount,
            currency=currency,
            transaction_id=transaction_id,
        )

    @staticmethod
    async def rollback(
        operator_id: str,
        player_id: str,
        amount: Decimal,
        currency: str,
        transaction_id: str,
        original_transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Rollback a previous wallet transaction.
        """

        adapter = (
            await AdapterFactory.get_wallet_adapter(
                operator_id=operator_id,
            )
        )

        return await adapter.rollback(
            player_id=player_id,
            amount=amount,
            currency=currency,
            transaction_id=transaction_id,
            original_transaction_id=(
                original_transaction_id
            ),
        )