"""
Module: core.auth.jwt_handler

Description:
    JWT access and refresh token
    creation and verification utilities.
"""

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from typing import (
    Any,
    Dict,
)

from jose import (
    JWTError,
    jwt,
)

from config.basic_config import settings


def create_access_token(
    data: Dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create JWT access token.
    """

    to_encode = data.copy()

    expire = (
        datetime.now(
            timezone.utc
        )
        + (
            expires_delta
            or timedelta(
                minutes=(
                    settings.ACCESS_TOKEN_EXPIRE_MINUTES
                )
            )
        )
    )

    to_encode.update(
        {
            "exp": expire,
            "token_type": "access",
        }
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_ACCESS_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(
    data: Dict[str, Any],
) -> str:
    """
    Create JWT refresh token.
    """

    to_encode = data.copy()

    expire = (
        datetime.now(
            timezone.utc
        )
        + timedelta(
            minutes=(
                settings.REFRESH_TOKEN_EXPIRE_MINUTES
            )
        )
    )

    to_encode.update(
        {
            "exp": expire,
            "token_type": "refresh",
        }
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_REFRESH_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> Dict[str, Any]:
    """
    Decode and validate JWT access token.
    """

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_ACCESS_KEY,
            algorithms=[
                settings.ALGORITHM
            ],
        )

        if payload.get(
            "token_type"
        ) != "access":

            raise ValueError(
                "Invalid access token."
            )

        return payload

    except JWTError as exc:

        raise ValueError(
            "Invalid or expired access token."
        ) from exc


def decode_refresh_token(
    token: str,
) -> Dict[str, Any]:
    """
    Decode and validate JWT refresh token.
    """

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_REFRESH_KEY,
            algorithms=[
                settings.ALGORITHM
            ],
        )

        if payload.get(
            "token_type"
        ) != "refresh":

            raise ValueError(
                "Invalid refresh token."
            )

        return payload

    except JWTError as exc:

        raise ValueError(
            "Invalid or expired refresh token."
        ) from exc