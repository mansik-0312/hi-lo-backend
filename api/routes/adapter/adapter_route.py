"""
Module: api.routes.adapter.adapter_route

Description:
    HTTP routes for adapter configuration.
"""

from fastapi import APIRouter

from api.controller.adapter.adapter_controller import (
    create_adapter,
    get_adapter,
    update_adapter,
)

from schemas.adapter.adapter_schema import (
    AdapterCreateRequest,
    AdapterResponse,
    AdapterUpdateRequest,
)


router = APIRouter(
    prefix="/adapters",
    tags=["Adapters"],
)


@router.post(
    "",
    response_model=AdapterResponse,
)
async def create_adapter_route(
    payload: AdapterCreateRequest,
):
    """
    Create an adapter configuration.
    """

    return await create_adapter(payload)


@router.get(
    "/{adapter_id}",
    response_model=AdapterResponse,
)
async def get_adapter_route(
    adapter_id: str,
):
    """
    Retrieve an adapter configuration.
    """

    return await get_adapter(adapter_id)


@router.put(
    "/{adapter_id}",
    response_model=AdapterResponse,
)
async def update_adapter_route(
    adapter_id: str,
    payload: AdapterUpdateRequest,
):
    """
    Update an adapter configuration.
    """

    return await update_adapter(
        adapter_id,
        payload,
    )