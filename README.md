# IPL Predictor

This repository packages an IPL match simulator as a single FastAPI app with a built-in static frontend. It combines a time-aware data pipeline, a micrograd-style winner model, and score estimation logic for interactive match previews.

The project uses `backend/data/IPL.csv` as the primary historical source and standardizes it into cleaned match, ball-by-ball, and feature datasets covering IPL seasons `2008-2025`.

## What Ships

- `backend/src/preprocessing.py`: raw loading, schema cleanup, validation, and canonical exports
- `backend/src/features.py`: innings aggregates and leakage-safe team history features
- `backend/src/dataset_builder.py`: one-row-per-match dataset assembly and model matrix export
- `backend/src/maindataset.py`: full dataset pipeline runner
- `backend/main.py`: micrograd training utilities, artifact bootstrapping, and prediction logic
- `backend/web/app.py`: FastAPI deployment entrypoint
- `backend/web/static/`: frontend served directly by FastAPI

## Runtime Behavior

- The app serves the browser UI at `/`
- The API serves `/health`, `/metadata`, and `/predict`
- Generated files in `backend/Processed` and the trained model in `backend/models/model.pkl` are not committed
- On a fresh deployment, the app can rebuild missing processed datasets from `backend/data/IPL.csv`
- If the trained model is missing, the app can train a fallback micrograd model automatically

## Install

```bash
pip install -r requirements.txt
```

## Run Locally

```bash
uvicorn backend.web.app:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## Deploy

Use this entrypoint:

```bash
uvicorn backend.web.app:app --host 0.0.0.0 --port $PORT
```

A `Procfile` is included for platforms that support it. No separate frontend build step is required.

## Manual Dataset Rebuild

```bash
python backend/src/maindataset.py
```

## Example Prediction Payload

```json
{
  "team1": "Chennai Super Kings",
  "team2": "Mumbai Indians",
  "toss_winner": "Mumbai Indians",
  "user_predicted_score_team1": 180,
  "user_predicted_score_team2": 170,
  "key_player_team1": "MS Dhoni",
  "key_player_team2": "Jasprit Bumrah"
}
```

## Modeling Notes

- `target = 1` means the canonical `team1` side won the match
- no-result matches are excluded from the training set
- all rolling and form features are shifted to avoid future leakage
- normalization happens after a chronological train/validation split
- the first cold start can take longer because missing artifacts may be generated automatically
