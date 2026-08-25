"""
Module: config.game.hilo_config

Description:
    Configuration for the Hi-Lo game.

This configuration keeps game rules separate from
the service and engine so the same game can later
be deployed for different operators/platforms.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class HiLoGameConfig:
    """
    Configurable Hi-Lo game rules.
    """

    # Betting limits
    min_bet: Decimal = Decimal("1.00")
    max_bet: Decimal = Decimal("100.00")

    # Payout rules
    win_payout_multiplier: Decimal = Decimal("2.00")

    # Equal-card behavior
    push_returns_bet: bool = True


# Default configuration for the current game.
HILO_GAME_CONFIG = HiLoGameConfig()