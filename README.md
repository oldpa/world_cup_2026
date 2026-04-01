# World Cup 2026 Simulator

This project simulates the World Cup 2026 tournament using:

- Fixture list from `world_cup_2026_simulation_matches.csv`
- FIFA ranking points (`fifa_rank.csv`) as Elo-like team strength

It includes a FastAPI backend and a React frontend for rerunning simulations with tunable parameters.

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API endpoints:

- `GET /health`
- `POST /simulate`
- `POST /simulate/many`

Main simulation parameters:

- `variance` (0..1): higher means more randomness
- `draw_bias` (-0.2..0.2): shifts draw likelihood
- `home_advantage` (Elo points)
- `elo_scale` (Elo logistic scale)
- `seed` (optional deterministic runs)

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI is served at `http://localhost:5173` and expects the backend at `http://127.0.0.1:8000`.

To override backend URL in frontend, create `frontend/.env` from `frontend/.env.example`:

```bash
cp frontend/.env.example frontend/.env
```

Then set:

```bash
VITE_API_BASE=https://your-api-url
```

## Deploy on Render (recommended)

This repo includes `render.yaml` to deploy both backend and frontend.

1. Push this project to GitHub.
2. In Render, choose **New > Blueprint** and connect your repo.
3. Render will create:
   - `world-cup-2026-api` (FastAPI backend)
   - `world-cup-2026-ui` (static frontend)
4. Wait for both services to finish deploying.
5. Open the UI service URL and run simulations.

Notes:
- Backend CORS is environment-configurable:
  - `ALLOW_ALL_ORIGINS=true` (current blueprint default)
  - or set `ALLOWED_ORIGINS` / `ALLOWED_ORIGIN_REGEX`
- Frontend reads backend URL from `VITE_API_BASE`.

## Model assumptions

- FIFA points are treated like Elo ratings.
- Group ranking uses points, goal difference, goals scored, then head-to-head subset metrics.
- Third-place teams are globally ranked, then consumed for `3rd[...]` knockout placeholders.
- Knockout draws after 90 minutes are resolved by stochastic extra-time/penalties winner selection.
