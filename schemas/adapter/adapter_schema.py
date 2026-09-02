"""
Module: schemas.adapter.adapter_schema

Description:
    Pydantic schemas used by the adapter APIs.

Adapters allow the Hi-Lo platform to communicate with different
operator/casino wallet systems without changing the game engine.

The adapter configuration is intentionally separated from the
adapter persistence model.

Secrets must never be accepted back in API responses.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
)

from config.models.enums import (
    AdapterStatus,
    AdapterType,
)


# ============================================================================
# CREATE ADAPTER
# ============================================================================


class AdapterCreateRequest(BaseModel):
    """
    Request schema for creating a wallet adapter.
    """

    operator_id: str = Field(
        ...,
        min_length=1,
        description="Operator that owns the adapter.",
    )

    adapter_type: AdapterType = Field(
        ...,
        description="Type of wallet adapter.",
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Human-readable adapter name.",
    )

    base_url: Optional[HttpUrl] = Field(
        default=None,
        description="Base URL of the operator wallet API.",
    )

    authentication_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Authentication mechanism used by the adapter.",
    )

    endpoints: Dict[str, str] = Field(
        default_factory=dict,
        description="Wallet endpoint configuration.",
    )

    configuration: Dict[str, Any] = Field(
        default_factory=dict,
        description="Non-sensitive adapter configuration.",
    )

    secret_reference: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Reference to credentials stored in a secret manager.",
    )


# ============================================================================
# UPDATE ADAPTER
# ============================================================================


class AdapterUpdateRequest(BaseModel):
    """
    Request schema for updating an adapter.

    All fields are optional so partial updates are supported.
    """

    adapter_type: Optional[
        AdapterType
    ] = None

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    status: Optional[
        AdapterStatus
    ] = None

    base_url: Optional[
        HttpUrl
    ] = None

    authentication_type: Optional[
        str
    ] = Field(
        default=None,
        max_length=50,
    )

    endpoints: Optional[
        Dict[str, str]
    ] = None

    configuration: Optional[
        Dict[str, Any]
    ] = None

    secret_reference: Optional[
        str
    ] = Field(
        default=None,
        max_length=255,
    )

# ============================================================================
# ADAPTER RESPONSE
# ============================================================================


class AdapterResponse(BaseModel):
    """
    Public adapter response.

    Secret values are intentionally excluded.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str

    operator_id: str

    adapter_type: AdapterType

    name: str

    status: AdapterStatus

    base_url: Optional[str] = None

    authentication_type: Optional[str] = None

    endpoints: Dict[str, str] = Field(
        default_factory=dict
    )

    configuration: Dict[str, Any] = Field(
        default_factory=dict
    )

    secret_reference: Optional[str] = None

    created_at: datetime

    updated_at: datetime


# ============================================================================
# ADAPTER TEST
# ============================================================================


class AdapterTestRequest(BaseModel):
    """
    Request schema for testing an adapter connection.
    """

    adapter_id: str = Field(
        ...,
        min_length=1,
    )


class AdapterTestResponse(BaseModel):
    """
    Response returned after testing an adapter.
    """

    adapter_id: str

    success: bool

    status: str

    message: str

    response_time_ms: Optional[float] = None

    tested_at: datetime