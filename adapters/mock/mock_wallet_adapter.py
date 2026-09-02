"""
Module: adapters.mock.mock_wallet_adapter

Description:
    Mock wallet adapter implementation.

Used for local development and testing without
connecting to an external operator wallet API.
"""

from decimal import Decimal
from typing import Any, Dict

from adapters.base.wallet_adapter import (
    WalletAdapter,
)


class MockWalletAdapter(WalletAdapter):
    """
    In-memory mock wallet implementation.

    This adapter simulates wallet operations for
    local development and testing.

    Transaction tracking is maintained in memory
    to simulate basic wallet idempotency and
    rollback validation.
    """

    # ---------------------------------------------------------
    # IN-MEMORY WALLET STORAGE
    # ---------------------------------------------------------

    _balances: Dict[str, Decimal] = {}

    _transactions: Dict[str, Dict[str, Any]] = {}

    def __init__(
        self,
        configuration: Dict[str, Any] | None = None,
    ):
        """
        Initialize mock wallet adapter.
        """

        self.configuration = configuration or {}

        adapter_configuration = (
            self.configuration.get(
                "configuration",
                self.configuration,
            )
        )

        self.default_balance = Decimal(
            str(
                adapter_configuration.get(
                    "default_balance",
                    10000,
                )
            )
        )

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================

    @staticmethod
    def _serialize_transaction(
        transaction: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Return a copy of a transaction dictionary.

        Decimal values are preserved because the
        API response layer can serialize them.
        """

        return dict(transaction)

    # =========================================================
    # GET BALANCE
    # =========================================================

    async def get_balance(
        self,
        player_id: str,
        currency: str,
    ) -> Dict[str, Any]:
        """
        Retrieve mock wallet balance.
        """

        balance = self._balances.get(
            player_id,
            self.default_balance,
        )

        return {
            "player_id": player_id,
            "currency": currency,
            "balance": balance,
        }

    # =========================================================
    # DEBIT
    # =========================================================

    async def debit(
        self,
        player_id: str,
        amount: Decimal,
        currency: str,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Debit amount from mock wallet.

        The transaction ID is idempotent. If the same
        transaction ID is received again, the previously
        recorded transaction result is returned without
        debiting the balance again.
        """

        amount = Decimal(str(amount))

        # -----------------------------------------------------
        # 1. Check duplicate transaction
        # -----------------------------------------------------

        existing_transaction = (
            self._transactions.get(
                transaction_id
            )
        )

        if existing_transaction:

            if (
                existing_transaction.get(
                    "operation"
                )
                != "debit"
            ):
                raise ValueError(
                    "Transaction ID already exists "
                    "for another operation."
                )

            return self._serialize_transaction(
                existing_transaction
            )

        # -----------------------------------------------------
        # 2. Get current balance
        # -----------------------------------------------------

        balance = self._balances.get(
            player_id,
            self.default_balance,
        )

        # -----------------------------------------------------
        # 3. Validate balance
        # -----------------------------------------------------

        if balance < amount:
            raise ValueError(
                "Insufficient wallet balance."
            )

        # -----------------------------------------------------
        # 4. Debit balance
        # -----------------------------------------------------

        new_balance = balance - amount

        self._balances[player_id] = new_balance

        # -----------------------------------------------------
        # 5. Record transaction
        # -----------------------------------------------------

        transaction = {
            "transaction_id": transaction_id,
            "player_id": player_id,
            "currency": currency,
            "amount": amount,
            "balance": new_balance,
            "status": "success",
            "operation": "debit",
            "rolled_back": False,
        }

        self._transactions[
            transaction_id
        ] = transaction

        # -----------------------------------------------------
        # 6. Return transaction
        # -----------------------------------------------------

        return self._serialize_transaction(
            transaction
        )

    # =========================================================
    # CREDIT
    # =========================================================

    async def credit(
        self,
        player_id: str,
        amount: Decimal,
        currency: str,
        transaction_id: str,
    ) -> Dict[str, Any]:
        """
        Credit amount to mock wallet.

        The transaction ID is idempotent. If the same
        transaction ID is received again, the previously
        recorded transaction result is returned without
        crediting the balance again.
        """

        amount = Decimal(str(amount))

        # -----------------------------------------------------
        # 1. Check duplicate transaction
        # -----------------------------------------------------

        existing_transaction = (
            self._transactions.get(
                transaction_id
            )
        )

        if existing_transaction:

            if (
                existing_transaction.get(
                    "operation"
                )
                != "credit"
            ):
                raise ValueError(
                    "Transaction ID already exists "
                    "for another operation."
                )

            return self._serialize_transaction(
                existing_transaction
            )

        # -----------------------------------------------------
        # 2. Get current balance
        # -----------------------------------------------------

        balance = self._balances.get(
            player_id,
            self.default_balance,
        )

        # -----------------------------------------------------
        # 3. Credit balance
        # -----------------------------------------------------

        new_balance = balance + amount

        self._balances[player_id] = new_balance

        # -----------------------------------------------------
        # 4. Record transaction
        # -----------------------------------------------------

        transaction = {
            "transaction_id": transaction_id,
            "player_id": player_id,
            "currency": currency,
            "amount": amount,
            "balance": new_balance,
            "status": "success",
            "operation": "credit",
        }

        self._transactions[
            transaction_id
        ] = transaction

        # -----------------------------------------------------
        # 5. Return transaction
        # -----------------------------------------------------

        return self._serialize_transaction(
            transaction
        )

    # =========================================================
    # ROLLBACK
    # =========================================================

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

        The rollback operation automatically performs the
        opposite action of the original transaction:

        - Original debit  -> rollback credits the amount.
        - Original credit -> rollback debits the amount.
        """

        amount = Decimal(
            str(amount)
        )

        original_transaction = (
            self._transactions.get(
                original_transaction_id
            )
        )

        if not original_transaction:
            raise ValueError(
                "Original transaction not found."
            )

        if (
            original_transaction["player_id"]
            != player_id
        ):
            raise ValueError(
                "Original transaction does not belong "
                "to this player."
            )

        if (
            original_transaction["currency"]
            != currency
        ):
            raise ValueError(
                "Original transaction currency mismatch."
            )

        if (
            Decimal(
                str(
                    original_transaction["amount"]
                )
            )
            != amount
        ):
            raise ValueError(
                "Rollback amount does not match "
                "original transaction amount."
            )

        original_operation = (
            original_transaction["operation"]
        )

        # -------------------------------------------------
        # Reverse original debit
        # -------------------------------------------------

        if original_operation == "debit":

            result = await self.credit(
                player_id=player_id,
                amount=amount,
                currency=currency,
                transaction_id=transaction_id,
            )

        # -------------------------------------------------
        # Reverse original credit
        # -------------------------------------------------

        elif original_operation == "credit":

            result = await self.debit(
                player_id=player_id,
                amount=amount,
                currency=currency,
                transaction_id=transaction_id,
            )

        else:

            raise ValueError(
                "Unsupported original transaction "
                "operation."
            )

        # -------------------------------------------------
        # Add rollback metadata
        # -------------------------------------------------

        result[
            "original_transaction_id"
        ] = original_transaction_id

        result[
            "operation"
        ] = "rollback"

        result[
            "reversed_operation"
        ] = original_operation

        return result