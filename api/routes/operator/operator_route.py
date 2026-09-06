"""
Module: api.routes.operator.operator_route

Description:
    HTTP routes for operator configuration.
"""

from fastapi import APIRouter

from api.controller.operator.operator_controller import (
    create_operator,
    get_operator,
    update_operator,
)

from schemas.operator.operator_schema import (
    OperatorCreateRequest,
    OperatorResponse,
    OperatorUpdateRequest,
)


router = APIRouter(
    prefix="/operators",
    tags=["Operators"],
)


@router.post(
    "",
    response_model=OperatorResponse,
)
async def create_operator_route(
    payload: OperatorCreateRequest,
):
    """
    Create an operator.
    """

    return await create_operator(
        payload
    )


@router.get(
    "/{operator_id}",
    response_model=OperatorResponse,
)
async def get_operator_route(
    operator_id: str,
):
    """
    Retrieve an operator configuration.
    """

    return await get_operator(
        operator_id
    )


@router.put(
    "/{operator_id}",
    response_model=OperatorResponse,
)
async def update_operator_route(
    operator_id: str,
    payload: OperatorUpdateRequest,
):
    """
    Update an operator configuration.
    """

    return await update_operator(
        operator_id,
        payload,
    )