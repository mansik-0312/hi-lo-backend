"""
Module: services.game.hilo_service

Description:
    Business service for the Hi-Lo card game.

Responsibilities:
    - Start games.
    - Validate game state.
    - Validate bets and predictions.
    - Draw cards.
    - Evaluate predictions.
    - Calculate payouts.
    - Persist game and round state.

The service coordinates the game engine and repositories.

It must not contain HTTP-specific logic.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from bson.decimal128 import Decimal128

from config.models.hilo_game_model import (
    HiLoGameRepository,
)
from config.models.hilo_round_model import (
    HiLoRoundRepository,
)
from services.game.hilo_engine import HiLoGameEngine


class HiLoGameService:
    """
    Business service for Hi-Lo gameplay.
    """

    def __init__(self) -> None:
        """
        Initialize the Hi-Lo service.
        """

        self.engine = HiLoGameEngine()

    # =========================================================
    # START GAME
    # =========================================================

    async def start_game(
        self,
        player_id: str,
        initial_balance: Decimal,
    ) -> Dict[str, Any]:
        """
        Start a new Hi-Lo game.

        Args:
            player_id:
                Identifier of the player.

            initial_balance:
                Starting balance for the game.

        Returns:
            Newly created game information.

        Raises:
            ValueError:
                If the initial balance is invalid.
        """

        if initial_balance <= 0:
            raise ValueError(
                "Initial balance must be greater than zero."
            )

        deck = self.engine.create_deck()

        self.engine.shuffle_deck(deck)

        current_card, remaining_deck = (
            self.engine.draw_card(deck)
        )

        game_data = {
            "player_id": player_id,
            "status": "active",
            "current_card": current_card,
            "remaining_deck": remaining_deck,
            "balance": initial_balance,
            "current_round_id": None,
            "round_number": 0,
        }

        game_id = await HiLoGameRepository.create_game(
            game_data
        )

        return {
            "game_id": game_id,
            "status": "active",
            "current_card": current_card,
            "balance": initial_balance,
        }

    # =========================================================
    # GET GAME
    # =========================================================

    async def get_game(
        self,
        game_id: str,
        player_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve the current game state.

        Raises:
            ValueError:
                If the game does not exist or does not belong
                to the player.
        """

        game = await HiLoGameRepository.get_player_game(
            game_id=game_id,
            player_id=player_id,
        )

        if not game:
            raise ValueError(
                "Game not found."
            )

        # Never expose the remaining deck to the client.
        game.pop("remaining_deck", None)

        return game

    # =========================================================
    # PLAY ROUND
    # =========================================================

    async def play_round(
        self,
        game_id: str,
        player_id: str,
        bet_amount: Decimal,
        prediction: str,
    ) -> Dict[str, Any]:
        """
        Play one Higher/Lower round.

        Raises:
            ValueError:
                If the game cannot accept the round.
        """

        # -----------------------------------------------------
        # 1. Get game
        # -----------------------------------------------------

        game = await HiLoGameRepository.get_player_game(
            game_id=game_id,
            player_id=player_id,
        )

        if not game:
            raise ValueError(
                "Game not found."
            )

        # -----------------------------------------------------
        # 2. Validate game state
        # -----------------------------------------------------

        if game.get("status") != "active":
            raise ValueError(
                "Game is no longer active."
            )

        # -----------------------------------------------------
        # 3. Validate prediction BEFORE drawing a card
        # -----------------------------------------------------

        prediction = prediction.strip().lower()

        if prediction not in {
            "higher",
            "lower",
        }:
            raise ValueError(
                "Prediction must be 'higher' or 'lower'."
            )

        # -----------------------------------------------------
        # 4. Validate bet
        # -----------------------------------------------------

        if bet_amount <= 0:
            raise ValueError(
                "Bet amount must be greater than zero."
            )

        balance = Decimal(
            str(
                game.get(
                    "balance",
                    "0",
                )
            )
        )

        if bet_amount > balance:
            raise ValueError(
                "Insufficient game balance."
            )

        # -----------------------------------------------------
        # 5. Validate deck
        # -----------------------------------------------------

        remaining_deck = game.get(
            "remaining_deck",
            [],
        )

        if not remaining_deck:
            raise ValueError(
                "No cards remain."
            )

        # -----------------------------------------------------
        # 6. Draw next card
        # -----------------------------------------------------

        previous_card = game["current_card"]

        next_card, remaining_deck = (
            self.engine.draw_card(
                remaining_deck
            )
        )

        # -----------------------------------------------------
        # 7. Evaluate result
        # -----------------------------------------------------

        result = self.engine.evaluate_prediction(
            prediction=prediction,
            previous_card=previous_card,
            next_card=next_card,
        )

        # -----------------------------------------------------
        # 8. Calculate payout
        # -----------------------------------------------------

        payout = Decimal(
            str(
                self.engine.calculate_payout(
                    float(bet_amount),
                    result,
                )
            )
        )

        # -----------------------------------------------------
        # 9. Calculate new balance
        # -----------------------------------------------------

        new_balance = (
            balance
            - bet_amount
            + payout
        )

        # -----------------------------------------------------
        # 10. Calculate round number
        # -----------------------------------------------------

        round_number = (
            game.get(
                "round_number",
                0,
            )
            + 1
        )

        # -----------------------------------------------------
        # 11. Persist round
        # -----------------------------------------------------

        round_data = {
            "game_id": game_id,
            "player_id": player_id,
            "round_number": round_number,
            "bet_amount": bet_amount,
            "prediction": prediction,
            "previous_card": previous_card,
            "next_card": next_card,
            "result": result,
            "payout": payout,
            "status": "completed",
        }

        round_id = (
            await HiLoRoundRepository.create_round(
                round_data
            )
        )

        # -----------------------------------------------------
        # 12. Determine game status
        # -----------------------------------------------------

        game_status = (
            "completed"
            if not remaining_deck
            else "active"
        )

        # -----------------------------------------------------
        # 13. Persist updated game
        # -----------------------------------------------------

        await HiLoGameRepository.update_game(
            game_id,
            {
                "current_card": next_card,
                "remaining_deck": remaining_deck,
                "balance": new_balance,
                "current_round_id": round_id,
                "round_number": round_number,
                "status": game_status,
            },
        )

        # -----------------------------------------------------
        # 14. Return existing API response
        # -----------------------------------------------------

        return {
            "game_id": game_id,
            "round_id": round_id,
            "previous_card": previous_card,
            "next_card": next_card,
            "prediction": prediction,
            "result": result,
            "bet_amount": bet_amount,
            "payout": payout,
            "balance": new_balance,
        }

    # =========================================================
    # ROUND SERIALIZATION
    # =========================================================

    @staticmethod
    def _serialize_round(
        round_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert MongoDB round document into
        API-compatible data.
        """

        round_data = round_data.copy()

        if "_id" in round_data:
            round_data["round_id"] = str(
                round_data.pop("_id")
            )

        if isinstance(
            round_data.get("bet_amount"),
            Decimal128,
        ):
            round_data["bet_amount"] = Decimal(
                str(
                    round_data["bet_amount"]
                )
            )

        if isinstance(
            round_data.get("payout"),
            Decimal128,
        ):
            round_data["payout"] = Decimal(
                str(
                    round_data["payout"]
                )
            )

        return round_data

    # =========================================================
    # GET ROUND BY ID
    # =========================================================

    async def get_round_by_id(
        self,
        round_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single Hi-Lo round.
        """

        round_data = (
            await HiLoRoundRepository.get_round_by_id(
                round_id
            )
        )

        if not round_data:
            return None

        return self._serialize_round(
            round_data
        )

    # =========================================================
    # GET GAME ROUNDS
    # =========================================================

    async def get_game_rounds(
        self,
        game_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all rounds for a game.
        """

        rounds = (
            await HiLoRoundRepository.get_game_rounds(
                game_id
            )
        )

        return [
            self._serialize_round(
                round_data
            )
            for round_data in rounds
        ]

    # =========================================================
    # GET PLAYER ROUND HISTORY
    # =========================================================

    async def get_player_rounds(
        self,
        player_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve round history for a player.
        """

        if skip < 0:
            raise ValueError(
                "Skip cannot be negative."
            )

        if limit <= 0:
            raise ValueError(
                "Limit must be greater than zero."
            )

        if limit > 100:
            raise ValueError(
                "Limit cannot exceed 100."
            )

        rounds = (
            await HiLoRoundRepository.get_player_rounds(
                player_id=player_id,
                skip=skip,
                limit=limit,
            )
        )

        return [
            self._serialize_round(
                round_data
            )
            for round_data in rounds
        ]

    # =========================================================
    # GET SPECIFIC GAME ROUND
    # =========================================================

    async def get_game_round(
        self,
        round_id: str,
        game_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific round belonging to a game.
        """

        round_data = (
            await HiLoRoundRepository.get_game_round(
                round_id=round_id,
                game_id=game_id,
            )
        )

        if not round_data:
            return None

        return self._serialize_round(
            round_data
        )

    # =========================================================
    # GAME HISTORY
    # =========================================================

    async def get_game_history(
        self,
        player_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Retrieve game history for a player.
        """

        if skip < 0:
            raise ValueError(
                "Skip cannot be negative."
            )

        if limit <= 0:
            raise ValueError(
                "Limit must be greater than zero." 
            )

        if limit > 100:
            raise ValueError(
                "Limit cannot exceed 100."
            )

        games, total = (
            await HiLoGameRepository.get_player_games(
                player_id=player_id,
                skip=skip,
                limit=limit,
            )
        )

        return {
            "player_id": player_id,
            "games": games,
            "total": total,
        }