"""
Module: schemas.operator.operator_schema

Description:
    Request and response schemas for operator
    configuration management.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from config.models.enums import OperatorStatus


class OperatorCreateRequest(BaseModel):
    """
    Request schema for creating an operator.
    """

    operator_code: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
    )

    default_currency: str = Field(
        ...,
        min_length=3,
        max_length=10,
    )

    configuration: Dict[str, Any] = Field(
        default_factory=dict
    )


class OperatorUpdateRequest(BaseModel):
    """
    Request schema for updating an operator.

    Operator code is intentionally excluded because
    it should remain stable after creation.
    """

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    status: Optional[OperatorStatus] = None

    default_currency: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=10,
    )

    configuration: Optional[Dict[str, Any]] = None


class OperatorResponse(BaseModel):
    """
    Response schema for an operator.
    """

    id: str

    operator_code: str

    name: str

    status: OperatorStatus

    default_currency: str

    configuration: Dict[str, Any]

    created_at: datetime

    updated_at: datetime