"""Dataset assembly helpers for converting team history into match rows."""

from __future__ import annotations

import pandas as pd


def build_match_dataset(team_history: pd.DataFrame) -> pd.DataFrame:
    """Assemble one-row-per-match data."""

    return team_history.copy()


def extract_model_matrix(match_dataset: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Split features from the binary winner target."""

    target = match_dataset["target"]
    features = match_dataset.drop(columns=["target"])
    return features, target
