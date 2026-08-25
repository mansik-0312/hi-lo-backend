"""
Module: core.auth.player_context

Description:
    Provides a portable player context abstraction for game APIs.
"""

from dataclasses import dataclass

from fastapi import Request


@dataclass(frozen=True)
class PlayerContext:
    """
    Represents the player executing a game request.

    This abstraction keeps game logic independent from
    casino/operator authentication systems.
    """

    player_id: str


def get_player_context(
    request: Request,
) -> PlayerContext:
    """
    Resolve the current player.

    Temporary implementation:
    Uses demo-player until real authentication
    or platform integration is introduced.
    """

    return PlayerContext(
        player_id="demo-player",
    )