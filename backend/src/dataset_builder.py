"""Dataset assembly helpers for converting team history into match rows."""

from __future__ import annotations

import pandas as pd


IDENTIFIER_COLUMNS = {
    "match_id",
    "match_date",
    "season_id",
    "team_id",
    "opponent_team_id",
    "winner_team_id",
    "venue_name",
    "city_name",
    "host_country",
    "toss_decision",
}


def _rename_side_columns(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    keep_columns = {"match_id", "match_date"}
    renamed = frame.copy()
    renamed.columns = [
        column if column in keep_columns else f"{prefix}_{column}"
        for column in renamed.columns
    ]
    return renamed


def build_match_dataset(team_history: pd.DataFrame) -> pd.DataFrame:
    """Assemble one-row-per-match data."""

    decided = team_history[team_history["winner_team_id"].notna()].copy()
    side_a = _rename_side_columns(decided, "team1")
    side_b = _rename_side_columns(decided, "team2")

    dataset = side_a.merge(
        side_b,
        on=["match_id", "match_date"],
        how="inner",
    )
    dataset = dataset[dataset["team1_team_id"] != dataset["team2_team_id"]]
    dataset = dataset[dataset["team1_team_id"] < dataset["team2_team_id"]]
    return dataset


def extract_model_matrix(match_dataset: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Split features from the binary winner target."""

    target = match_dataset["target"]
    features = match_dataset.drop(columns=["target"])
    return features, target
