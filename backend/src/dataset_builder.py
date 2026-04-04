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
LEAKY_PREFIXES = (
    "team1_won_match",
    "team1_lost_match",
    "team2_won_match",
    "team2_lost_match",
)


def _rename_side_columns(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    keep_columns = {"match_id", "match_date"}
    renamed = frame.copy()
    renamed.columns = [
        column if column in keep_columns else f"{prefix}_{column}"
        for column in renamed.columns
    ]
    return renamed


def add_relative_strength_features(dataset: pd.DataFrame) -> pd.DataFrame:
    """Create team1 minus team2 differences for key metrics."""

    enriched = dataset.copy()
    comparable_metrics = [
        "win_rate_before_match",
        "last_5_matches_win_rate",
        "batting_run_rate_mean_before_match",
        "batting_powerplay_run_rate_mean_before_match",
        "batting_death_over_run_rate_mean_before_match",
        "batting_boundary_percentage_mean_before_match",
        "bowling_run_rate_conceded_mean_before_match",
        "bowling_wicket_rate_mean_before_match",
        "bowling_dot_ball_percentage_mean_before_match",
        "venue_win_rate_before_match",
        "head_to_head_win_rate_before_match",
    ]
    for metric in comparable_metrics:
        enriched[f"delta_{metric}"] = (
            enriched[f"team1_{metric}"] - enriched[f"team2_{metric}"]
        )
    return enriched


def drop_leaky_or_unused_columns(dataset: pd.DataFrame) -> pd.DataFrame:
    """Remove identifiers and direct outcome fields from the model table."""

    pruned = dataset.copy()
    drop_columns = [
        column
        for column in pruned.columns
        if column in {
            "team1_winner_team_id",
            "team2_winner_team_id",
        }
        or column.endswith("_match_id")
        or any(column.startswith(prefix) for prefix in LEAKY_PREFIXES)
    ]
    return pruned.drop(columns=drop_columns)


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
    dataset["target"] = (dataset["team1_team_id"] == dataset["team1_winner_team_id"]).astype(int)
    dataset["team1_is_toss_winner"] = (
        dataset["team1_toss_winner_id"] == dataset["team1_team_id"]
    ).astype(int)
    dataset["team2_is_toss_winner"] = (
        dataset["team1_toss_winner_id"] == dataset["team2_team_id"]
    ).astype(int)
    dataset["team1_home_country"] = (
        dataset["team1_host_country"].str.lower() == "india"
    ).astype(int)
    dataset = add_relative_strength_features(dataset)
    return drop_leaky_or_unused_columns(dataset)


def extract_model_matrix(match_dataset: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Split features from the binary winner target."""

    ordered = match_dataset.sort_values(["match_date", "match_id"]).reset_index(drop=True)
    target = ordered["target"].astype(int)
    feature_frame = ordered.drop(columns=["target"])
    numeric_features = feature_frame.select_dtypes(include=["number", "bool"]).copy()
    features = numeric_features.drop(columns=["match_id"])
    return features, target
