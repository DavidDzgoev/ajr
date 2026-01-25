"""Rating calculators for different rating systems."""

import logging
import math
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class RatingCalculator(ABC):
    """Base class for rating calculators."""

    @abstractmethod
    def calculate_rating_change(
        self,
        player_rating: float,
        opponent_rating: float,
        result: float,  # 1.0 for win, 0.5 for draw, 0.0 for loss
        **kwargs: Any,
    ) -> dict[str, float]:
        """
        Calculate rating change after a match.

        Args:
            player_rating: Current rating of the player.
            opponent_rating: Current rating of the opponent.
            result: Match result (1.0 = win, 0.5 = draw, 0.0 = loss).
            **kwargs: Additional parameters specific to the calculator.

        Returns:
            Dictionary with new rating and other relevant values.
        """
        pass

    @abstractmethod
    def get_initial_rating(self) -> dict[str, float]:
        """
        Get initial rating values for a new player.

        Returns:
            Dictionary with initial rating values.
        """
        pass


class EloCalculator(RatingCalculator):
    """Elo rating system calculator."""

    def __init__(self, k_factor: float = 32.0, initial_rating: float = 1500.0) -> None:
        """
        Initialize Elo calculator.

        Args:
            k_factor: K-factor for Elo calculation (default: 32).
            initial_rating: Initial rating for new players (default: 1500).
        """
        self.k_factor = k_factor
        self.initial_rating = initial_rating

    def expected_score(self, player_rating: float, opponent_rating: float) -> float:
        """
        Calculate expected score based on ratings.

        Args:
            player_rating: Player's rating.
            opponent_rating: Opponent's rating.

        Returns:
            Expected score (0.0 to 1.0).
        """
        return 1.0 / (1.0 + 10.0 ** ((opponent_rating - player_rating) / 400.0))

    def calculate_rating_change(
        self,
        player_rating: float,
        opponent_rating: float,
        result: float,
        **kwargs: Any,
    ) -> dict[str, float]:
        """
        Calculate Elo rating change.

        Args:
            player_rating: Current rating of the player.
            opponent_rating: Current rating of the opponent.
            result: Match result (1.0 = win, 0.5 = draw, 0.0 = loss).
            **kwargs: Additional parameters (not used for Elo).

        Returns:
            Dictionary with 'rating' (new rating) and 'rating_change' (change amount).
        """
        expected = self.expected_score(player_rating, opponent_rating)
        rating_change = self.k_factor * (result - expected)
        new_rating = player_rating + rating_change

        return {
            "rating": new_rating,
            "rating_change": rating_change,
        }

    def get_initial_rating(self) -> dict[str, float]:
        """Get initial Elo rating."""
        return {"rating": self.initial_rating}


class GlickoCalculator(RatingCalculator):
    """Glicko-2 rating system calculator."""

    def __init__(
        self,
        initial_rating: float = 1500.0,
        initial_rd: float = 350.0,
        initial_volatility: float = 0.06,
        tau: float = 0.5,
    ) -> None:
        """
        Initialize Glicko-2 calculator.

        Args:
            initial_rating: Initial rating (default: 1500).
            initial_rd: Initial rating deviation (default: 350).
            initial_volatility: Initial volatility (default: 0.06).
            tau: System constant (default: 0.5).
        """
        self.initial_rating = initial_rating
        self.initial_rd = initial_rd
        self.initial_volatility = initial_volatility
        self.tau = tau

    def g(self, rd: float) -> float:
        """Calculate g(RD) function."""
        return 1.0 / math.sqrt(1.0 + 3.0 * (rd**2) / (math.pi**2))

    def expected_score(
        self, player_rating: float, opponent_rating: float, opponent_rd: float
    ) -> float:
        """
        Calculate expected score.

        Args:
            player_rating: Player's rating.
            opponent_rating: Opponent's rating.
            opponent_rd: Opponent's rating deviation.

        Returns:
            Expected score (0.0 to 1.0).
        """
        g_rd = self.g(opponent_rd)
        return 1.0 / (1.0 + math.exp(-g_rd * (player_rating - opponent_rating)))

    def calculate_rating_change(
        self,
        player_rating: float,
        opponent_rating: float,
        result: float,
        player_rd: float | None = None,
        opponent_rd: float | None = None,
        player_volatility: float | None = None,
        **kwargs: Any,
    ) -> dict[str, float]:
        """
        Calculate Glicko-2 rating change.

        Args:
            player_rating: Current rating of the player.
            opponent_rating: Current rating of the opponent.
            result: Match result (1.0 = win, 0.5 = draw, 0.0 = loss).
            player_rd: Player's rating deviation (default: initial_rd).
            opponent_rd: Opponent's rating deviation (default: initial_rd).
            player_volatility: Player's volatility (default: initial_volatility).
            **kwargs: Additional parameters (not used).

        Returns:
            Dictionary with new rating, rd, volatility, and rating_change.
        """
        if player_rd is None:
            player_rd = self.initial_rd
        if opponent_rd is None:
            opponent_rd = self.initial_rd
        if player_volatility is None:
            player_volatility = self.initial_volatility

        # Step 1: Convert rating and RD to Glicko-2 scale
        mu = (player_rating - 1500.0) / 173.7178
        phi = player_rd / 173.7178

        # Step 2: Calculate v (variance)
        g_opponent_rd = self.g(opponent_rd)
        expected = self.expected_score(player_rating, opponent_rating, opponent_rd)
        v = 1.0 / (g_opponent_rd**2 * expected * (1.0 - expected))

        # Step 3: Calculate delta
        delta = v * g_opponent_rd * (result - expected)

        # Step 4: Update volatility (simplified version)
        # Full Glicko-2 uses iterative method, but we'll use a simplified approach
        new_volatility = player_volatility  # In full implementation, this would be calculated

        # Step 5: Update phi (RD)
        phi_star = math.sqrt(phi**2 + new_volatility**2)
        new_phi = 1.0 / math.sqrt(1.0 / phi_star**2 + 1.0 / v)

        # Step 6: Update mu (rating)
        new_mu = mu + new_phi**2 * g_opponent_rd * (result - expected)

        # Step 7: Convert back to Glicko scale
        new_rating = 173.7178 * new_mu + 1500.0
        new_rd = 173.7178 * new_phi

        rating_change = new_rating - player_rating

        return {
            "rating": new_rating,
            "rating_deviation": new_rd,
            "volatility": new_volatility,
            "rating_change": rating_change,
        }

    def get_initial_rating(self) -> dict[str, float]:
        """Get initial Glicko-2 rating."""
        return {
            "rating": self.initial_rating,
            "rating_deviation": self.initial_rd,
            "volatility": self.initial_volatility,
        }


def get_calculator(formula_type: str, config: dict[str, Any]) -> RatingCalculator:
    """
    Factory function to get appropriate calculator.

    Args:
        formula_type: Type of rating system ("elo", "glicko", etc.).
        config: Configuration dictionary for the calculator.

    Returns:
        RatingCalculator instance.

    Raises:
        ValueError: If formula_type is not supported.
    """
    if formula_type == "elo":
        k_factor = config.get("k_factor", 32.0)
        initial_rating = config.get("initial_rating", 1500.0)
        return EloCalculator(k_factor=k_factor, initial_rating=initial_rating)
    elif formula_type == "glicko":
        initial_rating = config.get("initial_rating", 1500.0)
        initial_rd = config.get("initial_rd", 350.0)
        initial_volatility = config.get("initial_volatility", 0.06)
        tau = config.get("tau", 0.5)
        return GlickoCalculator(
            initial_rating=initial_rating,
            initial_rd=initial_rd,
            initial_volatility=initial_volatility,
            tau=tau,
        )
    else:
        raise ValueError(f"Unsupported formula type: {formula_type}")
