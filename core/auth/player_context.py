from dataclasses import dataclass

from fastapi import (
    Header,
    HTTPException,
    status,
)


@dataclass(frozen=True)
class PlayerContext:
    """
    Represents the player executing a game request.
    """

    player_id: str
    operator_id: str


def get_player_context(
    player_id: str | None = Header(
        default=None,
        alias="X-Player-ID",
    ),
    operator_id: str | None = Header(
        default=None,
        alias="X-Operator-ID",
    ),
) -> PlayerContext:
    """
    Resolve the current player and operator
    from request headers.
    """

    if not player_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Player ID is required.",
        )

    if not operator_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Operator ID is required.",
        )

    return PlayerContext(
        player_id=player_id,
        operator_id=operator_id,
    )