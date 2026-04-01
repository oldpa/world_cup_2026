import { useState } from 'react'
import './App.css'
import {
  runManySimulations,
  runSingleSimulation,
  type MultiSimulationResult,
  type SimulationResult,
} from './api'
import { ResultsView } from './components/ResultsView'
import { SimulationControls } from './components/SimulationControls'

const WORLD_CUP_TEAMS = [
  'Algeria',
  'Argentina',
  'Australia',
  'Austria',
  'Belgium',
  'Bosnia and Herzegovina',
  'Brazil',
  'Cabo Verde',
  'Canada',
  'Colombia',
  'Congo DR',
  'Croatia',
  'Curaçao',
  'Czechia',
  'Ecuador',
  'Egypt',
  'England',
  'France',
  'Germany',
  'Ghana',
  'Haiti',
  'IR Iran',
  'Iraq',
  'Japan',
  'Jordan',
  'Korea Republic',
  'Mexico',
  'Morocco',
  'Netherlands',
  'New Zealand',
  'Norway',
  'Panama',
  'Paraguay',
  'Portugal',
  'Qatar',
  'Saudi Arabia',
  'Scotland',
  'Senegal',
  'South Africa',
  'Spain',
  'Sweden',
  'Switzerland',
  'Tunisia',
  'Türkiye',
  'Uruguay',
  'USA',
  'Uzbekistan',
  "Côte d'Ivoire",
]

function App() {
  const [single, setSingle] = useState<SimulationResult | null>(null)
  const [aggregate, setAggregate] = useState<MultiSimulationResult | null>(null)
  const [highlightTeam, setHighlightTeam] = useState('Sweden')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRunSingle = async (params: Parameters<typeof runSingleSimulation>[0]) => {
    setBusy(true)
    setError(null)
    setAggregate(null)
    try {
      const result = await runSingleSimulation(params)
      setSingle(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run simulation')
    } finally {
      setBusy(false)
    }
  }

  const handleRunMany = async (
    params: Omit<Parameters<typeof runManySimulations>[0], 'highlight_team'>,
  ) => {
    setBusy(true)
    setError(null)
    setSingle(null)
    try {
      const result = await runManySimulations({
        ...params,
        highlight_team: highlightTeam,
      })
      setAggregate(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run aggregate simulation')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="app">
      <header>
        <h1>World Cup 2026 Simulator</h1>
        <p>Tune Elo parameters, rerun the tournament, and estimate title odds.</p>
      </header>
      {error ? <p className="error">{error}</p> : null}
      <SimulationControls
        busy={busy}
        onRunSingle={handleRunSingle}
        onRunMany={handleRunMany}
      />
      <ResultsView
        single={single}
        aggregate={aggregate}
        highlightTeam={highlightTeam}
        highlightOptions={WORLD_CUP_TEAMS}
        onHighlightTeamChange={setHighlightTeam}
      />
    </main>
  )
}

export default App
