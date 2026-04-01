from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    AggregateTeamStats,
    MultiSimulationParams,
    MultiSimulationResult,
    SimulationParams,
    SimulationResult,
)
from app.simulator.tournament import aggregate_runs, simulate_tournament

ROOT_DIR = Path(__file__).resolve().parents[2]
MATCHES_CSV = ROOT_DIR / "world_cup_2026_simulation_matches.csv"
RANKINGS_CSV = ROOT_DIR / "fifa_rank.csv"

app = FastAPI(title="World Cup 2026 Simulator API", version="0.1.0")

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]
allowed_origin_regex = os.getenv(
    "ALLOWED_ORIGIN_REGEX",
    r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
)
allow_all_origins = os.getenv("ALLOW_ALL_ORIGINS", "false").lower() == "true"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else allowed_origins,
    allow_origin_regex=None if allow_all_origins or allowed_origins else allowed_origin_regex,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/simulate", response_model=SimulationResult)
def simulate(payload: SimulationParams) -> SimulationResult:
    return simulate_tournament(MATCHES_CSV, RANKINGS_CSV, payload)


@app.post("/simulate/many", response_model=MultiSimulationResult)
def simulate_many(payload: MultiSimulationParams) -> MultiSimulationResult:
    aggregate = aggregate_runs(
        matches_csv=MATCHES_CSV,
        rankings_csv=RANKINGS_CSV,
        params=SimulationParams(
            variance=payload.variance,
            draw_bias=payload.draw_bias,
            home_advantage=payload.home_advantage,
            elo_scale=payload.elo_scale,
            seed=payload.seed,
        ),
        runs=payload.runs,
        highlight_team=payload.highlight_team,
    )
    return MultiSimulationResult(
        runs=aggregate["runs"],
        aggregate=[AggregateTeamStats(**row) for row in aggregate["aggregate"]],
        highlight_team=aggregate["highlight_team"],
        highlight_best_placement=aggregate["highlight_best_placement"],
        highlight_best_journey=aggregate["highlight_best_journey"],
    )
