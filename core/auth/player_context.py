"""
Module: core.auth.player_context

Description:
    Provides authenticated player context
    from a verified JWT token.
"""

from dataclasses import dataclass

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from core.auth.jwt_dependency import (
    get_current_token,
)


@dataclass(frozen=True)
class PlayerContext:
    """
    Represents the authenticated player
    executing a game request.
    """

    user_id: str

    player_id: str
    operator_id: str

    role: str


def get_player_context(
    token_data: dict = Depends(
        get_current_token
    ),
) -> PlayerContext:
    """
    Resolve authenticated player and operator
    from a verified JWT token.
    """

    user_id = token_data.get(
        "user_id"
    )

    player_id = token_data.get(
        "player_id"
    )

    operator_id = token_data.get(
        "operator_id"
    )

    role = token_data.get(
        "role"
    )

    if not user_id:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid token: user ID missing.",
        )

    if not player_id:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid token: player ID missing.",
        )

    if not operator_id:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid token: operator ID missing."
            ),
        )

    if not role:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid token: role missing.",
        )

    return PlayerContext(
        user_id=user_id,
        player_id=player_id,
        operator_id=operator_id,
        role=role,
    )