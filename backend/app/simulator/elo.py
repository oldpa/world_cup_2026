from __future__ import annotations

import random
from typing import Literal


Outcome = Literal["home", "away", "draw"]


def expected_home_win_probability(
    home_rating: float,
    away_rating: float,
    home_advantage: float,
    scale: float,
) -> float:
    delta = away_rating - (home_rating + home_advantage)
    return 1.0 / (1.0 + 10 ** (delta / scale))


def _temperature_adjust(probabilities: list[float], temperature: float) -> list[float]:
    if temperature <= 0:
        return probabilities
    adjusted = [p ** (1.0 / temperature) for p in probabilities]
    total = sum(adjusted)
    if total <= 0:
        return probabilities
    return [p / total for p in adjusted]


def outcome_probabilities(
    home_rating: float,
    away_rating: float,
    home_advantage: float,
    draw_bias: float,
    variance: float,
    scale: float,
) -> tuple[float, float, float]:
    p_home_raw = expected_home_win_probability(
        home_rating=home_rating,
        away_rating=away_rating,
        home_advantage=home_advantage,
        scale=scale,
    )
    rating_gap = abs(home_rating - away_rating)
    base_draw = max(0.16, 0.28 - (rating_gap / 4000.0))
    p_draw = min(0.45, max(0.06, base_draw + draw_bias))
    p_home = p_home_raw * (1.0 - p_draw)
    p_away = (1.0 - p_home_raw) * (1.0 - p_draw)
    temperature = 1.0 + (variance * 2.0)
    p_home, p_draw, p_away = _temperature_adjust([p_home, p_draw, p_away], temperature)
    return p_home, p_draw, p_away


def sample_outcome(
    rng: random.Random,
    home_rating: float,
    away_rating: float,
    home_advantage: float,
    draw_bias: float,
    variance: float,
    scale: float,
) -> Outcome:
    p_home, p_draw, p_away = outcome_probabilities(
        home_rating=home_rating,
        away_rating=away_rating,
        home_advantage=home_advantage,
        draw_bias=draw_bias,
        variance=variance,
        scale=scale,
    )
    roll = rng.random()
    if roll < p_home:
        return "home"
    if roll < p_home + p_draw:
        return "draw"
    return "away"


def sample_scoreline(rng: random.Random, outcome: Outcome, knockout: bool) -> tuple[int, int]:
    if outcome == "draw":
        draw_scores = [(0, 0), (1, 1), (2, 2), (3, 3)]
        weights = [0.32, 0.44, 0.2, 0.04]
        return rng.choices(draw_scores, weights=weights, k=1)[0]

    if outcome == "home":
        score_options = [(1, 0), (2, 0), (2, 1), (3, 1), (3, 0), (4, 1)]
        weights = [0.26, 0.22, 0.24, 0.14, 0.1, 0.04]
        return rng.choices(score_options, weights=weights, k=1)[0]

    score_options = [(0, 1), (0, 2), (1, 2), (1, 3), (0, 3), (1, 4)]
    weights = [0.26, 0.22, 0.24, 0.14, 0.1, 0.04]
    return rng.choices(score_options, weights=weights, k=1)[0]


def decide_knockout_winner_after_draw(
    rng: random.Random,
    home_team: str,
    away_team: str,
    home_rating: float,
    away_rating: float,
    home_advantage: float,
    scale: float,
) -> tuple[str, Literal["extra_time", "penalties"]]:
    p_home = expected_home_win_probability(home_rating, away_rating, home_advantage, scale)
    decided_by = "extra_time" if rng.random() < 0.55 else "penalties"
    winner = home_team if rng.random() < p_home else away_team
    return winner, decided_by
