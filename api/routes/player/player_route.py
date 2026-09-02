"""
Module: api.routes.player.player_route

Description:
    HTTP routes for player management.
"""

from fastapi import APIRouter

from api.controller.player.player_controller import (
    create_player,
    get_player,
)

from schemas.player.player_schema import (
    PlayerCreateRequest,
    PlayerResponse,
)


router = APIRouter(
    prefix="/players",
    tags=["Players"],
)


@router.post(
    "",
    response_model=PlayerResponse,
)
async def create_player_route(
    payload: PlayerCreateRequest,
):
    """
    Register a player.
    """

    return await create_player(payload)


@router.get(
    "/{player_id}",
    response_model=PlayerResponse,
)
async def get_player_route(
    player_id: str,
):
    """
    Retrieve a player.
    """

    return await get_player(player_id)