# Frontend And Endpoint Audit

## Current Structure

```text
IPL_Predictor/
|- api/
|  |- health.py
|  |- metadata.py
|  `- predict.py
|- backend/
|  |- main.py
|  |- Processed/
|  |- models/
|  |- src/
|  `- web/
|     |- app.py
|     `- static/
|        |- app.js
|        |- index.html
|        `- styles.css
|- frontend/
|  |- index.html
|  |- package.json
|  |- src/
|  |  |- App.jsx
|  |  |- main.jsx
|  |  |- components/
|  |  `- services/api.js
|  |- dist/
|  `- node_modules/
|- vercel.json
|- requirements.txt
`- README.md
```

## Frontend-Related Folders And Files

- `frontend/`: primary React and Vite application
- `frontend/src/main.jsx`: React entry point
- `frontend/src/App.jsx`: app shell
- `frontend/src/components/*`: UI components
- `frontend/src/services/api.js`: frontend API client
- `backend/web/static/*`: second standalone frontend implementation
- `backend/web/app.py`: also serves HTML from the backend static frontend

## Current API Endpoints

### Local FastAPI app in `backend/web/app.py`

- `GET /`
- `GET /health`
- `GET /metadata`
- `POST /predict`

### Vercel Python functions in `api/`

- `GET /api/health`
- `GET /api/metadata`
- `POST /api/predict`

## Problems Found

### Duplicate frontend entry points

- `frontend/index.html` + `frontend/src/main.jsx` define a React frontend
- `backend/web/static/index.html` + `backend/web/static/app.js` define a second frontend
- `backend/web/app.py` serves the backend static frontend at `/`

### Duplicate endpoint systems

- `backend/web/app.py` defines root-level API routes
- `api/health.py`, `api/metadata.py`, and `api/predict.py` define a second API surface for Vercel
- the same metadata and prediction logic exists in more than one place

### Routing inconsistency

- frontend runtime sometimes targets `/metadata` and `/predict`
- deployment also exposes `/api/metadata` and `/api/predict`
- rewrites are used to compensate for inconsistent route design instead of having one API shape

### Dead or redundant files

- `backend/web/static/*` is redundant if `frontend/` is the source of truth
- `frontend/dist/` is a generated build output and should not be a tracked application source
- `frontend/node_modules/` should not be tracked in version control

## Refactor Direction

- keep `frontend/` as the single frontend source of truth
- remove `backend/web/static/*`
- standardize backend API under `/api/*`
- reuse one shared router implementation for both local FastAPI and Vercel deployment wrappers
- stop serving a second frontend from FastAPI
