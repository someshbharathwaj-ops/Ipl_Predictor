"""Feature engineering helpers for leakage-safe IPL match modeling."""

from __future__ import annotations

import pandas as pd


def build_innings_stats(balls: pd.DataFrame) -> pd.DataFrame:
    """Create per-innings performance aggregates."""

    return balls.copy()


def build_team_history_frame(
    matches: pd.DataFrame,
    innings_stats: pd.DataFrame,
) -> pd.DataFrame:
    """Create one row per team per match before matchup assembly."""

    return matches.copy()
