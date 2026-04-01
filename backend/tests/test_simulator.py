from pathlib import Path

from app.models import SimulationParams
from app.simulator.elo import outcome_probabilities
from app.simulator.normalization import canonical_team_name
from app.simulator.tournament import aggregate_runs, simulate_tournament


def test_team_name_normalization() -> None:
    assert canonical_team_name("IR Iran") == "IR Iran"
    assert canonical_team_name("Türkiye") == "Türkiye"
    assert canonical_team_name("Korea Republic") == "Korea Republic"
    assert canonical_team_name("Cote d'Ivoire") == "Côte d'Ivoire"


def test_elo_outcome_probabilities_sum() -> None:
    probs = outcome_probabilities(
        home_rating=1700,
        away_rating=1600,
        home_advantage=35,
        draw_bias=0.0,
        variance=0.35,
        scale=400,
    )
    assert len(probs) == 3
    assert abs(sum(probs) - 1.0) < 1e-9


def test_full_tournament_simulation_smoke() -> None:
    root = Path(__file__).resolve().parents[2]
    result = simulate_tournament(
        matches_csv=root / "world_cup_2026_simulation_matches.csv",
        rankings_csv=root / "fifa_rank.csv",
        params=SimulationParams(seed=123),
    )
    assert result.champion
    assert result.runner_up
    assert len(result.group_tables) == 12
    assert len(result.matches) > 100


def test_aggregate_runs_smoke() -> None:
    root = Path(__file__).resolve().parents[2]
    aggregate = aggregate_runs(
        matches_csv=root / "world_cup_2026_simulation_matches.csv",
        rankings_csv=root / "fifa_rank.csv",
        params=SimulationParams(),
        runs=20,
    )
    assert aggregate["runs"] == 20
    assert len(aggregate["aggregate"]) > 0
