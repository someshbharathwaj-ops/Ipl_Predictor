# IPL Predictor

This repository contains a time-aware data pipeline for building one-row-per-match IPL training data for a micrograd-style neural network.

The project now prefers `backend/data/IPL.csv` as the primary historical source because it provides unified ball-by-ball IPL coverage from 2008 through 2025. The older split files remain as fallback inputs only.

Pipeline flow:

1. Raw CSV tables from `backend/data`
2. Cleaning, schema normalization, and validation
3. Time-aware team and matchup feature engineering
4. Final match dataset and numeric model input in `backend/Processed`

The current historical dataset covers IPL seasons 2008 through 2016. The rebuilt pipeline avoids target leakage by using only information available before each match.

## Project layout

- `backend/src/preprocessing.py`: raw table loading, schema cleanup, derived columns, validation, and audit output
- `backend/src/features.py`: innings aggregates and pre-match franchise features
- `backend/src/dataset_builder.py`: one-row-per-match dataset assembly and model matrix export
- `backend/src/maindataset.py`: end-to-end pipeline runner

## Generated outputs

- `innings_stats.csv`: team batting innings aggregates by match
- `team_history_features.csv`: one row per team per match with shifted historical features
- `match_dataset.csv`: one row per decided match with both teams and context joined together
- `micrograd_model_input.csv`: numeric model-ready feature matrix with the `target` column
- `ball_by_ball_2008_2025.csv`: canonical expanded ball-by-ball export
- `matches_2008_2025.csv`: canonical expanded match-level export
- `data_audit.json`: schema and missing-value audit
- `validation_report.json`: logical data integrity checks
- `feature_manifest.json`: final dataset structure and feature list
- `dataset_coverage.json`: season/date coverage summary
- `expansion_status.json`: whether the repo already covers the requested range
- `api_ingestion_plan.json`: fallback ingestion design for future source gaps

## Running the pipeline

```bash
python backend/src/maindataset.py
```

## Prediction API

Run the backend API with:

```bash
uvicorn backend.web.app:app --reload
```

Available endpoints:

- `GET /health`
- `GET /metadata`
- `POST /predict`

Example payload:

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

## Frontend

Install and run the frontend from the `frontend` directory:

```bash
npm install
npm run dev
```

If needed, point the UI to a different backend with:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Modeling notes

- `target = 1` means the canonical `team1` side won the match
- no-result matches are excluded from the training set
- feature windows are shifted so each match only sees historical information
- normalization is best applied after a time-based train/validation split to avoid leakage
