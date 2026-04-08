# IPL Predictor

A simple IPL match prediction project with:

- a React frontend in `frontend/`
- a FastAPI backend in `backend/web/`
- shared API handlers used locally and on Vercel

The app predicts:

- the likely match winner
- win probability for both teams
- projected scorecards for both innings

## Structure

- `frontend/`: the only frontend source of truth
- `frontend/src/main.jsx`: React entry point
- `frontend/src/App.jsx`: single-page app shell
- `frontend/src/services/api.js`: shared frontend API client
- `backend/web/app.py`: local FastAPI app exposing `/api/*`
- `backend/web/api_handlers.py`: shared API contracts and handlers
- `api/*.py`: thin Vercel wrappers that reuse the same backend handlers
- `backend/main.py`: model loading, artifact bootstrapping, and prediction logic
- `backend/src/`: dataset pipeline and feature engineering code

## How It Works

1. The frontend sends requests to `/api`.
2. FastAPI or Vercel routes those requests to shared handlers.
3. The backend loads processed match data and the saved model.
4. The model predicts the winner and probability.
5. The backend also estimates a realistic scoreboard for both teams.

## API Design

All backend runtime endpoints are standardized under `/api`:

- `GET /api/health`
- `GET /api/metadata`
- `POST /api/predict`

The React frontend calls these endpoints through one consistent base URL. In development, Vite proxies `/api` to the local FastAPI server. In production, Vercel serves the frontend and Python API functions from the same repo root.

## Quick Start

Run every command from the repository root:

```bash
cd IPL_Predictor
```

### 1. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 2. Install frontend dependencies

```bash
cd frontend
npm install
```

### 3. Start the backend

```bash
python -m uvicorn backend.web.app:app --host 127.0.0.1 --port 8000
```

Important:

- start the backend from the repository root, not from `backend/`
- if you run the command inside `backend/`, Python will fail with `ModuleNotFoundError: No module named 'backend'`

### 4. Start the frontend

```bash
cd frontend
npm run dev
```

### 5. Open the app

```text
http://127.0.0.1:5173
```

Backend health check:

```text
http://127.0.0.1:8000/api/health
```

## Environment Variables

Frontend:

- `VITE_API_BASE_URL`
  - optional
  - defaults to `/api`
  - set this only if the frontend must call a different backend origin

See [frontend/.env.example](/c:/Users/SOMESH%20BHARATHWAJ/Documents/GitHub/IPL_Predictor/frontend/.env.example).

## Deployment

### Vercel

Use the repository root as the project root, not `frontend/`.

Expected deployment behavior:

- Vercel builds the React app from `frontend/`
- Vercel exposes Python API functions from `api/`
- rewrites in `vercel.json` keep `/api/*` routed to the Python functions

### Generic Python Hosting

You can also run the local FastAPI backend directly:

```bash
uvicorn backend.web.app:app --host 0.0.0.0 --port $PORT
```

## Validation

Frontend build:

```bash
npm --prefix frontend run build
```

Backend smoke tests:

```bash
python -m pytest backend/tests/test_api_smoke.py
```

## Data And Model Notes

- `backend/Processed/team_history_features.csv`
- `backend/Processed/match_dataset.csv`
- `backend/models/model.pkl`

These runtime artifacts are included because the deployed API needs them to answer `/api/metadata` and `/api/predict` without rebuilding the full dataset at request time.
