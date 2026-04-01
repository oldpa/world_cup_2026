import { useState } from 'react'
import type { SimulationParams } from '../api'

type Props = {
  busy: boolean
  onRunSingle: (params: SimulationParams) => Promise<void>
  onRunMany: (params: SimulationParams & { runs: number }) => Promise<void>
}

const defaultParams: SimulationParams = {
  variance: 0.35,
  draw_bias: 0,
  home_advantage: 35,
  elo_scale: 400,
  seed: null,
}

export function SimulationControls({
  busy,
  onRunMany,
  onRunSingle,
}: Props) {
  const [params, setParams] = useState<SimulationParams>(defaultParams)
  const [runs, setRuns] = useState(500)
  const [showConfig, setShowConfig] = useState(false)

  return (
    <section className="panel">
      <h2>Simulation Controls</h2>
      <div className="actions">
        <button type="button" onClick={() => setShowConfig((prev) => !prev)}>
          {showConfig ? 'Hide Config' : 'Show Config'}
        </button>
        <button disabled={busy} onClick={() => onRunSingle(params)}>
          Run Single Tournament
        </button>
        <button disabled={busy} onClick={() => onRunMany({ ...params, runs })}>
          Run Aggregate Simulation
        </button>
      </div>
      {showConfig ? (
        <div className="grid">
          <label>
            Variance ({params.variance.toFixed(2)})
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={params.variance}
              onChange={(e) =>
                setParams((prev) => ({ ...prev, variance: Number(e.target.value) }))
              }
            />
          </label>
          <label>
            Draw Bias
            <input
              type="number"
              step={0.01}
              min={-0.2}
              max={0.2}
              value={params.draw_bias}
              onChange={(e) =>
                setParams((prev) => ({ ...prev, draw_bias: Number(e.target.value) }))
              }
            />
          </label>
          <label>
            Home Advantage (Elo pts)
            <input
              type="number"
              step={1}
              value={params.home_advantage}
              onChange={(e) =>
                setParams((prev) => ({
                  ...prev,
                  home_advantage: Number(e.target.value),
                }))
              }
            />
          </label>
          <label>
            Elo Scale
            <input
              type="number"
              step={10}
              value={params.elo_scale}
              onChange={(e) =>
                setParams((prev) => ({ ...prev, elo_scale: Number(e.target.value) }))
              }
            />
          </label>
          <label>
            Seed (optional)
            <input
              type="number"
              value={params.seed ?? ''}
              onChange={(e) =>
                setParams((prev) => ({
                  ...prev,
                  seed: e.target.value ? Number(e.target.value) : null,
                }))
              }
            />
          </label>
          <label>
            Runs (for aggregate)
            <input
              type="number"
              min={1}
              max={5000}
              value={runs}
              onChange={(e) => setRuns(Number(e.target.value))}
            />
          </label>
        </div>
      ) : null}
    </section>
  )
}
