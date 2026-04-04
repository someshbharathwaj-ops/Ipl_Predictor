"""Feature engineering helpers for leakage-safe IPL match modeling."""

from __future__ import annotations

import pandas as pd


def add_ball_outcome_flags(balls: pd.DataFrame) -> pd.DataFrame:
    """Annotate ball rows with reusable scoring flags."""

    flagged = balls.copy()
    flagged["is_dot_ball"] = (flagged["total_runs"] == 0).astype(int)
    flagged["is_boundary"] = flagged["batsman_scored"].isin([4, 6]).astype(int)
    flagged["phase"] = pd.cut(
        flagged["over_id"],
        bins=[0, 6, 15, 20],
        labels=["powerplay", "middle", "death"],
        include_lowest=True,
    )
    return flagged


def build_innings_stats(balls: pd.DataFrame) -> pd.DataFrame:
    """Create per-innings performance aggregates."""

    flagged = add_ball_outcome_flags(balls)
    primary_innings = flagged[flagged["innings_id"] <= 2].copy()

    innings = (
        primary_innings.groupby(
            ["match_id", "innings_id", "batting_team_id", "bowling_team_id"],
            as_index=False,
        )
        .agg(
            total_runs=("total_runs", "sum"),
            wickets_lost=("is_wicket", "sum"),
            legal_balls=("is_legal_delivery", "sum"),
            dot_balls=("is_dot_ball", "sum"),
            boundary_balls=("is_boundary", "sum"),
            extra_runs=("extra_runs", "sum"),
        )
    )
    return innings


def build_team_history_frame(
    matches: pd.DataFrame,
    innings_stats: pd.DataFrame,
) -> pd.DataFrame:
    """Create one row per team per match before matchup assembly."""

    return matches.copy()
