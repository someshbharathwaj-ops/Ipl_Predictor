# IPL Predictor

This repository contains a time-aware data pipeline for building one-row-per-match IPL training data for a micrograd-style neural network.

Pipeline flow:

1. Raw CSV tables from `backend/data`
2. Cleaning, schema normalization, and validation
3. Time-aware team and matchup feature engineering
4. Final match dataset and numeric model input in `backend/Processed`

The current historical dataset covers IPL seasons 2008 through 2016. The rebuilt pipeline avoids target leakage by using only information available before each match.
