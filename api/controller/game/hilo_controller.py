"""
Module: api.controller.game.hilo_controller

Description:
    HTTP controller for the Hi-Lo game APIs.

The controller:
    - Receives validated API data.
    - Obtains the authenticated player.
    - Calls the game service.
    - Returns service results.

Business logic must remain in the service layer.
"""

from decimal import Decimal
from typing import Any, Dict

from services.game.hilo_service import HiLoGameService

from typing import Any, Dict, List, Optional

class HiLoGameController:
    """
    Controller responsible for Hi-Lo API operations.
    """

    def __init__(self) -> None:
        """
        Initialize the controller and Hi-Lo service.
        """

        self.service = HiLoGameService()

    # =========================================================
    # START GAME
    # =========================================================

    async def start_game(
        self,
        operator_id: str,
        player_id: str,
        currency: str,
    ) -> Dict[str, Any]:
        """
        Start a new Hi-Lo game.
        """

        return await self.service.start_game(
            operator_id=operator_id,
            player_id=player_id,
            currency=currency,
        )
    
    async def get_game(
        self,
        game_id: str,
        player_id: str,
        operator_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve a game.

        Args:
            game_id:
                Game identifier.

            player_id:
                Authenticated player identifier.

        Returns:
            Current game state.
        """

        return await self.service.get_game(
            game_id=game_id,
            player_id=player_id,
            operator_id=operator_id,
        )

    async def play_round(
        self,
        game_id: str,
        player_id: str,
        operator_id: str,
        bet_amount: Decimal,
        prediction: str,
    ) -> Dict[str, Any]:
        """
        Play one Hi-Lo round.

        Args:
            game_id:
                Game identifier.

            player_id:
                Authenticated player identifier.

            bet_amount:
                Amount wagered.

            prediction:
                Higher or Lower.

        Returns:
            Round result and updated balance.
        """

        return await self.service.play_round(
            game_id=game_id,
            player_id=player_id,
            operator_id=operator_id,
            bet_amount=bet_amount,
            prediction=prediction,
        )

    async def get_round_by_id(
        self,
        round_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single round.
        """

        return await self.service.get_round_by_id(
            round_id=round_id,
        )

    async def get_game_round(
        self,
        game_id: str,
        round_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific round belonging to a game.
        """

        return await self.service.get_game_round(
            round_id=round_id,
            game_id=game_id,
        )

    async def get_game_rounds(
        self,
        game_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all rounds belonging to a game.
        """

        return await self.service.get_game_rounds(
            game_id=game_id,
        )

    async def get_player_rounds(
        self,
        player_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve round history for a player.
        """

        return await self.service.get_player_rounds(
            player_id=player_id,
            skip=skip,
            limit=limit,
        )

    async def get_game_history(
        self,
        player_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Retrieve game history for a player.
        """

        return await self.service.get_game_history(
            player_id=player_id,
            skip=skip,
            limit=limit,
        )

    # =========================================================
    # CANCEL GAME
    # =========================================================

    async def cancel_game(
        self,
        game_id: str,
        player_id: str,
        operator_id: str,
    ) -> Dict[str, Any]:
        """
        Cancel an active Hi-Lo game.

        Only the player who owns the game may cancel it.
        """

        return await self.service.cancel_game(
            game_id=game_id,
            player_id=player_id,
            operator_id=operator_id,
        )