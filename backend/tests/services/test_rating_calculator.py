from collections.abc import Generator

import pytest

from app.services.rating_calculator import (
    EloCalculator,
    GlickoCalculator,
    get_calculator,
)


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[None, None, None]:
    yield


def test_glicko2_calculate_rating_change_updates_all_components() -> None:
    calculator = GlickoCalculator(tau=0.5, epsilon=1e-6)

    result = calculator.calculate_rating_change(
        player_rating=1500.0,
        opponent_rating=1400.0,
        result=1.0,
        player_rd=200.0,
        opponent_rd=30.0,
        player_volatility=0.06,
    )

    assert result["rating"] == pytest.approx(1563.5641943063383, rel=1e-12)
    assert result["rating_deviation"] == pytest.approx(175.402655938555, rel=1e-12)
    assert result["volatility"] == pytest.approx(0.059998657304847616, rel=1e-12)
    assert result["rating_change"] == pytest.approx(63.56419430633832, rel=1e-12)


def test_glicko2_volatility_reacts_to_unexpected_result() -> None:
    calculator = GlickoCalculator(tau=0.5, epsilon=1e-6)

    upset_win = calculator.calculate_rating_change(
        player_rating=1500.0,
        opponent_rating=1800.0,
        result=1.0,
        player_rd=80.0,
        opponent_rd=50.0,
        player_volatility=0.06,
    )
    expected_loss = calculator.calculate_rating_change(
        player_rating=1500.0,
        opponent_rating=1800.0,
        result=0.0,
        player_rd=80.0,
        opponent_rd=50.0,
        player_volatility=0.06,
    )

    assert upset_win["volatility"] > 0.06
    assert expected_loss["volatility"] < 0.06


def test_get_calculator_passes_epsilon_to_glicko() -> None:
    calculator = get_calculator(
        "glicko",
        {
            "initial_rating": 1600.0,
            "initial_rd": 120.0,
            "initial_volatility": 0.07,
            "tau": 0.7,
            "epsilon": 1e-8,
        },
    )

    assert isinstance(calculator, GlickoCalculator)
    assert calculator.initial_rating == 1600.0
    assert calculator.initial_rd == 120.0
    assert calculator.initial_volatility == 0.07
    assert calculator.tau == 0.7
    assert calculator.epsilon == 1e-8


def test_elo_expected_score_equal_ratings_is_half() -> None:
    calculator = EloCalculator()
    assert calculator.expected_score(1500.0, 1500.0) == pytest.approx(0.5)


def test_elo_rating_change_win_against_equal_rating() -> None:
    calculator = EloCalculator(k_factor=32.0, initial_rating=1500.0)
    result = calculator.calculate_rating_change(
        player_rating=1500.0,
        opponent_rating=1500.0,
        result=1.0,
    )

    assert result["rating"] == pytest.approx(1516.0)
    assert result["rating_change"] == pytest.approx(16.0)


def test_elo_rating_change_draw_when_favored_decreases_rating() -> None:
    calculator = EloCalculator(k_factor=32.0, initial_rating=1500.0)
    result = calculator.calculate_rating_change(
        player_rating=1600.0,
        opponent_rating=1400.0,
        result=0.5,
    )

    expected_score = calculator.expected_score(1600.0, 1400.0)
    assert expected_score > 0.5
    assert result["rating_change"] == pytest.approx(32.0 * (0.5 - expected_score))
    assert result["rating"] == pytest.approx(1600.0 + result["rating_change"])
    assert result["rating_change"] < 0


def test_get_calculator_passes_elo_config() -> None:
    calculator = get_calculator(
        "elo",
        {
            "k_factor": 24.0,
            "initial_rating": 1700.0,
        },
    )

    assert isinstance(calculator, EloCalculator)
    assert calculator.k_factor == 24.0
    assert calculator.initial_rating == 1700.0
