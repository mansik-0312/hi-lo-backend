"""
Module: services.game.hilo_engine

Description:
    Core deterministic game engine for the Hi-Lo card game.

Responsibilities:
    - Create and shuffle decks.
    - Draw cards.
    - Compare cards.
    - Determine Higher/Lower outcomes.
    - Calculate payouts.

This module must not:
    - Access MongoDB.
    - Access HTTP requests.
    - Access FastAPI dependencies.
    - Modify player wallets.

The engine contains pure game logic so it can be tested independently.
"""

import random
from typing import Dict, List, Tuple


class HiLoGameEngine:
    """
    Core engine for the Hi-Lo card game.

    A standard 52-card deck is used.

    Card values:
        Ace   = 14
        2-10  = face value
        Jack  = 11
        Queen = 12
        King  = 13
    """

    SUITS = (
        "clubs",
        "diamonds",
        "hearts",
        "spades",
    )

    RANKS = (
        ("2", 2),
        ("3", 3),
        ("4", 4),
        ("5", 5),
        ("6", 6),
        ("7", 7),
        ("8", 8),
        ("9", 9),
        ("10", 10),
        ("J", 11),
        ("Q", 12),
        ("K", 13),
        ("A", 14),
    )

    @classmethod
    def create_deck(cls) -> List[Dict]:
        """
        Create a standard 52-card deck.

        Returns:
            A list containing all 52 cards.
        """

        return [
            {
                "rank": rank,
                "suit": suit,
                "value": value,
            }
            for suit in cls.SUITS
            for rank, value in cls.RANKS
        ]

    @classmethod
    def shuffle_deck(
        cls,
        deck: List[Dict],
    ) -> List[Dict]:
        """
        Shuffle a deck in place.

        Args:
            deck:
                List of card dictionaries.

        Returns:
            The shuffled deck.
        """

        random.shuffle(deck)

        return deck

    @classmethod
    def draw_card(
        cls,
        deck: List[Dict],
    ) -> Tuple[Dict, List[Dict]]:
        """
        Draw the top card from the deck.

        Args:
            deck:
                Remaining deck.

        Returns:
            Tuple containing:
                - drawn card
                - remaining deck

        Raises:
            ValueError:
                If no cards remain.
        """

        if not deck:
            raise ValueError(
                "No cards remain in the deck."
            )

        card = deck[0]

        return card, deck[1:]

    @staticmethod
    def compare_cards(
        previous_card: Dict,
        next_card: Dict,
    ) -> str:
        """
        Compare two cards.

        Args:
            previous_card:
                Previously revealed card.

            next_card:
                Newly revealed card.

        Returns:
            One of:
                "higher"
                "lower"
                "equal"
        """

        previous_value = previous_card["value"]
        next_value = next_card["value"]

        if next_value > previous_value:
            return "higher"

        if next_value < previous_value:
            return "lower"

        return "equal"

    @classmethod
    def evaluate_prediction(
        cls,
        prediction: str,
        previous_card: Dict,
        next_card: Dict,
    ) -> str:
        """
        Determine the result of a player's prediction.

        Args:
            prediction:
                Player prediction: "higher" or "lower".

            previous_card:
                Previously visible card.

            next_card:
                Newly drawn card.

        Returns:
            "win", "loss", or "push".
        """

        actual_result = cls.compare_cards(
            previous_card,
            next_card,
        )

        if actual_result == "equal":
            return "push"

        if prediction == actual_result:
            return "win"

        return "loss"

    @staticmethod
    def calculate_payout(
        bet_amount: float,
        result: str,
        payout_multiplier: float,
    ) -> float:
        """
        Calculate the payout for a round.

        Current MVP rules:

            Win:
                Returns bet × payout multiplier.

            Push:
                Returns original bet.

            Loss:
                Returns zero.

        Args:
            bet_amount:
                Amount wagered.

            result:
                Round result.

            payout_multiplier:
                Winning payout multiplier.

        Returns:
            Payout amount.
        """

        if result == "win":
            return bet_amount * payout_multiplier

        if result == "push":
            return bet_amount

        return 0.0