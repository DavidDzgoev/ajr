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
        epsilon: float = 1e-6,
    ) -> None:
        """
        Initialize Glicko-2 calculator.

        Args:
            initial_rating: Initial rating (default: 1500).
            initial_rd: Initial rating deviation (default: 350).
            initial_volatility: Initial volatility (default: 0.06).
            tau: System constant (default: 0.5).
            epsilon: Convergence tolerance for volatility iteration.
        """
        self.initial_rating = initial_rating
        self.initial_rd = initial_rd
        self.initial_volatility = initial_volatility
        self.tau = tau
        self.epsilon = epsilon

    @staticmethod
    def _scale_down_rating(rating: float) -> float:
        """Convert rating from Glicko scale to Glicko-2 scale."""
        return (rating - 1500.0) / 173.7178

    @staticmethod
    def _scale_up_rating(mu: float) -> float:
        """Convert rating from Glicko-2 scale to Glicko scale."""
        return 173.7178 * mu + 1500.0

    @staticmethod
    def _scale_down_rd(rd: float) -> float:
        """Convert RD from Glicko scale to Glicko-2 scale."""
        return rd / 173.7178

    @staticmethod
    def _scale_up_rd(phi: float) -> float:
        """Convert RD from Glicko-2 scale to Glicko scale."""
        return 173.7178 * phi

    def g(self, phi: float) -> float:
        """Calculate g(phi) function for RD on Glicko-2 scale."""
        return 1.0 / math.sqrt(1.0 + (3.0 * phi**2) / (math.pi**2))

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
        mu = self._scale_down_rating(player_rating)
        mu_opponent = self._scale_down_rating(opponent_rating)
        phi_opponent = self._scale_down_rd(opponent_rd)
        g_phi = self.g(phi_opponent)
        return 1.0 / (1.0 + math.exp(-g_phi * (mu - mu_opponent)))

    def _calculate_new_volatility(
        self, phi: float, delta: float, v: float, sigma: float
    ) -> float:
        """
        Calculate updated volatility using the iterative Glicko-2 algorithm.

        Args:
            phi: Current player RD on Glicko-2 scale.
            delta: Estimated improvement (Glicko-2 scale).
            v: Estimated variance.
            sigma: Current volatility.

        Returns:
            Updated volatility.
        """

        a = math.log(sigma**2)
        tau_sq = self.tau**2

        def f(x: float) -> float:
            exp_x = math.exp(x)
            num = exp_x * (delta**2 - phi**2 - v - exp_x)
            den = 2.0 * (phi**2 + v + exp_x) ** 2
            return (num / den) - ((x - a) / tau_sq)

        a_bound = a
        if delta**2 > phi**2 + v:
            b_bound = math.log(delta**2 - phi**2 - v)
        else:
            k = 1
            while f(a - k * self.tau) < 0:
                k += 1
            b_bound = a - k * self.tau

        f_a = f(a_bound)
        f_b = f(b_bound)

        while abs(b_bound - a_bound) > self.epsilon:
            c_bound = a_bound + ((a_bound - b_bound) * f_a / (f_b - f_a))
            f_c = f(c_bound)

            if f_c * f_b < 0:
                a_bound = b_bound
                f_a = f_b
            else:
                f_a /= 2.0

            b_bound = c_bound
            f_b = f_c

        return math.exp(a_bound / 2.0)

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
        mu = self._scale_down_rating(player_rating)
        phi = self._scale_down_rd(player_rd)
        mu_opponent = self._scale_down_rating(opponent_rating)
        phi_opponent = self._scale_down_rd(opponent_rd)

        # Step 2: Calculate v (variance)
        g_opponent = self.g(phi_opponent)
        expected = 1.0 / (1.0 + math.exp(-g_opponent * (mu - mu_opponent)))
        v = 1.0 / (g_opponent**2 * expected * (1.0 - expected))

        # Step 3: Calculate delta
        delta = v * g_opponent * (result - expected)

        # Step 4: Update volatility (iterative Glicko-2 algorithm)
        new_volatility = self._calculate_new_volatility(
            phi=phi, delta=delta, v=v, sigma=player_volatility
        )

        # Step 5: Update phi (RD)
        phi_star = math.sqrt(phi**2 + new_volatility**2)
        new_phi = 1.0 / math.sqrt(1.0 / phi_star**2 + 1.0 / v)

        # Step 6: Update mu (rating)
        new_mu = mu + new_phi**2 * g_opponent * (result - expected)

        # Step 7: Convert back to Glicko scale
        new_rating = self._scale_up_rating(new_mu)
        new_rd = self._scale_up_rd(new_phi)

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
        epsilon = config.get("epsilon", 1e-6)
        return GlickoCalculator(
            initial_rating=initial_rating,
            initial_rd=initial_rd,
            initial_volatility=initial_volatility,
            tau=tau,
            epsilon=epsilon,
        )
    else:
        raise ValueError(f"Unsupported formula type: {formula_type}")
