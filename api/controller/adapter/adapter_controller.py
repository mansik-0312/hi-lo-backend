"""
Module: api.controller.adapter.adapter_controller

Description:
    Controller layer for adapter configuration APIs.

The controller is responsible for:

    - Receiving validated request schemas.
    - Calling the AdapterService.
    - Converting business errors into HTTP responses.

Business logic must remain inside the service layer.
Database operations must remain inside repository/model files.
"""
"""
Module: api.controller.adapter.adapter_controller

Description:
    Controller functions for adapter configuration.
"""

import logging

from fastapi import HTTPException, status

from services.adapter.adapter_factory import (
    AdapterFactory,
)

from schemas.adapter.adapter_schema import (
    AdapterCreateRequest,
    AdapterResponse,
    AdapterUpdateRequest,
)


logger = logging.getLogger(__name__)


async def create_adapter(
    payload: AdapterCreateRequest,
) -> AdapterResponse:
    """
    Create a wallet adapter configuration.
    """

    try:
        adapter = await AdapterFactory.create_adapter(
            payload
        )

        return AdapterResponse(
            **adapter
        )

    except ValueError as exc:
        logger.warning(
            "Adapter creation validation failed: %s",
            str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Unexpected error while creating adapter."
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                f"Unable to create adapter: {str(exc)}"
            ),
        )


async def get_adapter(
    adapter_id: str,
) -> AdapterResponse:
    """
    Retrieve an adapter configuration.

    Args:
        adapter_id:
            MongoDB adapter identifier.

    Returns:
        AdapterResponse:
            Adapter configuration.

    Raises:
        HTTPException:
            If the adapter does not exist.
    """

    try:
        adapter = await AdapterFactory.get_adapter(
            adapter_id
        )

        return AdapterResponse(
            **adapter
        )

    except ValueError as exc:
        error_message = str(exc)

        if (
            error_message == "Adapter not found."
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=error_message,
            )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=error_message,
        )

    except Exception:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to retrieve adapter."
            ),
        )


async def update_adapter(
    adapter_id: str,
    payload: AdapterUpdateRequest,
) -> AdapterResponse:
    """
    Update an adapter configuration.

    Args:
        adapter_id:
            MongoDB adapter identifier.

        payload:
            Adapter update request.

    Returns:
        AdapterResponse:
            Updated adapter configuration.

    Raises:
        HTTPException:
            If the update operation fails.
    """

    try:
        adapter = await AdapterFactory.update_adapter(
            adapter_id=adapter_id,
            payload=payload,
        )

        return AdapterResponse(
            **adapter
        )

    except ValueError as exc:
        error_message = str(exc)

        if error_message == "Adapter not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Unexpected error while updating adapter."
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                f"Unable to update adapter: {str(exc)}"
            ),
        )