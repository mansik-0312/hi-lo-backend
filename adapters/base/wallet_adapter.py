"""
Module: adapters.base.wallet_adapter

Description:
    Abstract wallet adapter contract.

Every wallet adapter implementation must provide
methods for:

    - Balance retrieval
    - Debit
    - Credit
    - Rollback
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict


class WalletAdapter(ABC):
    """
    Base interface for all wallet adapters.

    Game and round services should interact only
    with this interface and should not depend on
    a specific wallet implementation.
    """

    @abstractmethod
    async def get_balance(
        self,
        player_id: str,
        currency: str,
    ) -> Dict[str, Any]:
        """
        Retrieve player wallet balance.
        """

        pass

    @abstractmethod
    async def debit(
        self,
        player_id: str,
        amount: Decimal,
        currency: str,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Debit funds from the player wallet.
        """

        pass

    @abstractmethod
    async def debit(
        self,
        player_id: str,
        amount: Decimal,
        currency: str,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Credit funds to the player wallet.
        """

        pass

    @abstractmethod
    async def rollback(
        self,
        player_id: str,
        amount: Decimal,
        currency: str,
        transaction_id: str,
        original_transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Reverse a previous wallet transaction.

        Args:
            player_id:
                Player whose transaction is being reversed.

            amount:
                Amount to reverse.

            currency:
                Transaction currency.

            transaction_id:
                Unique transaction ID for this rollback.

            original_transaction_id:
                Original wallet transaction being reversed.
        """

        pass