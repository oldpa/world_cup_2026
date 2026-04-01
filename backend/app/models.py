from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SimulationParams(BaseModel):
    variance: float = Field(default=0.35, ge=0.0, le=1.0)
    draw_bias: float = Field(default=0.0, ge=-0.2, le=0.2)
    home_advantage: float = Field(default=35.0, ge=-150.0, le=150.0)
    elo_scale: float = Field(default=400.0, gt=0.0)
    seed: int | None = Field(default=None)


class MultiSimulationParams(SimulationParams):
    runs: int = Field(default=200, ge=1, le=5000)
    highlight_team: str = Field(default="Sweden")


class GroupStanding(BaseModel):
    team: str
    group: str
    played: int
    points: int
    goals_for: int
    goals_against: int
    goal_difference: int
    wins: int
    draws: int
    losses: int
    position: int


class MatchResult(BaseModel):
    match_id: str
    stage: str
    group: str | None
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    winner: str | None
    decided_by: Literal["normal", "extra_time", "penalties", "group_draw"]


class SimulationResult(BaseModel):
    champion: str
    runner_up: str
    third_place: str
    fourth_place: str
    group_tables: dict[str, list[GroupStanding]]
    matches: list[MatchResult]


class AggregateTeamStats(BaseModel):
    team: str
    champion_pct: float
    finalist_pct: float
    semifinal_pct: float
    quarter_pct: float
    top8_pct: float
    top16_pct: float
    top32_pct: float


class MultiSimulationResult(BaseModel):
    runs: int
    aggregate: list[AggregateTeamStats]
    highlight_team: str
    highlight_best_placement: str
    highlight_best_journey: list[MatchResult]
