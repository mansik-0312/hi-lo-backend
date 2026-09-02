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
from fastapi import HTTPException, status
from uuid import uuid4

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

from config.game.hilo_config import (
    HILO_GAME_CONFIG,
    HiLoGameConfig,
)

from services.wallet.wallet_service import (
    WalletService,
)

from config.models.enums import GameStatus, RoundStatus

class HiLoGameService:
    """
    Business service for Hi-Lo gameplay.
    """

    def __init__(
        self,
        config: HiLoGameConfig = HILO_GAME_CONFIG,
    ) -> None:
        """
        Initialize the Hi-Lo service.

        Args:
            config:
                Game configuration containing betting
                and payout rules.
        """

        self.engine = HiLoGameEngine()
        self.config = config

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

        The player's balance is retrieved from the
        operator wallet through WalletService.
        """

        # -----------------------------------------------------
        # 1. Get player wallet balance
        # -----------------------------------------------------

        wallet_balance = (
            await WalletService.get_balance(
                operator_id=operator_id,
                player_id=player_id,
                currency=currency,
            )
        )

        balance = Decimal(
            str(
                wallet_balance.get(
                    "balance",
                    "0",
                )
            )
        )

        # -----------------------------------------------------
        # 2. Validate balance
        # -----------------------------------------------------

        if balance <= Decimal("0"):
            raise ValueError(
                "Wallet balance must be greater than zero."
            )

        # -----------------------------------------------------
        # 3. Create deck
        # -----------------------------------------------------

        deck = self.engine.create_deck()

        self.engine.shuffle_deck(
            deck
        )

        current_card, remaining_deck = (
            self.engine.draw_card(
                deck
            )
        )

        # -----------------------------------------------------
        # 4. Create game
        # -----------------------------------------------------

        game_data = {
            "operator_id": operator_id,
            "player_id": player_id,
            "status": GameStatus.ACTIVE.value,
            "current_card": current_card,
            "remaining_deck": remaining_deck,
            "balance": balance,
            "current_round_id": None,
            "round_number": 0,
            "currency": currency,
        }

        game_id = (
            await HiLoGameRepository.create_game(
                game_data
            )
        )

        # -----------------------------------------------------
        # 5. Return game
        # -----------------------------------------------------

        return {
            "game_id": game_id,
            "operator_id": operator_id,
            "player_id": player_id,
            "status": GameStatus.ACTIVE.value,
            "current_card": current_card,
            "currency": currency,
            "balance": balance,
        }
    # =========================================================
    # GET GAME
    # =========================================================

    async def get_game(
        self,
        game_id: str,
        player_id: str,
        operator_id: str,
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
            operator_id=operator_id,
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
        operator_id: str,
        bet_amount: Decimal,
        prediction: str,
    ) -> Dict[str, Any]:
        """
        Play one Higher/Lower round.

        Flow:

            1. Retrieve and validate game.
            2. Validate prediction and bet.
            3. Debit bet amount from operator wallet.
            4. Draw and evaluate next card.
            5. Calculate payout.
            6. Credit winnings when payout is greater than zero.
            7. Persist completed round.
            8. Update game state.
            9. Roll back wallet debit if processing fails.

        Raises:
            ValueError:
                If the game or wallet operation fails.
        """

        # =====================================================
        # 1. GET GAME
        # =====================================================

        game = await HiLoGameRepository.get_player_game(
            game_id=game_id,
            player_id=player_id,
            operator_id=operator_id,
        )

        if not game:
            raise ValueError(
                "Game not found."
            )

        # =====================================================
        # 1. VALIDATE GAME OWNERSHIP
        # =====================================================

        if game.get("player_id") != player_id:
            raise ValueError(
                "You do not have access to this game."
            )

        # =====================================================
        # 2. VALIDATE GAME STATE
        # =====================================================

        if game.get("status") != GameStatus.ACTIVE.value:
            raise ValueError(
                "Game is no longer active."
            )
        # =====================================================
        # 2. VALIDATE GAME STATE
        # =====================================================

        if game.get("status") != "active":
            raise ValueError(
                "Game is no longer active."
            )

        operator_id = game.get(
            "operator_id"
        )

        if not operator_id:
            raise ValueError(
                "Game operator is missing."
            )

        currency = game.get(
            "currency",
            "INR",
        )

        # =====================================================
        # 3. VALIDATE PREDICTION
        # =====================================================

        prediction = prediction.strip().lower()

        if prediction not in {
            "higher",
            "lower",
        }:
            raise ValueError(
                "Prediction must be 'higher' or 'lower'."
            )

        # =====================================================
        # 4. VALIDATE BET
        # =====================================================

        if bet_amount < self.config.min_bet:
            raise ValueError(
                f"Bet amount must be at least "
                f"{self.config.min_bet}."
            )

        if bet_amount > self.config.max_bet:
            raise ValueError(
                f"Bet amount cannot exceed "
                f"{self.config.max_bet}."
            )

        game_balance = Decimal(
            str(
                game.get(
                    "balance",
                    "0",
                )
            )
        )

        if bet_amount > game_balance:
            raise ValueError(
                "Insufficient game balance."
            )

        # =====================================================
        # 5. VALIDATE DECK
        # =====================================================

        remaining_deck = game.get(
            "remaining_deck",
            [],
        )

        if not remaining_deck:
            raise ValueError(
                "No cards remain."
            )

        # =====================================================
        # 6. PREPARE WALLET TRANSACTION
        # =====================================================

        bet_transaction_id = (
            f"hilo_debit_{uuid4().hex}"
        )

        payout_transaction_id = None
        rollback_transaction_id = None

        debit_completed = False
        payout_completed = False

        try:

            # =================================================
            # 7. DEBIT BET FROM WALLET
            # =================================================

            wallet_debit = await WalletService.debit(
                operator_id=operator_id,
                player_id=player_id,
                amount=bet_amount,
                currency=currency,
                transaction_id=bet_transaction_id,
            )

            if wallet_debit.get("status") != "success":
                raise ValueError(
                    "Wallet debit failed."
                )

            debit_completed = True

            # Wallet balance immediately after debit.
            wallet_balance = Decimal(
                str(
                    wallet_debit.get(
                        "balance",
                        "0",
                    )
                )
            )

            # =================================================
            # 8. DRAW NEXT CARD
            # =================================================

            previous_card = game[
                "current_card"
            ]

            next_card, updated_remaining_deck = (
                self.engine.draw_card(
                    remaining_deck
                )
            )

            # =================================================
            # 9. EVALUATE RESULT
            # =================================================

            result = (
                self.engine.evaluate_prediction(
                    prediction=prediction,
                    previous_card=previous_card,
                    next_card=next_card,
                )
            )

            # =================================================
            # 10. CALCULATE PAYOUT
            # =================================================

            payout = Decimal(
                str(
                    self.engine.calculate_payout(
                        float(bet_amount),
                        result,
                        float(
                            self.config
                            .win_payout_multiplier
                        ),
                    )
                )
            )

            # =================================================
            # 11. CREDIT PAYOUT TO WALLET
            # =================================================

            if payout > Decimal("0"):

                payout_transaction_id = (
                    f"hilo_payout_{uuid4().hex}"
                )

                wallet_credit = (
                    await WalletService.credit(
                        operator_id=operator_id,
                        player_id=player_id,
                        amount=payout,
                        currency=currency,
                        transaction_id=(
                            payout_transaction_id
                        ),
                    )
                )

                if (
                    wallet_credit.get(
                        "status"
                    )
                    != "success"
                ):
                    raise ValueError(
                        "Wallet payout credit failed."
                    )

                payout_completed = True

                # Final balance after payout credit.
                wallet_balance = Decimal(
                    str(
                        wallet_credit.get(
                            "balance",
                            "0",
                        )
                    )
                )
                # -----------------------------------------------------
                # TEST ONLY: Force failure after payout credit
                # -----------------------------------------------------

                # raise ValueError(
                #     "TEST: Forced failure after payout credit."
                # )
            # =================================================
            # 12. FINAL BALANCE
            # =================================================

            new_balance = wallet_balance

            # =================================================
            # 13. CALCULATE ROUND NUMBER
            # =================================================

            round_number = (
                game.get(
                    "round_number",
                    0,
                )
                + 1
            )

            # =================================================
            # 14. DETERMINE GAME STATUS
            # =================================================

            game_status = (
                "completed"
                if not updated_remaining_deck
                else "active"
            )

            # =================================================
            # 15. PERSIST ROUND
            # =================================================

            round_data = {
                "game_id": game_id,
                "operator_id": operator_id,
                "player_id": player_id,

                "currency": currency,

                "round_number": (
                    round_number
                ),

                "bet_amount": (
                    bet_amount
                ),

                "prediction": (
                    prediction
                ),

                "previous_card": (
                    previous_card
                ),

                "next_card": (
                    next_card
                ),

                "result": result,

                "payout": payout,

                # ---------------------------------------------
                # WALLET TRANSACTION AUDIT
                # ---------------------------------------------

                "bet_transaction_id": (
                    bet_transaction_id
                ),

                "payout_transaction_id": (
                    payout_transaction_id
                ),

                "rollback_transaction_id": (
                    rollback_transaction_id
                ),

                "status": "completed",
            }

            round_id = (
                await HiLoRoundRepository.create_round(
                    round_data
                )
            )

            # =================================================
            # 16. UPDATE GAME
            # =================================================

            game_updated = (
                await HiLoGameRepository.update_game(
                    game_id,
                    {
                        "current_card": (
                            next_card
                        ),

                        "remaining_deck": (
                            updated_remaining_deck
                        ),

                        "balance": (
                            new_balance
                        ),

                        "current_round_id": (
                            round_id
                        ),

                        "round_number": (
                            round_number
                        ),

                        "status": (
                            game_status
                        ),
                    },
                )
            )

            if not game_updated:
                raise ValueError(
                    "Unable to update game."
                )

            # =================================================
            # 17. RETURN RESULT
            # =================================================

            return {
                "game_id": game_id,

                "round_id": round_id,

                "previous_card": (
                    previous_card
                ),

                "next_card": (
                    next_card
                ),

                "prediction": prediction,

                "result": result,

                "bet_amount": (
                    bet_amount
                ),

                "payout": payout,

                "currency": currency,

                "balance": (
                    new_balance
                ),
            }

        except Exception as exc:

            print(
                "ORIGINAL ERROR:",
                str(exc),
            )

            print(
                "debit_completed:",
                debit_completed,
            )

            print(
                "payout_completed:",
                payout_completed,
            )

            print(
                "bet_transaction_id:",
                bet_transaction_id,
            )

            print(
                "payout_transaction_id:",
                payout_transaction_id,
            )

            # =================================================
            # COMPENSATE PAYOUT TRANSACTION
            # =================================================

            if payout_completed and payout_transaction_id:

                try:

                    print(
                        "STARTING PAYOUT ROLLBACK"
                    )

                    payout_rollback_transaction_id = (
                        f"hilo_payout_rollback_{uuid4().hex}"
                    )

                    payout_rollback_response = (
                        await WalletService.rollback(
                            operator_id=operator_id,
                            player_id=player_id,
                            amount=payout,
                            currency=currency,
                            transaction_id=(
                                payout_rollback_transaction_id
                            ),
                            original_transaction_id=(
                                payout_transaction_id
                            ),
                        )
                    )

                    print(
                        "PAYOUT ROLLBACK RESPONSE:",
                        payout_rollback_response,
                    )

                    if (
                        payout_rollback_response.get(
                            "status"
                        )
                        != "success"
                    ):
                        raise ValueError(
                            "Payout rollback failed."
                        )

                except Exception as rollback_exc:

                    print(
                        "PAYOUT ROLLBACK FAILED:",
                        str(rollback_exc),
                    )

            # =================================================
            # COMPENSATE BET DEBIT TRANSACTION
            # =================================================

            if debit_completed and bet_transaction_id:

                try:

                    print(
                        "STARTING BET ROLLBACK"
                    )

                    bet_rollback_transaction_id = (
                        f"hilo_bet_rollback_{uuid4().hex}"
                    )

                    bet_rollback_response = (
                        await WalletService.rollback(
                            operator_id=operator_id,
                            player_id=player_id,
                            amount=bet_amount,
                            currency=currency,
                            transaction_id=(
                                bet_rollback_transaction_id
                            ),
                            original_transaction_id=(
                                bet_transaction_id
                            ),
                        )
                    )

                    print(
                        "BET ROLLBACK RESPONSE:",
                        bet_rollback_response,
                    )

                    if (
                        bet_rollback_response.get(
                            "status"
                        )
                        != "success"
                    ):
                        raise ValueError(
                            "Bet rollback failed."
                        )

                except Exception as rollback_exc:

                    print(
                        "BET ROLLBACK FAILED:",
                        str(rollback_exc),
                    )

            raise exc        
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

        rounds, total = (
            await HiLoRoundRepository.get_player_rounds(
                player_id=player_id,
                skip=skip,
                limit=limit,
            )
        )

        print("ROUNDS:", rounds)
        print("ROUNDS TYPE:", type(rounds))
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

        A game may only be cancelled by its owner and
        only while its status is ACTIVE.
        """

        # -----------------------------------------------------
        # 1. Get game
        # -----------------------------------------------------

        game = await HiLoGameRepository.get_game_by_id(
            game_id
        )

        if not game:
            raise ValueError(
                "Game not found."
            )

        # -----------------------------------------------------
        # 2. Ownership validation
        # -----------------------------------------------------

        if game["player_id"] != player_id:
            raise ValueError(
                "You do not have permission to cancel this game."
            )

        # -----------------------------------------------------
        # 3. Validate lifecycle state
        # -----------------------------------------------------

        if (
            game["status"]
            != GameStatus.ACTIVE.value
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Only active games can be cancelled."
                ),
            )

        # -----------------------------------------------------
        # 4. Cancel game
        # -----------------------------------------------------

        updated = (
            await HiLoGameRepository.update_game_if_active(
                game_id=game_id,
                update_data={
                    "status": GameStatus.CANCELLED.value,
                },
            )
        )

        if not updated:
            raise ValueError(
                "Game could not be cancelled."
            )

        # -----------------------------------------------------
        # 5. Return result
        # -----------------------------------------------------

        return {
            "game_id": game_id,
            "status": GameStatus.CANCELLED.value,
            "message": "Game cancelled successfully.",
        }