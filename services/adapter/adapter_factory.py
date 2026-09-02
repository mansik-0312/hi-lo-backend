"""
Module: services.adapter.adapter_factory

Description:
    Factory responsible for resolving the correct
    wallet adapter implementation for an operator.
"""

from adapters.base.wallet_adapter import (
    WalletAdapter,
)

from adapters.mock.mock_wallet_adapter import (
    MockWalletAdapter,
)

from config.models.adapter_model import (
    AdapterRepository,
)


class AdapterFactory:
    """
    Factory responsible for creating wallet adapter
    instances based on operator configuration.
    """

    @staticmethod
    async def get_wallet_adapter(
        operator_id: str,
    ) -> WalletAdapter:
        """
        Resolve the active wallet adapter for an
        operator.

        Args:
            operator_id:
                MongoDB operator identifier.

        Returns:
            WalletAdapter implementation.

        Raises:
            ValueError:
                If no active adapter exists or the
                adapter type is unsupported.
        """

        adapter = (
            await AdapterRepository.get_active_by_operator(
                operator_id
            )
        )

        if not adapter:
            raise ValueError(
                "No active adapter found for operator."
            )

        adapter_type = adapter.get(
            "adapter_type"
        )

        if adapter_type == "mock":

            return MockWalletAdapter(
                configuration=adapter
            )

        raise ValueError(
            f"Unsupported adapter type: {adapter_type}"
        )