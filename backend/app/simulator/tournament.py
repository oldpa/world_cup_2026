from __future__ import annotations

import csv
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.models import GroupStanding, MatchResult, SimulationParams, SimulationResult
from app.simulator.elo import (
    decide_knockout_winner_after_draw,
    sample_outcome,
    sample_scoreline,
)
from app.simulator.normalization import canonical_team_name


@dataclass
class Fixture:
    match_id: str
    date: str
    stage: str
    group: str | None
    home_slot: str
    away_slot: str
    home_code: str
    away_code: str
    home_dep_match: str | None
    away_dep_match: str | None


@dataclass
class TeamTableRow:
    team: str
    group: str
    played: int = 0
    points: int = 0
    goals_for: int = 0
    goals_against: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against


def _is_group_stage(fixture: Fixture) -> bool:
    return fixture.stage.strip() == "Group Stage"


def _numeric_match_id(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits or value


def _load_rankings(rankings_csv: Path) -> dict[str, float]:
    ratings: dict[str, float] = {}
    with rankings_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_name = (row.get("team") or "").strip()
            raw_points = (row.get("points") or "").strip()
            if not raw_name or not raw_points:
                continue
            team = canonical_team_name(raw_name)
            if team in ratings:
                # Keep first seen entry if duplicate rows are present.
                continue
            ratings[team] = float(raw_points)
    return ratings


def _load_fixtures(matches_csv: Path) -> list[Fixture]:
    fixtures: list[Fixture] = []
    with matches_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            match_id = (row.get("match_id") or "").strip()
            if not match_id:
                continue
            fixtures.append(
                Fixture(
                    match_id=match_id,
                    date=(row.get("date") or "").strip(),
                    stage=(row.get("stage") or "").strip(),
                    group=((row.get("group") or "").strip() or None),
                    home_slot=(row.get("home_slot") or "").strip(),
                    away_slot=(row.get("away_slot") or "").strip(),
                    home_code=(row.get("home_code") or "").strip(),
                    away_code=(row.get("away_code") or "").strip(),
                    home_dep_match=((row.get("home_dep_match") or "").strip() or None),
                    away_dep_match=((row.get("away_dep_match") or "").strip() or None),
                )
            )
    return fixtures


def _collect_fixture_teams(fixtures: list[Fixture]) -> set[str]:
    teams: set[str] = set()
    for fx in fixtures:
        if _is_group_stage(fx):
            teams.add(canonical_team_name(fx.home_slot))
            teams.add(canonical_team_name(fx.away_slot))
    return teams


def _validate_data(fixtures: list[Fixture], ratings: dict[str, float]) -> None:
    missing = sorted(t for t in _collect_fixture_teams(fixtures) if t not in ratings)
    if missing:
        missing_joined = ", ".join(missing)
        raise ValueError(f"Missing ratings for: {missing_joined}")


def _init_group_table(fixtures: list[Fixture]) -> dict[str, dict[str, TeamTableRow]]:
    groups: dict[str, dict[str, TeamTableRow]] = defaultdict(dict)
    for fx in fixtures:
        if not _is_group_stage(fx) or not fx.group:
            continue
        group = fx.group
        home = canonical_team_name(fx.home_slot)
        away = canonical_team_name(fx.away_slot)
        if home not in groups[group]:
            groups[group][home] = TeamTableRow(team=home, group=group)
        if away not in groups[group]:
            groups[group][away] = TeamTableRow(team=away, group=group)
    return groups


def _apply_group_result(
    row_home: TeamTableRow,
    row_away: TeamTableRow,
    home_goals: int,
    away_goals: int,
) -> None:
    row_home.played += 1
    row_away.played += 1
    row_home.goals_for += home_goals
    row_home.goals_against += away_goals
    row_away.goals_for += away_goals
    row_away.goals_against += home_goals
    if home_goals > away_goals:
        row_home.points += 3
        row_home.wins += 1
        row_away.losses += 1
    elif away_goals > home_goals:
        row_away.points += 3
        row_away.wins += 1
        row_home.losses += 1
    else:
        row_home.points += 1
        row_away.points += 1
        row_home.draws += 1
        row_away.draws += 1


def _head_to_head_stats(
    tied_teams: list[str],
    group_matches: list[MatchResult],
) -> dict[str, TeamTableRow]:
    stats = {team: TeamTableRow(team=team, group="") for team in tied_teams}
    tied_set = set(tied_teams)
    for m in group_matches:
        if m.home_team not in tied_set or m.away_team not in tied_set:
            continue
        _apply_group_result(
            stats[m.home_team],
            stats[m.away_team],
            m.home_goals,
            m.away_goals,
        )
    return stats


def _sort_teams_with_tiebreak(
    teams: list[str],
    table_rows: dict[str, TeamTableRow],
    group_matches: list[MatchResult],
    ratings: dict[str, float],
) -> list[str]:
    teams = sorted(
        teams,
        key=lambda t: (
            table_rows[t].points,
            table_rows[t].goal_difference,
            table_rows[t].goals_for,
        ),
        reverse=True,
    )
    resolved: list[str] = []
    idx = 0
    while idx < len(teams):
        pivot = table_rows[teams[idx]]
        tie_group = [teams[idx]]
        idx += 1
        while idx < len(teams):
            nxt = table_rows[teams[idx]]
            if (
                nxt.points == pivot.points
                and nxt.goal_difference == pivot.goal_difference
                and nxt.goals_for == pivot.goals_for
            ):
                tie_group.append(teams[idx])
                idx += 1
            else:
                break
        if len(tie_group) == 1:
            resolved.extend(tie_group)
            continue
        h2h = _head_to_head_stats(tie_group, group_matches)
        tie_group_sorted = sorted(
            tie_group,
            key=lambda t: (
                h2h[t].points,
                h2h[t].goal_difference,
                h2h[t].goals_for,
                ratings.get(t, 0.0),
                t,
            ),
            reverse=True,
        )
        resolved.extend(tie_group_sorted)
    return resolved


def _sorted_group_tables(
    group_table: dict[str, dict[str, TeamTableRow]],
    group_matches: dict[str, list[MatchResult]],
    ratings: dict[str, float],
) -> dict[str, list[GroupStanding]]:
    output: dict[str, list[GroupStanding]] = {}
    for group, rows in sorted(group_table.items()):
        order = _sort_teams_with_tiebreak(
            teams=list(rows.keys()),
            table_rows=rows,
            group_matches=group_matches[group],
            ratings=ratings,
        )
        standings: list[GroupStanding] = []
        for pos, team in enumerate(order, start=1):
            row = rows[team]
            standings.append(
                GroupStanding(
                    team=team,
                    group=group,
                    played=row.played,
                    points=row.points,
                    goals_for=row.goals_for,
                    goals_against=row.goals_against,
                    goal_difference=row.goal_difference,
                    wins=row.wins,
                    draws=row.draws,
                    losses=row.losses,
                    position=pos,
                )
            )
        output[group] = standings
    return output


def _rank_third_place_teams(group_tables: dict[str, list[GroupStanding]], ratings: dict[str, float]) -> list[GroupStanding]:
    third_place = [rows[2] for rows in group_tables.values() if len(rows) >= 3]
    return sorted(
        third_place,
        key=lambda row: (
            row.points,
            row.goal_difference,
            row.goals_for,
            ratings.get(row.team, 0.0),
            row.team,
        ),
        reverse=True,
    )


def _slot_team_from_code(
    code: str,
    group_tables: dict[str, list[GroupStanding]],
    results_by_match: dict[str, MatchResult],
    dep_match_id: str | None,
) -> str:
    if not code:
        raise ValueError("Missing slot code")
    if re.fullmatch(r"[A-L][1-4]", code):
        group = code[0]
        position = int(code[1])
        return group_tables[group][position - 1].team
    if code[0] in ("W", "L"):
        source = dep_match_id or code[1:]
        source = _numeric_match_id(source)
        match = results_by_match[source]
        if code[0] == "W":
            if not match.winner:
                raise ValueError(f"No winner available for match {source}")
            return match.winner
        return match.away_team if match.winner == match.home_team else match.home_team
    raise ValueError(f"Unsupported slot code: {code}")


def _allowed_groups_from_placeholder(code: str) -> set[str]:
    if not (code.startswith("3rd[") and code.endswith("]")):
        return set()
    return set(code[4:-1])


def _assign_third_place_placeholders(
    fixtures: list[Fixture],
    third_place_ranked: list[GroupStanding],
) -> dict[tuple[str, str], str]:
    # Select the top 8 third-place teams first.
    qualified = third_place_ranked[:8]
    qualified_teams = [row.team for row in qualified]
    team_to_group = {row.team: row.group for row in qualified}

    placeholders: list[tuple[str, str, set[str]]] = []
    for fx in fixtures:
        if _is_group_stage(fx):
            continue
        if fx.home_code.startswith("3rd["):
            placeholders.append((fx.match_id, "home", _allowed_groups_from_placeholder(fx.home_code)))
        if fx.away_code.startswith("3rd["):
            placeholders.append((fx.match_id, "away", _allowed_groups_from_placeholder(fx.away_code)))

    # Most constrained placeholders first to avoid dead ends.
    placeholders.sort(
        key=lambda item: sum(
            1 for team in qualified_teams if team_to_group[team] in item[2]
        )
    )

    assignment: dict[tuple[str, str], str] = {}
    used: set[str] = set()

    def backtrack(index: int) -> bool:
        if index >= len(placeholders):
            return True
        match_id, side, allowed_groups = placeholders[index]
        candidates = [
            team
            for team in qualified_teams
            if team not in used and team_to_group[team] in allowed_groups
        ]
        for team in candidates:
            assignment[(match_id, side)] = team
            used.add(team)
            if backtrack(index + 1):
                return True
            used.remove(team)
            assignment.pop((match_id, side), None)
        return False

    if not backtrack(0):
        raise ValueError("Unable to resolve third-place placeholders with current fixtures")
    return assignment


def _simulate_single_match(
    rng: random.Random,
    fixture: Fixture,
    home_team: str,
    away_team: str,
    ratings: dict[str, float],
    params: SimulationParams,
    knockout: bool,
) -> MatchResult:
    home_rating = ratings[home_team]
    away_rating = ratings[away_team]
    outcome = sample_outcome(
        rng=rng,
        home_rating=home_rating,
        away_rating=away_rating,
        home_advantage=params.home_advantage,
        draw_bias=params.draw_bias,
        variance=params.variance,
        scale=params.elo_scale,
    )
    home_goals, away_goals = sample_scoreline(rng, outcome, knockout=knockout)
    winner: str | None = None
    decided_by: MatchResult.__annotations__["decided_by"] = "normal"
    if home_goals > away_goals:
        winner = home_team
    elif away_goals > home_goals:
        winner = away_team
    else:
        if knockout:
            winner, decided_by = decide_knockout_winner_after_draw(
                rng=rng,
                home_team=home_team,
                away_team=away_team,
                home_rating=home_rating,
                away_rating=away_rating,
                home_advantage=params.home_advantage,
                scale=params.elo_scale,
            )
        else:
            decided_by = "group_draw"
    return MatchResult(
        match_id=fixture.match_id,
        stage=fixture.stage,
        group=fixture.group,
        home_team=home_team,
        away_team=away_team,
        home_goals=home_goals,
        away_goals=away_goals,
        winner=winner,
        decided_by=decided_by,
    )


def simulate_tournament(
    matches_csv: Path,
    rankings_csv: Path,
    params: SimulationParams,
) -> SimulationResult:
    rng = random.Random(params.seed)
    fixtures = _load_fixtures(matches_csv)
    ratings = _load_rankings(rankings_csv)
    _validate_data(fixtures, ratings)

    group_table = _init_group_table(fixtures)
    group_matches: dict[str, list[MatchResult]] = defaultdict(list)
    all_results: list[MatchResult] = []
    results_by_numeric_match_id: dict[str, MatchResult] = {}

    for fx in fixtures:
        if not _is_group_stage(fx):
            continue
        home_team = canonical_team_name(fx.home_slot)
        away_team = canonical_team_name(fx.away_slot)
        result = _simulate_single_match(
            rng=rng,
            fixture=fx,
            home_team=home_team,
            away_team=away_team,
            ratings=ratings,
            params=params,
            knockout=False,
        )
        group = fx.group or ""
        group_matches[group].append(result)
        _apply_group_result(
            group_table[group][home_team],
            group_table[group][away_team],
            result.home_goals,
            result.away_goals,
        )
        all_results.append(result)
        results_by_numeric_match_id[_numeric_match_id(fx.match_id)] = result

    sorted_groups = _sorted_group_tables(group_table, group_matches, ratings)
    ranked_third = _rank_third_place_teams(sorted_groups, ratings)
    third_place_assignment = _assign_third_place_placeholders(fixtures, ranked_third)

    for fx in fixtures:
        if _is_group_stage(fx):
            continue
        if fx.home_code.startswith("3rd["):
            home_team = third_place_assignment[(fx.match_id, "home")]
        else:
            home_team = _slot_team_from_code(
                code=fx.home_code,
                group_tables=sorted_groups,
                results_by_match=results_by_numeric_match_id,
                dep_match_id=fx.home_dep_match,
            )
        if fx.away_code.startswith("3rd["):
            away_team = third_place_assignment[(fx.match_id, "away")]
        else:
            away_team = _slot_team_from_code(
                code=fx.away_code,
                group_tables=sorted_groups,
                results_by_match=results_by_numeric_match_id,
                dep_match_id=fx.away_dep_match,
            )
        result = _simulate_single_match(
            rng=rng,
            fixture=fx,
            home_team=home_team,
            away_team=away_team,
            ratings=ratings,
            params=params,
            knockout=True,
        )
        all_results.append(result)
        results_by_numeric_match_id[_numeric_match_id(fx.match_id)] = result

    final_match = results_by_numeric_match_id["104"]
    bronze_match = results_by_numeric_match_id["103"]
    if not final_match.winner or not bronze_match.winner:
        raise ValueError("Final matches did not produce winners")
    runner_up = final_match.away_team if final_match.winner == final_match.home_team else final_match.home_team
    fourth_place = bronze_match.away_team if bronze_match.winner == bronze_match.home_team else bronze_match.home_team

    return SimulationResult(
        champion=final_match.winner,
        runner_up=runner_up,
        third_place=bronze_match.winner,
        fourth_place=fourth_place,
        group_tables=sorted_groups,
        matches=all_results,
    )


def aggregate_runs(
    matches_csv: Path,
    rankings_csv: Path,
    params: SimulationParams,
    runs: int,
    highlight_team: str = "Sweden",
) -> dict[str, Any]:
    champions: dict[str, int] = defaultdict(int)
    finalists: dict[str, int] = defaultdict(int)
    semifinalists: dict[str, int] = defaultdict(int)
    quarterfinals: dict[str, int] = defaultdict(int)
    top8: dict[str, int] = defaultdict(int)
    top16: dict[str, int] = defaultdict(int)
    top32: dict[str, int] = defaultdict(int)
    all_teams: set[str] = set()
    best_highlight_score = -1
    best_highlight_label = "Group Stage"
    best_highlight_journey: list[dict[str, Any]] = []

    def placement_from_result(result: SimulationResult, team: str) -> tuple[int, str]:
        if team == result.champion:
            return 8, "Champion"
        if team == result.runner_up:
            return 7, "Runner-up"
        if team == result.third_place:
            return 6, "Third Place"
        if team == result.fourth_place:
            return 5, "Fourth Place"

        team_matches = [
            m for m in result.matches if m.home_team == team or m.away_team == team
        ]
        if not team_matches:
            return 0, "No Matches"

        stage_score = {
            "Group Stage": 0,
            "Round of 32": 1,
            "Round of 16": 2,
            "Quarter-final": 3,
            "Semi-final": 4,
            "Bronze final": 5,
            "Final": 6,
        }
        furthest = max(stage_score.get(m.stage, 0) for m in team_matches)
        labels = {
            0: "Group Stage",
            1: "Round of 32",
            2: "Round of 16",
            3: "Quarter-final",
            4: "Semi-final",
            5: "Bronze final",
            6: "Final",
        }
        return furthest, labels[furthest]

    def stage_reach_score(result: SimulationResult, team: str) -> int:
        team_matches = [m for m in result.matches if m.home_team == team or m.away_team == team]
        if not team_matches:
            return 0
        stage_score = {
            "Group Stage": 0,
            "Round of 32": 1,
            "Round of 16": 2,
            "Quarter-final": 3,
            "Semi-final": 4,
            "Bronze final": 5,
            "Final": 6,
        }
        return max(stage_score.get(m.stage, 0) for m in team_matches)

    for i in range(runs):
        run_params = params.model_copy(update={"seed": (params.seed + i) if params.seed is not None else None})
        result = simulate_tournament(matches_csv, rankings_csv, run_params)
        champions[result.champion] += 1
        finalists[result.champion] += 1
        finalists[result.runner_up] += 1
        semifinalists[result.champion] += 1
        semifinalists[result.runner_up] += 1
        semifinalists[result.third_place] += 1
        semifinalists[result.fourth_place] += 1

        for group_rows in result.group_tables.values():
            for row in group_rows:
                all_teams.add(row.team)
                reach = stage_reach_score(result, row.team)
                if reach >= 1:
                    top32[row.team] += 1
                if reach >= 2:
                    top16[row.team] += 1
                if reach >= 3:
                    quarterfinals[row.team] += 1
                    top8[row.team] += 1

        score, label = placement_from_result(result, highlight_team)
        if score > best_highlight_score:
            best_highlight_score = score
            best_highlight_label = label
            best_highlight_journey = [
                m.model_dump()
                for m in result.matches
                if m.home_team == highlight_team or m.away_team == highlight_team
            ]

    teams = sorted(all_teams)
    aggregate = []
    for team in teams:
        aggregate.append(
            {
                "team": team,
                "champion_pct": round((champions[team] / runs) * 100, 2),
                "finalist_pct": round((finalists[team] / runs) * 100, 2),
                "semifinal_pct": round((semifinalists[team] / runs) * 100, 2),
                "quarter_pct": round((quarterfinals[team] / runs) * 100, 2),
                "top8_pct": round((top8[team] / runs) * 100, 2),
                "top16_pct": round((top16[team] / runs) * 100, 2),
                "top32_pct": round((top32[team] / runs) * 100, 2),
            }
        )
    aggregate.sort(key=lambda x: (x["champion_pct"], x["finalist_pct"]), reverse=True)
    return {
        "runs": runs,
        "aggregate": aggregate,
        "highlight_team": highlight_team,
        "highlight_best_placement": best_highlight_label,
        "highlight_best_journey": best_highlight_journey,
    }
