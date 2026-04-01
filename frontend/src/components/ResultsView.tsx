import type { MatchResult, MultiSimulationResult, SimulationResult } from '../api'

type Props = {
  single: SimulationResult | null
  aggregate: MultiSimulationResult | null
  highlightTeam: string
  highlightOptions: string[]
  onHighlightTeamChange: (team: string) => void
}

function stageOrder(stage: string): number {
  const order: Record<string, number> = {
    'Group Stage': 1,
    'Round of 32': 2,
    'Round of 16': 3,
    'Quarter-final': 4,
    'Semi-final': 5,
    'Bronze final': 6,
    Final: 7,
  }
  return order[stage] ?? 99
}

const TEAM_FLAGS: Record<string, string> = {
  Algeria: '🇩🇿',
  Argentina: '🇦🇷',
  Australia: '🇦🇺',
  Austria: '🇦🇹',
  Belgium: '🇧🇪',
  'Bosnia and Herzegovina': '🇧🇦',
  Brazil: '🇧🇷',
  'Cabo Verde': '🇨🇻',
  Canada: '🇨🇦',
  Colombia: '🇨🇴',
  'Congo DR': '🇨🇩',
  Croatia: '🇭🇷',
  Curaçao: '🇨🇼',
  Czechia: '🇨🇿',
  Ecuador: '🇪🇨',
  Egypt: '🇪🇬',
  England: '🏴',
  France: '🇫🇷',
  Germany: '🇩🇪',
  Ghana: '🇬🇭',
  Haiti: '🇭🇹',
  'IR Iran': '🇮🇷',
  Iraq: '🇮🇶',
  Japan: '🇯🇵',
  Jordan: '🇯🇴',
  Korea: '🇰🇷',
  'Korea Republic': '🇰🇷',
  Mexico: '🇲🇽',
  Morocco: '🇲🇦',
  Netherlands: '🇳🇱',
  'New Zealand': '🇳🇿',
  Norway: '🇳🇴',
  Panama: '🇵🇦',
  Paraguay: '🇵🇾',
  Portugal: '🇵🇹',
  Qatar: '🇶🇦',
  'Saudi Arabia': '🇸🇦',
  Scotland: '🏴',
  Senegal: '🇸🇳',
  Spain: '🇪🇸',
  Sweden: '🇸🇪',
  Switzerland: '🇨🇭',
  Tunisia: '🇹🇳',
  Türkiye: '🇹🇷',
  USA: '🇺🇸',
  Uruguay: '🇺🇾',
  Uzbekistan: '🇺🇿',
  "Côte d'Ivoire": '🇨🇮',
  'South Africa': '🇿🇦',
}

function teamDisplay(team: string): string {
  return `${TEAM_FLAGS[team] ?? '⚽'} ${team}`
}

function renderMatchList(matches: MatchResult[]) {
  return [...matches]
    .sort((a, b) => stageOrder(a.stage) - stageOrder(b.stage))
    .map((m) => (
      <li key={m.match_id} className="match-item">
        <div className="match-meta">
          <span className="stage-badge">{m.stage}</span>
          <span className="muted">#{m.match_id}</span>
        </div>
        <div className="match-main">
          <span className={m.winner === m.home_team ? 'team winner' : 'team'}>
            {teamDisplay(m.home_team)}
          </span>
          <span className="score-wrap">
            <span className="score">
              {m.home_goals} - {m.away_goals}
            </span>
            <span
              className="decision-mark"
              title={
                m.decided_by === 'normal'
                  ? 'Decided in normal time'
                  : m.decided_by === 'extra_time'
                    ? 'Decided in extra time'
                    : m.decided_by === 'penalties'
                      ? 'Decided by penalties'
                      : 'Group-stage draw'
              }
              aria-label={
                m.decided_by === 'normal'
                  ? 'Decided in normal time'
                  : m.decided_by === 'extra_time'
                    ? 'Decided in extra time'
                    : m.decided_by === 'penalties'
                      ? 'Decided by penalties'
                      : 'Group-stage draw'
              }
            >
              {m.decided_by === 'normal'
                ? 'N'
                : m.decided_by === 'extra_time'
                  ? 'ET'
                  : m.decided_by === 'penalties'
                    ? 'P'
                    : 'D'}
            </span>
          </span>
          <span className={m.winner === m.away_team ? 'team winner' : 'team'}>
            {teamDisplay(m.away_team)}
          </span>
        </div>
      </li>
    ))
}

function renderMatchColumns(matches: MatchResult[], scrollable = true) {
  const groupStageMatches = matches.filter((m) => m.stage === 'Group Stage')
  const knockoutMatches = matches.filter((m) => m.stage !== 'Group Stage')
  const listClassName = scrollable ? 'matches' : 'matches full-height'
  return (
    <div className="match-columns">
      <div className="match-column">
        <h5>Group Stage</h5>
        {groupStageMatches.length > 0 ? (
          <ul className={listClassName}>{renderMatchList(groupStageMatches)}</ul>
        ) : (
          <p className="muted">No group-stage matches.</p>
        )}
      </div>
      <div className="match-column">
        <h5>Knockout Rounds</h5>
        {knockoutMatches.length > 0 ? (
          <ul className={listClassName}>{renderMatchList(knockoutMatches)}</ul>
        ) : (
          <p className="muted">No knockout matches.</p>
        )}
      </div>
    </div>
  )
}

export function ResultsView({
  single,
  aggregate,
  highlightTeam,
  highlightOptions,
  onHighlightTeamChange,
}: Props) {
  const singleJourney =
    single?.matches.filter(
      (m) => m.home_team === highlightTeam || m.away_team === highlightTeam,
    ) ?? []
  const highlightedAggregateStats =
    aggregate?.aggregate.find((row) => row.team === aggregate.highlight_team) ?? null
  return (
    <section className="panel">
      <div className="results-header">
        <h2>Results</h2>
        <label className="inline-highlight">
          Highlighted team:
          <select value={highlightTeam} onChange={(e) => onHighlightTeamChange(e.target.value)}>
            {highlightOptions.map((team) => (
              <option key={team} value={team}>
                {team}
              </option>
            ))}
          </select>
        </label>
      </div>

      {single ? (
        <>
          <h3>{highlightTeam} Journey (Single Run)</h3>
          {singleJourney.length > 0 ? (
            renderMatchColumns(singleJourney)
          ) : (
            <p className="muted">No matches found for {highlightTeam} in this run.</p>
          )}

          <div className="podium">
            <div>Champion: {single.champion}</div>
            <div>Runner-up: {single.runner_up}</div>
            <div>Third: {single.third_place}</div>
            <div>Fourth: {single.fourth_place}</div>
          </div>

          <h3>Group Tables</h3>
          <div className="groups">
            {Object.entries(single.group_tables)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([group, table]) => (
                <div key={group} className="group-card">
                  <h4>Group {group}</h4>
                  <table>
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Team</th>
                        <th>Pts</th>
                        <th>GD</th>
                        <th>GF</th>
                        <th>GA</th>
                      </tr>
                    </thead>
                    <tbody>
                      {table.map((row) => (
                        <tr key={row.team}>
                          <td>{row.position}</td>
                          <td>{teamDisplay(row.team)}</td>
                          <td>{row.points}</td>
                          <td>{row.goal_difference}</td>
                          <td>{row.goals_for}</td>
                          <td>{row.goals_against}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
          </div>

          <h3>Matches</h3>
          {renderMatchColumns(single.matches)}
        </>
      ) : (
        <p className="muted">Run a single tournament to see group tables and full bracket matches.</p>
      )}

      <h3>Aggregate Odds</h3>
      {aggregate ? (
        <>
          <h4>{aggregate.highlight_team} Aggregate Stats</h4>
          {highlightedAggregateStats ? (
            <table>
              <thead>
                <tr>
                  <th>Champion %</th>
                  <th>Finalist %</th>
                  <th>Semi %</th>
                  <th>Quarter %</th>
                  <th>Top8 %</th>
                  <th>Top16 %</th>
                  <th>Top32 %</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{highlightedAggregateStats.champion_pct}</td>
                  <td>{highlightedAggregateStats.finalist_pct}</td>
                  <td>{highlightedAggregateStats.semifinal_pct}</td>
                  <td>{highlightedAggregateStats.quarter_pct}</td>
                  <td>{highlightedAggregateStats.top8_pct}</td>
                  <td>{highlightedAggregateStats.top16_pct}</td>
                  <td>{highlightedAggregateStats.top32_pct}</td>
                </tr>
              </tbody>
            </table>
          ) : (
            <p className="muted">No aggregate stats found for {aggregate.highlight_team}.</p>
          )}

          <h4>
            {aggregate.highlight_team} Best Placement: {aggregate.highlight_best_placement}
          </h4>
          {aggregate.highlight_best_journey.length > 0 ? (
            renderMatchColumns(aggregate.highlight_best_journey, false)
          ) : (
            <p className="muted">No aggregate journey available.</p>
          )}

          <table>
            <thead>
              <tr>
                <th>Team</th>
                <th>Champion %</th>
                <th>Finalist %</th>
                <th>Semi %</th>
                <th>Quarter %</th>
                <th>Top8 %</th>
                <th>Top16 %</th>
                <th>Top32 %</th>
              </tr>
            </thead>
            <tbody>
              {aggregate.aggregate.map((row) => (
                <tr key={row.team}>
                  <td>{teamDisplay(row.team)}</td>
                  <td>{row.champion_pct}</td>
                  <td>{row.finalist_pct}</td>
                  <td>{row.semifinal_pct}</td>
                  <td>{row.quarter_pct}</td>
                  <td>{row.top8_pct}</td>
                  <td>{row.top16_pct}</td>
                  <td>{row.top32_pct}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ) : (
        <p className="muted">Run aggregate simulation to estimate title odds.</p>
      )}
    </section>
  )
}
