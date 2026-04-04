# IPL Predictor

This repository contains a time-aware data pipeline for building one-row-per-match IPL training data for a micrograd-style neural network.

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
- `data_audit.json`: schema and missing-value audit
- `validation_report.json`: logical data integrity checks
- `feature_manifest.json`: final dataset structure and feature list

## Running the pipeline

```bash
python backend/src/maindataset.py
```

## Modeling notes

- `target = 1` means the canonical `team1` side won the match
- no-result matches are excluded from the training set
- feature windows are shifted so each match only sees historical information
- normalization is best applied after a time-based train/validation split to avoid leakage
