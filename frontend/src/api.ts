export type SimulationParams = {
  variance: number
  draw_bias: number
  home_advantage: number
  elo_scale: number
  seed?: number | null
}

export type GroupStanding = {
  team: string
  group: string
  played: number
  points: number
  goals_for: number
  goals_against: number
  goal_difference: number
  wins: number
  draws: number
  losses: number
  position: number
}

export type MatchResult = {
  match_id: string
  stage: string
  group: string | null
  home_team: string
  away_team: string
  home_goals: number
  away_goals: number
  winner: string | null
  decided_by: string
}

export type SimulationResult = {
  champion: string
  runner_up: string
  third_place: string
  fourth_place: string
  group_tables: Record<string, GroupStanding[]>
  matches: MatchResult[]
}

export type AggregateTeamStats = {
  team: string
  champion_pct: number
  finalist_pct: number
  semifinal_pct: number
  quarter_pct: number
  top8_pct: number
  top16_pct: number
  top32_pct: number
}

export type MultiSimulationResult = {
  runs: number
  aggregate: AggregateTeamStats[]
  highlight_team: string
  highlight_best_placement: string
  highlight_best_journey: MatchResult[]
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export async function runSingleSimulation(
  params: SimulationParams,
): Promise<SimulationResult> {
  const response = await fetch(`${API_BASE}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  if (!response.ok) {
    throw new Error(`Simulation failed: ${response.status}`)
  }
  return response.json()
}

export async function runManySimulations(
  params: SimulationParams & { runs: number; highlight_team: string },
): Promise<MultiSimulationResult> {
  const response = await fetch(`${API_BASE}/simulate/many`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  if (!response.ok) {
    throw new Error(`Multi simulation failed: ${response.status}`)
  }
  return response.json()
}
