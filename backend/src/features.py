"""Feature engineering helpers for leakage-safe IPL match modeling."""

from __future__ import annotations

import pandas as pd


ROLLING_WINDOWS = (3, 5)


def _rate_from_phase(group: pd.DataFrame) -> float:
    legal_balls = group["is_legal_delivery"].sum()
    if legal_balls == 0:
        return 0.0
    return float(group["total_runs"].sum() / (legal_balls / 6.0))


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


def build_phase_run_rates(balls: pd.DataFrame) -> pd.DataFrame:
    """Compute powerplay, middle, and death over scoring rates."""

    primary_innings = add_ball_outcome_flags(balls)
    primary_innings = primary_innings[primary_innings["innings_id"] <= 2].copy()

    phase_rates = (
        primary_innings.groupby(
            ["match_id", "innings_id", "batting_team_id", "phase"],
            observed=True,
        )
        .apply(_rate_from_phase)
        .rename("phase_run_rate")
        .reset_index()
    )
    phase_rates = phase_rates.pivot_table(
        index=["match_id", "innings_id", "batting_team_id"],
        columns="phase",
        values="phase_run_rate",
        fill_value=0.0,
    ).reset_index()
    phase_rates.columns.name = None
    phase_rates = phase_rates.rename(
        columns={
            "powerplay": "powerplay_run_rate",
            "middle": "middle_over_run_rate",
            "death": "death_over_run_rate",
        }
    )
    return phase_rates


def _shifted_group_expanding_mean(
    frame: pd.DataFrame,
    group_column: str,
    value_column: str,
) -> pd.Series:
    grouped = frame.groupby(group_column)[value_column]
    return grouped.transform(lambda values: values.shift().expanding().mean())


def _shifted_group_rolling_mean(
    frame: pd.DataFrame,
    group_column: str,
    value_column: str,
    window: int,
) -> pd.Series:
    grouped = frame.groupby(group_column)[value_column]
    return grouped.transform(lambda values: values.shift().rolling(window, min_periods=1).mean())


def add_team_form_features(team_frame: pd.DataFrame) -> pd.DataFrame:
    """Add win-rate features based only on prior matches."""

    enriched = team_frame.sort_values(["match_date", "match_id", "team_id"]).copy()
    enriched["matches_played_before"] = enriched.groupby("team_id").cumcount()
    enriched["win_rate_before_match"] = _shifted_group_expanding_mean(
        enriched,
        "team_id",
        "won_match",
    ).fillna(0.5)
    enriched["last_5_matches_win_rate"] = _shifted_group_rolling_mean(
        enriched,
        "team_id",
        "won_match",
        window=5,
    ).fillna(0.5)
    return enriched


def add_batting_history_features(team_frame: pd.DataFrame) -> pd.DataFrame:
    """Add rolling batting form features for each team."""

    enriched = team_frame.copy()
    batting_metrics = [
        "batting_run_rate",
        "batting_powerplay_run_rate",
        "batting_middle_over_run_rate",
        "batting_death_over_run_rate",
        "batting_boundary_percentage",
    ]
    for column in batting_metrics:
        enriched[f"{column}_mean_before_match"] = _shifted_group_expanding_mean(
            enriched,
            "team_id",
            column,
        ).fillna(0.0)
    return enriched


def add_bowling_history_features(team_frame: pd.DataFrame) -> pd.DataFrame:
    """Add expanding bowling form features for each team."""

    enriched = team_frame.copy()
    bowling_metrics = [
        "bowling_run_rate_conceded",
        "bowling_wicket_rate",
        "bowling_dot_ball_percentage",
        "bowling_boundary_percentage_conceded",
        "bowling_powerplay_run_rate_conceded",
        "bowling_death_over_run_rate_conceded",
    ]
    for column in bowling_metrics:
        enriched[f"{column}_mean_before_match"] = _shifted_group_expanding_mean(
            enriched,
            "team_id",
            column,
        ).fillna(0.0)
    return enriched


def add_recent_rolling_metrics(team_frame: pd.DataFrame) -> pd.DataFrame:
    """Add short rolling windows to approximate recent form."""

    enriched = team_frame.copy()
    recent_metrics = [
        "batting_run_rate",
        "bowling_run_rate_conceded",
        "bowling_wicket_rate",
    ]
    for window in ROLLING_WINDOWS:
        for column in recent_metrics:
            enriched[f"{column}_last_{window}"] = _shifted_group_rolling_mean(
                enriched,
                "team_id",
                column,
                window=window,
            ).fillna(0.0)
    return enriched


def add_venue_history_features(team_frame: pd.DataFrame) -> pd.DataFrame:
    """Track how each team has historically performed at a venue."""

    enriched = team_frame.copy()
    venue_key = enriched["team_id"].astype(str) + "::" + enriched["venue_name"]
    enriched["venue_matches_before"] = (
        enriched.assign(_venue_key=venue_key)
        .groupby("_venue_key")
        .cumcount()
    )
    enriched["venue_win_rate_before_match"] = (
        enriched.assign(_venue_key=venue_key)
        .groupby("_venue_key")["won_match"]
        .transform(lambda values: values.shift().expanding().mean())
        .fillna(0.5)
    )
    return enriched


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
    innings["overs_faced"] = innings["legal_balls"] / 6.0
    innings["run_rate"] = innings["total_runs"] / innings["overs_faced"].where(innings["overs_faced"] > 0, 1)
    innings["wicket_rate"] = innings["wickets_lost"] / innings["legal_balls"].where(innings["legal_balls"] > 0, 1)
    innings["dot_ball_percentage"] = innings["dot_balls"] / innings["legal_balls"].where(innings["legal_balls"] > 0, 1)
    innings["boundary_percentage"] = innings["boundary_balls"] / innings["legal_balls"].where(innings["legal_balls"] > 0, 1)

    phase_rates = build_phase_run_rates(primary_innings)
    innings = innings.merge(
        phase_rates,
        on=["match_id", "innings_id", "batting_team_id"],
        how="left",
    )
    innings[[
        "powerplay_run_rate",
        "middle_over_run_rate",
        "death_over_run_rate",
    ]] = innings[[
        "powerplay_run_rate",
        "middle_over_run_rate",
        "death_over_run_rate",
    ]].fillna(0.0)
    return innings


def build_team_history_frame(
    matches: pd.DataFrame,
    innings_stats: pd.DataFrame,
) -> pd.DataFrame:
    """Create one row per team per match before matchup assembly."""

    team_frame = matches[[
        "match_id",
        "match_date",
        "season_id",
        "team_id",
        "opponent_team_id",
        "venue_name",
        "city_name",
        "host_country",
        "toss_winner_id",
        "toss_decision",
        "is_superover",
        "is_duckworth_lewis",
        "winner_team_id",
    ]].copy()
    team_frame["won_match"] = (team_frame["team_id"] == team_frame["winner_team_id"]).astype(int)
    team_frame["lost_match"] = (
        (team_frame["winner_team_id"].notna()) &
        (team_frame["team_id"] != team_frame["winner_team_id"])
    ).astype(int)

    batting_columns = [
        "match_id",
        "batting_team_id",
        "total_runs",
        "wickets_lost",
        "legal_balls",
        "run_rate",
        "wicket_rate",
        "dot_ball_percentage",
        "boundary_percentage",
        "powerplay_run_rate",
        "middle_over_run_rate",
        "death_over_run_rate",
    ]
    batting_stats = innings_stats[batting_columns].rename(
        columns={
            "batting_team_id": "team_id",
            "total_runs": "batting_runs",
            "wickets_lost": "batting_wickets_lost",
            "legal_balls": "batting_legal_balls",
            "run_rate": "batting_run_rate",
            "wicket_rate": "batting_wicket_rate",
            "dot_ball_percentage": "batting_dot_ball_percentage",
            "boundary_percentage": "batting_boundary_percentage",
            "powerplay_run_rate": "batting_powerplay_run_rate",
            "middle_over_run_rate": "batting_middle_over_run_rate",
            "death_over_run_rate": "batting_death_over_run_rate",
        }
    )
    team_frame = team_frame.merge(
        batting_stats,
        on=["match_id", "team_id"],
        how="left",
    )

    bowling_columns = [
        "match_id",
        "bowling_team_id",
        "total_runs",
        "wickets_lost",
        "legal_balls",
        "run_rate",
        "wicket_rate",
        "dot_ball_percentage",
        "boundary_percentage",
        "powerplay_run_rate",
        "middle_over_run_rate",
        "death_over_run_rate",
    ]
    bowling_stats = innings_stats[bowling_columns].rename(
        columns={
            "bowling_team_id": "team_id",
            "total_runs": "bowling_runs_conceded",
            "wickets_lost": "bowling_wickets_taken",
            "legal_balls": "bowling_legal_balls",
            "run_rate": "bowling_run_rate_conceded",
            "wicket_rate": "bowling_wicket_rate",
            "dot_ball_percentage": "bowling_dot_ball_percentage",
            "boundary_percentage": "bowling_boundary_percentage_conceded",
            "powerplay_run_rate": "bowling_powerplay_run_rate_conceded",
            "middle_over_run_rate": "bowling_middle_over_run_rate_conceded",
            "death_over_run_rate": "bowling_death_over_run_rate_conceded",
        }
    )
    team_frame = team_frame.merge(
        bowling_stats,
        on=["match_id", "team_id"],
        how="left",
    )
    return team_frame
