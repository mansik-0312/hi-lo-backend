"""
Module: adapters.http.http_wallet_adapter

Description:
    HTTP wallet adapter for communicating with external operator
    wallet APIs.

The adapter converts the platform's normalized wallet operations
into HTTP requests and converts operator responses back into the
platform's normalized wallet response format.

Supported operations:

    - Balance
    - Debit
    - Credit
    - Rollback
    - Health check

Operator-specific configuration is supplied when the adapter is
created.

The adapter must never expose credentials in responses or logs.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

import httpx

from adapters.base.wallet_adapter import WalletAdapter
from config.models.enums import WalletOperationStatus
from schemas.transaction.transaction_schema import (
    WalletTransactionRequest,
    WalletTransactionResponse,
)


# ============================================================================
# HTTP WALLET ADAPTER
# ============================================================================


class HTTPWalletAdapter(WalletAdapter):
    """
    HTTP implementation of the wallet adapter.

    This adapter allows the Hi-Lo platform to integrate with an
    external casino/operator wallet.

    The exact operator API is configurable.

    Example configuration:

        {
            "base_url": "https://wallet.example.com",
            "endpoints": {
                "balance": "/wallet/balance",
                "debit": "/wallet/debit",
                "credit": "/wallet/credit",
                "rollback": "/wallet/rollback",
                "health": "/health"
            }
        }

    Authentication details are supplied separately and should come
    from a secure secret manager/environment configuration.
    """

    def __init__(
        self,
        base_url: str,
        endpoints: Dict[str, str],
        authentication_type: Optional[str] = None,
        authentication_value: Optional[str] = None,
        timeout: float = 10.0,
        verify_ssl: bool = True,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize the HTTP wallet adapter.

        Args:
            base_url:
                Base URL of the operator wallet API.

            endpoints:
                Mapping of wallet operations to endpoint paths.

            authentication_type:
                Authentication mechanism.

                Examples:

                    bearer
                    api_key
                    none

            authentication_value:
                Secret authentication value.

                This value must never be logged.

            timeout:
                HTTP request timeout in seconds.

            verify_ssl:
                Whether TLS certificate verification is enabled.

            headers:
                Additional non-sensitive HTTP headers.
        """

        self.base_url = base_url.rstrip("/")

        self.endpoints = endpoints

        self.authentication_type = (
            authentication_type
            or "none"
        )

        self.authentication_value = (
            authentication_value
        )

        self.timeout = timeout

        self.verify_ssl = verify_ssl

        self.headers = headers or {}

    # ========================================================================
    # HTTP CLIENT
    # ========================================================================

    def _build_headers(
        self,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Build HTTP headers for an operator request.

        Args:
            idempotency_key:
                Optional idempotency key.

        Returns:
            HTTP headers.

        Important:
            Authentication values are never logged.
        """

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self.headers,
        }

        if (
            self.authentication_type.lower()
            == "bearer"
            and self.authentication_value
        ):
            headers["Authorization"] = (
                f"Bearer {self.authentication_value}"
            )

        elif (
            self.authentication_type.lower()
            == "api_key"
            and self.authentication_value
        ):
            headers["X-API-Key"] = (
                self.authentication_value
            )

        if idempotency_key:
            headers["Idempotency-Key"] = (
                idempotency_key
            )

        return headers

    def _get_url(
        self,
        operation: str,
    ) -> str:
        """
        Build an operator API URL.

        Args:
            operation:
                Operation name.

        Returns:
            Complete endpoint URL.

        Raises:
            ValueError:
                If the configured endpoint is missing.
        """

        endpoint = self.endpoints.get(
            operation
        )

        if not endpoint:
            raise ValueError(
                f"Wallet endpoint is not configured: {operation}"
            )

        return (
            f"{self.base_url}/"
            f"{endpoint.lstrip('/')}"
        )

    # ========================================================================
    # RESPONSE PARSING
    # ========================================================================

    @staticmethod
    def _extract_error(
        response: httpx.Response,
    ) -> tuple[str, str]:
        """
        Extract a safe error response from an operator API.

        Args:
            response:
                HTTP response.

        Returns:
            Tuple containing normalized error code and message.

        Important:
            The complete operator response must not automatically be
            exposed to API clients.
        """

        try:
            payload = response.json()

            error_code = (
                payload.get("error_code")
                or payload.get("code")
                or f"HTTP_{response.status_code}"
            )

            error_message = (
                payload.get("error_message")
                or payload.get("message")
                or "Wallet operation failed."
            )

            return (
                str(error_code),
                str(error_message),
            )

        except Exception:
            return (
                f"HTTP_{response.status_code}",
                "Wallet operation failed.",
            )

    @staticmethod
    def _extract_transaction_id(
        payload: Dict[str, Any],
    ) -> Optional[str]:
        """
        Extract external transaction ID from an operator response.

        Supports common response naming conventions.

        Args:
            payload:
                Operator response.

        Returns:
            External transaction identifier if available.
        """

        return (
            payload.get("external_transaction_id")
            or payload.get("transaction_id")
            or payload.get("transactionId")
            or payload.get("id")
        )

    @staticmethod
    def _extract_balance(
        payload: Dict[str, Any],
    ) -> Optional[Decimal]:
        """
        Extract player balance from an operator response.

        Args:
            payload:
                Operator response.

        Returns:
            Decimal balance when supplied.
        """

        value = (
            payload.get("balance")
            or payload.get("current_balance")
            or payload.get("available_balance")
        )

        if value is None:
            return None

        try:
            return Decimal(str(value))
        except Exception:
            return None

    # ========================================================================
    # BALANCE
    # ========================================================================

    async def get_balance(
        self,
        player_id: str,
        currency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WalletTransactionResponse:
        """
        Retrieve player balance from the operator wallet.

        Args:
            player_id:
                External player identifier.

            currency:
                Optional currency.

            metadata:
                Optional non-sensitive metadata.

        Returns:
            WalletTransactionResponse:
                Normalized wallet balance response.
        """

        transaction_id = (
            f"BALANCE-{player_id}"
        )

        try:
            url = self._get_url(
                "balance"
            )

            payload = {
                "player_id": player_id,
            }

            if currency:
                payload["currency"] = currency

            headers = self._build_headers()

            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=self.verify_ssl,
            ) as client:

                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                )

            if response.status_code >= 400:

                error_code, error_message = (
                    self._extract_error(response)
                )

                return self.build_failure_response(
                    transaction_id=transaction_id,
                    error_code=error_code,
                    error_message=error_message,
                )

            response_payload = response.json()

            balance = self._extract_balance(
                response_payload
            )

            if balance is None:
                return self.build_failure_response(
                    transaction_id=transaction_id,
                    error_code="INVALID_BALANCE_RESPONSE",
                    error_message=(
                        "Operator wallet did not return "
                        "a valid balance."
                    ),
                )

            return WalletTransactionResponse(
                success=True,
                transaction_id=transaction_id,
                status=WalletOperationStatus.SUCCESS,
                balance_before=balance,
                balance_after=balance,
                metadata={
                    "adapter": self.get_adapter_type(),
                    "fetched_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                },
            )

        except httpx.TimeoutException:

            return self.build_failure_response(
                transaction_id=transaction_id,
                error_code="WALLET_TIMEOUT",
                error_message=(
                    "Operator wallet request timed out."
                ),
            )

        except httpx.RequestError:

            return self.build_failure_response(
                transaction_id=transaction_id,
                error_code="WALLET_UNAVAILABLE",
                error_message=(
                    "Operator wallet is unavailable."
                ),
            )

        except Exception:

            return self.build_failure_response(
                transaction_id=transaction_id,
                error_code="WALLET_ERROR",
                error_message=(
                    "Unexpected wallet integration error."
                ),
            )

    # ========================================================================
    # DEBIT
    # ========================================================================

    async def debit(
        self,
        request: WalletTransactionRequest,
    ) -> WalletTransactionResponse:
        """
        Debit the player's operator wallet.

        Args:
            request:
                Normalized wallet transaction request.

        Returns:
            WalletTransactionResponse:
                Normalized debit response.
        """

        self.validate_amount(
            request.amount
        )

        return await self._execute_transaction(
            operation="debit",
            request=request,
        )

    # ========================================================================
    # CREDIT
    # ========================================================================

    async def credit(
        self,
        request: WalletTransactionRequest,
    ) -> WalletTransactionResponse:
        """
        Credit the player's operator wallet.

        Args:
            request:
                Normalized wallet transaction request.

        Returns:
            WalletTransactionResponse:
                Normalized credit response.
        """

        self.validate_amount(
            request.amount
        )

        return await self._execute_transaction(
            operation="credit",
            request=request,
        )

    # ========================================================================
    # ROLLBACK
    # ========================================================================

    async def rollback(
        self,
        request: WalletTransactionRequest,
    ) -> WalletTransactionResponse:
        """
        Roll back a previous operator wallet transaction.

        Args:
            request:
                Normalized rollback request.

        Returns:
            WalletTransactionResponse:
                Normalized rollback response.
        """

        self.validate_amount(
            request.amount
        )

        if not request.parent_transaction_id:

            return self.build_failure_response(
                transaction_id=request.transaction_id,
                error_code="PARENT_TRANSACTION_REQUIRED",
                error_message=(
                    "Parent transaction is required "
                    "for wallet rollback."
                ),
            )

        return await self._execute_transaction(
            operation="rollback",
            request=request,
        )

    # ========================================================================
    # GENERIC TRANSACTION
    # ========================================================================

    async def _execute_transaction(
        self,
        operation: str,
        request: WalletTransactionRequest,
    ) -> WalletTransactionResponse:
        """
        Execute a normalized wallet transaction against the operator.

        Args:
            operation:
                Wallet operation name.

            request:
                Normalized wallet transaction request.

        Returns:
            WalletTransactionResponse:
                Normalized wallet operation response.
        """

        try:
            url = self._get_url(
                operation
            )

            payload = {
                "player_id": request.player_id,
                "transaction_id": request.transaction_id,
                "amount": str(request.amount),
                "currency": request.currency,
                "game_id": request.game_id,
                "round_id": request.round_id,
                "transaction_type": (
                    request.transaction_type.value
                ),
                "idempotency_key": (
                    request.idempotency_key
                ),
                "metadata": request.metadata,
            }

            if request.parent_transaction_id:
                payload[
                    "parent_transaction_id"
                ] = request.parent_transaction_id

            headers = self._build_headers(
                request.idempotency_key
            )

            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=self.verify_ssl,
            ) as client:

                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                )

            # --------------------------------------------------------
            # FAILED RESPONSE
            # --------------------------------------------------------

            if response.status_code >= 400:

                error_code, error_message = (
                    self._extract_error(response)
                )

                return self.build_failure_response(
                    transaction_id=request.transaction_id,
                    error_code=error_code,
                    error_message=error_message,
                )

            # --------------------------------------------------------
            # SUCCESS RESPONSE
            # --------------------------------------------------------

            response_payload = response.json()

            external_transaction_id = (
                self._extract_transaction_id(
                    response_payload
                )
            )

            balance_before = (
                self._extract_balance(
                    response_payload
                )
            )

            balance_after = (
                self._extract_balance(
                    response_payload
                )
            )

            return self.build_success_response(
                transaction_id=request.transaction_id,
                external_transaction_id=(
                    external_transaction_id
                ),
                balance_before=balance_before,
                balance_after=balance_after,
                metadata={
                    "adapter": self.get_adapter_type(),
                    "operation": operation,
                },
            )

        except httpx.TimeoutException:

            return self.build_failure_response(
                transaction_id=request.transaction_id,
                error_code="WALLET_TIMEOUT",
                error_message=(
                    "Operator wallet request timed out."
                ),
            )

        except httpx.RequestError:

            return self.build_failure_response(
                transaction_id=request.transaction_id,
                error_code="WALLET_UNAVAILABLE",
                error_message=(
                    "Operator wallet is unavailable."
                ),
            )

        except ValueError as exc:

            return self.build_failure_response(
                transaction_id=request.transaction_id,
                error_code="INVALID_ADAPTER_CONFIGURATION",
                error_message=str(exc),
            )

        except Exception:

            return self.build_failure_response(
                transaction_id=request.transaction_id,
                error_code="WALLET_ERROR",
                error_message=(
                    "Unexpected wallet integration error."
                ),
            )

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    async def health_check(
        self,
    ) -> bool:
        """
        Check operator wallet availability.

        Returns:
            bool:
                True when the wallet health endpoint responds
                successfully.
        """

        try:
            url = self._get_url(
                "health"
            )

            headers = self._build_headers()

            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=self.verify_ssl,
            ) as client:

                response = await client.get(
                    url,
                    headers=headers,
                )

            return response.status_code < 400

        except Exception:
            return False

    # ========================================================================
    # ADAPTER TYPE
    # ========================================================================

    def get_adapter_type(
        self,
    ) -> str:
        """
        Return the adapter type.

        Returns:
            str:
                ``http``.
        """

        return "http"