"""Data loading, cleaning, and validation utilities for the IPL dataset."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "backend" / "data"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "Processed"


BALLS_RENAME_MAP = {
    "match_id": "match_id",
    "innings_id": "innings_id",
    "over_id": "over_id",
    "ball_id": "ball_id",
    "team_batting_id": "batting_team_id",
    "team_bowling_id": "bowling_team_id",
    "striker_id": "striker_id",
    "striker_batting_position": "striker_batting_position",
    "non_striker_id": "non_striker_id",
    "bowler_id": "bowler_id",
    "batsman_scored": "batsman_scored",
    "extra_type": "extra_type",
    "extra_runs": "extra_runs",
    "player_dissimal_id": "player_dismissal_id",
    "dissimal_type": "dismissal_type",
    "fielder_id": "fielder_id",
}

MATCH_RENAME_MAP = {
    "team_name_id": "team_id",
    "opponent_team_id": "opponent_team_id",
    "venue_name": "venue_name",
    "toss_winner_id": "toss_winner_id",
    "toss_decision": "toss_decision",
    "is_superover": "is_superover",
    "is_result": "is_result",
    "is_duckworthlewis": "is_duckworth_lewis",
    "win_type": "win_type",
    "won_by": "won_by",
    "match_winner_id": "winner_team_id",
    "city_name": "city_name",
    "host_country": "host_country",
}

STRING_MISSING_VALUES = {"", "NA", "N/A", "NULL", "None", "nan"}
PLAYER_DROP_COLUMNS = ["unnamed_7"]
NUMERIC_BALL_COLUMNS = [
    "match_id",
    "innings_id",
    "over_id",
    "ball_id",
    "batting_team_id",
    "bowling_team_id",
    "striker_id",
    "striker_batting_position",
    "non_striker_id",
    "bowler_id",
    "batsman_scored",
    "extra_runs",
]
NUMERIC_MATCH_COLUMNS = [
    "match_id",
    "team_id",
    "opponent_team_id",
    "season_id",
    "toss_winner_id",
    "is_superover",
    "is_result",
    "is_duckworth_lewis",
    "won_by",
    "winner_team_id",
    "man_of_the_match_id",
    "first_umpire_id",
    "second_umpire_id",
]


@dataclass(slots=True)
class ValidationIssue:
    """Simple validation issue container for audit reporting."""

    name: str
    severity: str
    rows: int
    details: dict[str, Any]


def load_csv_table(path: Path) -> pd.DataFrame:
    """Load a single CSV table from disk."""

    return pd.read_csv(path)


def load_raw_tables(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load all raw IPL tables into memory."""

    return {
        "balls": load_csv_table(data_dir / "Ball_by_Ball.csv"),
        "matches": load_csv_table(data_dir / "Match.csv"),
        "players": load_csv_table(data_dir / "Player.csv"),
        "player_match": load_csv_table(data_dir / "Player_Match.csv"),
        "seasons": load_csv_table(data_dir / "Season.csv"),
        "teams": load_csv_table(data_dir / "Team.csv"),
    }


def ensure_output_dir(output_dir: Path = OUTPUT_DIR) -> Path:
    """Create the processed output directory if needed."""

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def to_snake_case(name: str) -> str:
    """Normalize raw column names to snake case."""

    cleaned = re.sub(r"[^0-9A-Za-z]+", "_", name.strip())
    cleaned = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", cleaned)
    return cleaned.strip("_").lower()


def normalize_column_names(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with snake_case columns."""

    normalized = frame.copy()
    normalized.columns = [to_snake_case(column) for column in normalized.columns]
    return normalized


def normalize_table_columns(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Normalize schema names across the loaded tables."""

    normalized = {
        name: normalize_column_names(frame)
        for name, frame in tables.items()
    }

    normalized["balls"] = normalized["balls"].rename(columns=BALLS_RENAME_MAP)
    normalized["matches"] = normalized["matches"].rename(columns=MATCH_RENAME_MAP)
    return normalized


def clean_string_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Trim whitespace and standardize blank-like strings."""

    cleaned = frame.copy()
    object_columns = cleaned.select_dtypes(include="object").columns
    for column in object_columns:
        values = cleaned[column].astype(str).str.strip()
        values = values.replace(list(STRING_MISSING_VALUES), pd.NA)
        cleaned[column] = values
    return cleaned


def parse_match_dates(matches: pd.DataFrame) -> pd.DataFrame:
    """Parse the IPL date format into an actual timestamp."""

    parsed = matches.copy()
    parsed["match_date"] = pd.to_datetime(parsed["match_date"], format="%d-%b-%y")
    return parsed


def apply_basic_types(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Apply the initial set of string cleanup and type conversions."""

    typed = {name: clean_string_columns(frame) for name, frame in tables.items()}
    typed["matches"] = parse_match_dates(typed["matches"])
    return typed


def drop_noisy_columns(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Drop clearly empty or irrelevant raw columns."""

    cleaned = {name: frame.copy() for name, frame in tables.items()}
    existing_player_drops = [
        column for column in PLAYER_DROP_COLUMNS
        if column in cleaned["players"].columns
    ]
    if existing_player_drops:
        cleaned["players"] = cleaned["players"].drop(columns=existing_player_drops)
    return cleaned


def clean_ball_columns(balls: pd.DataFrame) -> pd.DataFrame:
    """Apply ball-by-ball specific cleaning and derived metrics."""

    cleaned = balls.copy()
    for column in NUMERIC_BALL_COLUMNS:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned["player_dismissal_id"] = pd.to_numeric(
        cleaned["player_dismissal_id"],
        errors="coerce",
    )
    cleaned["fielder_id"] = pd.to_numeric(cleaned["fielder_id"], errors="coerce")
    cleaned["extra_type"] = cleaned["extra_type"].fillna("none").str.lower()
    cleaned["dismissal_type"] = cleaned["dismissal_type"].fillna("none").str.lower()

    cleaned["total_runs"] = cleaned["batsman_scored"] + cleaned["extra_runs"]
    cleaned["is_wicket"] = cleaned["player_dismissal_id"].notna().astype(int)
    cleaned["is_legal_delivery"] = (~cleaned["extra_type"].isin({"wides", "noballs"})).astype(int)
    return cleaned


def clean_match_columns(matches: pd.DataFrame) -> pd.DataFrame:
    """Apply match-level normalization for modeling use."""

    cleaned = matches.copy()
    for column in NUMERIC_MATCH_COLUMNS:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned["toss_decision"] = cleaned["toss_decision"].str.lower()
    cleaned["win_type"] = cleaned["win_type"].str.lower()
    cleaned["venue_name"] = cleaned["venue_name"].fillna("unknown")
    cleaned["city_name"] = cleaned["city_name"].fillna("unknown")
    cleaned["host_country"] = cleaned["host_country"].fillna("unknown")
    return cleaned


def clean_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Run the full repository cleaning flow."""

    cleaned = normalize_table_columns(tables)
    cleaned = apply_basic_types(cleaned)
    cleaned = drop_noisy_columns(cleaned)
    cleaned["balls"] = clean_ball_columns(cleaned["balls"])
    cleaned["matches"] = clean_match_columns(cleaned["matches"])
    return cleaned


def summarize_table(frame: pd.DataFrame) -> dict[str, Any]:
    """Collect a compact profile for a single table."""

    return {
        "rows": int(frame.shape[0]),
        "columns": int(frame.shape[1]),
        "column_names": list(frame.columns),
        "missing_values": {
            column: int(count)
            for column, count in frame.isna().sum().items()
            if int(count) > 0
        },
    }


def build_data_audit(tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Create a data audit payload for repository inspection."""

    matches = tables["matches"]
    seasons = tables["seasons"]
    return {
        "generated_on": date.today().isoformat(),
        "tables": {
            name: summarize_table(frame)
            for name, frame in tables.items()
        },
        "season_years": sorted(seasons["season_year"].tolist()),
        "match_date_range": {
            "start": matches["match_date"].min().date().isoformat(),
            "end": matches["match_date"].max().date().isoformat(),
        },
    }
