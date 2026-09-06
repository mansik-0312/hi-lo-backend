"""
Module: core.auth.jwt_dependency

Description:
    FastAPI dependency for validating JWT
    access tokens.
"""

from typing import (
    Any,
    Dict,
)

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from core.auth.jwt_handler import (
    decode_access_token,
)


security = HTTPBearer()


def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
) -> Dict[str, Any]:
    """
    Validate Bearer token and return
    decoded JWT payload.
    """

    token = credentials.credentials

    try:

        payload = decode_access_token(
            token
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=str(exc),
        )

    return payload