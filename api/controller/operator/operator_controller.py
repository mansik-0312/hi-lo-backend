"""
Module: api.controller.operator.operator_controller

Description:
    Controller functions for operator
    configuration management.
"""

from services.operator.operator_service import (
    OperatorService,
)

from schemas.operator.operator_schema import (
    OperatorCreateRequest,
    OperatorUpdateRequest,
)


async def create_operator(
    payload: OperatorCreateRequest,
):
    """
    Create an operator.
    """

    return await OperatorService.create_operator(
        payload
    )


async def get_operator(
    operator_id: str,
):
    """
    Retrieve an operator.
    """

    return await OperatorService.get_operator(
        operator_id
    )


async def update_operator(
    operator_id: str,
    payload: OperatorUpdateRequest,
):
    """
    Update an operator.
    """

    return await OperatorService.update_operator(
        operator_id,
        payload,
    )