"""
Module: api.routes.game.hilo_route

Description:
    FastAPI routes for the Hi-Lo game.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from api.controller.game.hilo_controller import (
    HiLoGameController,
)

from schemas.game.hilo_schema import (
    PlaceBetRequest,
    StartGameRequest,
    StartGameResponse,
)

from core.auth.player_context import (
    PlayerContext,
    get_player_context,
)


router = APIRouter(
    prefix="/games/hi-lo",
    tags=["Hi-Lo Game"],
)

controller = HiLoGameController()


# =========================================================
# START GAME
# =========================================================

@router.post(
    "",
    response_model=StartGameResponse,
)
async def start_game(
    request: StartGameRequest,
    player: PlayerContext = Depends(
        get_player_context
    ),
):
    """
    Start a new Hi-Lo game.
    """

    try:

        return await controller.start_game(
            operator_id=player.operator_id,
            player_id=player.player_id,
            currency=request.currency,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

# =========================================================
# PLAYER GAME HISTORY
# IMPORTANT:
# Must come BEFORE /{game_id}
# =========================================================

@router.get(
    "/history",
)
async def get_game_history(
    skip: int = Query(
        0,
        ge=0,
    ),
    limit: int = Query(
        20,
        gt=0,
        le=100,
    ),
    player: PlayerContext = Depends(
        get_player_context
    ),
):
    """
    Retrieve game history for the current player.
    """

    try:
        return await controller.get_game_history(
            player_id=player.player_id,
            skip=skip,
            limit=limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# PLAYER ROUND HISTORY
# =========================================================

@router.get(
    "/rounds/history",
)
async def get_player_rounds(
    skip: int = Query(
        0,
        ge=0,
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
    ),
    player: PlayerContext = Depends(
        get_player_context
    ),
):
    """
    Retrieve the current player's Hi-Lo round history.
    """

    try:
        rounds = await controller.get_player_rounds(
            player_id=player.player_id,
            skip=skip,
            limit=limit,
        )

        return {
            "player_id": player.player_id,
            "rounds": rounds,
            "total": len(rounds),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# ROUND BY ID
# =========================================================

@router.get(
    "/rounds/{round_id}",
)
async def get_round_by_id(
    round_id: str,
):
    """
    Retrieve a Hi-Lo round by round ID.
    """

    try:
        round_data = await controller.get_round_by_id(
            round_id=round_id,
        )

        if not round_data:
            raise HTTPException(
                status_code=404,
                detail="Round not found.",
            )

        return round_data

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# GAME ROUNDS
# =========================================================

@router.get(
    "/{game_id}/rounds",
)
async def get_game_rounds(
    game_id: str,
    player: PlayerContext = Depends(
        get_player_context
    ),
):
    """
    Retrieve all rounds belonging to a game.
    """

    try:
        game = await controller.get_game(
            game_id=game_id,
            player_id=player.player_id,
            operator_id=player.operator_id
        )

        if not game:
            raise HTTPException(
                status_code=404,
                detail="Game not found.",
            )

        rounds = await controller.get_game_rounds(
            game_id=game_id,
        )

        return {
            "game_id": game_id,
            "rounds": rounds,
            "total": len(rounds),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# =========================================================
# SPECIFIC GAME ROUND
# =========================================================

@router.get(
    "/{game_id}/rounds/{round_id}",
)
async def get_game_round(
    game_id: str,
    round_id: str,
    player: PlayerContext = Depends(
        get_player_context
    ),
):
    """
    Retrieve a specific round belonging to a game.
    """

    try:
        game = await controller.get_game(
            game_id=game_id,
            player_id=player.player_id,
            operator_id=player.operator_id,
        )

        if not game:
            raise HTTPException(
                status_code=404,
                detail="Game not found.",
            )

        round_data = await controller.get_game_round(
            game_id=game_id,
            round_id=round_id,
        )

        if not round_data:
            raise HTTPException(
                status_code=404,
                detail="Round not found.",
            )

        return round_data

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# =========================================================
# GET GAME
# IMPORTANT:
# Dynamic route should be AFTER /history
# =========================================================

@router.get(
    "/{game_id}",
)
async def get_game(
    game_id: str,
    player: PlayerContext = Depends(
        get_player_context
    ),
):
    """
    Retrieve the current state of a Hi-Lo game.
    """

    try:
        return await controller.get_game(
            game_id=game_id,
            player_id=player.player_id,
            operator_id=player.operator_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# =========================================================
# PLAY ROUND
# =========================================================

@router.post(
    "/{game_id}/play",
)
async def play_round(
    game_id: str,
    request: PlaceBetRequest,
    player: PlayerContext = Depends(
        get_player_context
    ),
):
    """
    Play one Higher/Lower round.
    """

    try:
        return await controller.play_round(
            game_id=game_id,
            player_id=player.player_id,
            operator_id=player.operator_id,
            bet_amount=request.bet_amount,
            prediction=request.prediction,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.post(
    "/hi-lo/{game_id}/cancel",
)
async def cancel_game(
    game_id: str,
    player: PlayerContext = Depends(
        get_player_context
    ),
):
    return await controller.cancel_game(
        game_id=game_id,
        player_id=player.player_id,
        operator_id=player.operator_id,
    )