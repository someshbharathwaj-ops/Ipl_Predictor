"""Data loading, cleaning, and validation utilities for the IPL dataset."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "backend" / "data"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "Processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
PRIMARY_IPL_PATH = DATA_DIR / "IPL.csv"


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
    "is_duck_worth_lewis": "is_duckworth_lewis",
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
    "striker_batting_position",
    "batsman_scored",
    "extra_runs",
]
NUMERIC_MATCH_COLUMNS = [
    "match_id",
    "season_id",
    "is_superover",
    "is_result",
    "is_duckworth_lewis",
    "won_by",
]
MATCH_EXPORT_COLUMNS = [
    "source_system",
    "source_file",
    "match_id",
    "match_date",
    "season_id",
    "season_year",
    "team_id",
    "opponent_team_id",
    "venue_name",
    "city_name",
    "host_country",
    "toss_winner_id",
    "toss_decision",
    "is_superover",
    "is_result",
    "is_duckworth_lewis",
    "win_type",
    "won_by",
    "winner_team_id",
]
BALL_EXPORT_COLUMNS = [
    "source_system",
    "source_file",
    "match_id",
    "match_date",
    "season_id",
    "season_year",
    "innings_id",
    "over_id",
    "ball_id",
    "batting_team_id",
    "bowling_team_id",
    "striker_id",
    "striker_batting_position",
    "non_striker_id",
    "bowler_id",
    "runs",
    "extras",
    "extra_type",
    "total_runs",
    "player_dismissal_id",
    "dismissal_type",
    "fielder_id",
    "is_wicket",
    "is_legal_delivery",
    "over_phase",
]


@dataclass(slots=True)
class ValidationIssue:
    """Simple validation issue container for audit reporting."""

    name: str
    severity: str
    rows: int
    details: dict[str, Any]


@dataclass(slots=True)
class SourceAvailability:
    """Tracks whether an external source is ready for ingestion."""

    source_name: str
    enabled: bool
    path: str | None
    notes: str


def load_csv_table(path: Path) -> pd.DataFrame:
    """Load a single CSV table from disk."""

    return pd.read_csv(path)


def has_primary_ipl_csv(path: Path = PRIMARY_IPL_PATH) -> bool:
    """Return whether the unified IPL source file is available."""

    return path.exists()


def _first_non_null(series: pd.Series) -> Any:
    non_null = series.dropna()
    return non_null.iloc[0] if not non_null.empty else pd.NA


def _extract_margin_value(value: Any) -> float | None:
    if value is pd.NA or value is None:
        return None
    match = re.search(r"(\d+)", str(value))
    return float(match.group(1)) if match else None


def _extract_win_type(value: Any) -> str | None:
    if value is pd.NA or value is None:
        return None
    lowered = str(value).strip().lower()
    if lowered.endswith("runs"):
        return "by runs"
    if lowered.endswith("wickets"):
        return "by wickets"
    return lowered or None


def build_tables_from_primary_ipl(path: Path = PRIMARY_IPL_PATH) -> dict[str, pd.DataFrame]:
    """Build canonical repository tables from the unified IPL ball-by-ball source."""

    raw = pd.read_csv(path, low_memory=False)
    raw = normalize_column_names(raw)
    if "unnamed_0" in raw.columns:
        raw = raw.drop(columns=["unnamed_0"])

    raw["date"] = pd.to_datetime(raw["date"], errors="coerce")
    raw["match_id"] = pd.to_numeric(raw["match_id"], errors="coerce").astype("Int64")
    raw["innings"] = pd.to_numeric(raw["innings"], errors="coerce").astype("Int64")
    raw["over"] = pd.to_numeric(raw["over"], errors="coerce")
    raw["ball"] = pd.to_numeric(raw["ball"], errors="coerce")
    raw["bat_pos"] = pd.to_numeric(raw["bat_pos"], errors="coerce")
    raw["runs_batter"] = pd.to_numeric(raw["runs_batter"], errors="coerce").fillna(0)
    raw["runs_extras"] = pd.to_numeric(raw["runs_extras"], errors="coerce").fillna(0)
    raw["runs_total"] = pd.to_numeric(raw["runs_total"], errors="coerce").fillna(
        raw["runs_batter"] + raw["runs_extras"]
    )
    raw["valid_ball"] = pd.to_numeric(raw["valid_ball"], errors="coerce").fillna(0).astype(int)
    raw["year"] = pd.to_numeric(raw["year"], errors="coerce").astype("Int64")

    balls = pd.DataFrame(
        {
            "match_id": raw["match_id"],
            "innings_id": raw["innings"],
            "over_id": raw["over"].fillna(0).astype(int) + 1,
            "ball_id": raw["ball"].fillna(0).astype(int),
            "batting_team_id": raw["batting_team"],
            "bowling_team_id": raw["bowling_team"],
            "striker_id": raw["batter"],
            "striker_batting_position": raw["bat_pos"],
            "non_striker_id": raw["non_striker"],
            "bowler_id": raw["bowler"],
            "batsman_scored": raw["runs_batter"],
            "extra_type": raw["extra_type"],
            "extra_runs": raw["runs_extras"],
            "player_dismissal_id": raw["player_out"],
            "dismissal_type": raw["wicket_kind"],
            "fielder_id": raw["fielders"],
            "match_date": raw["date"],
            "season_id": raw["year"],
            "season_year": raw["year"],
            "source_system": "ipl_csv",
            "source_file": path.name,
            "valid_ball": raw["valid_ball"],
            "runs": raw["runs_batter"],
            "extras": raw["runs_extras"],
            "total_runs": raw["runs_total"],
        }
    )

    first_ball = raw.sort_values(["match_id", "innings", "over", "ball"]).groupby("match_id", as_index=False).first()
    matches = pd.DataFrame(
        {
            "match_id": first_ball["match_id"],
            "match_date": first_ball["date"],
            "team_id": first_ball["batting_team"],
            "opponent_team_id": first_ball["bowling_team"],
            "season_id": first_ball["year"],
            "season_year": first_ball["year"],
            "venue_name": first_ball["venue"],
            "toss_winner_id": first_ball["toss_winner"],
            "toss_decision": first_ball["toss_decision"],
            "is_superover": first_ball["superover_winner"].notna().astype(int),
            "is_result": first_ball["match_won_by"].notna().astype(int),
            "is_duckworth_lewis": first_ball["method"].notna().astype(int),
            "win_type": first_ball["win_outcome"].map(_extract_win_type),
            "won_by": first_ball["win_outcome"].map(_extract_margin_value),
            "winner_team_id": first_ball["match_won_by"],
            "man_of_the_match_id": first_ball["player_of_match"],
            "first_umpire_id": pd.NA,
            "second_umpire_id": pd.NA,
            "city_name": first_ball["city"],
            "host_country": "India",
            "source_system": "ipl_csv",
            "source_file": path.name,
        }
    )

    team_names = pd.Index(
        pd.concat([raw["batting_team"], raw["bowling_team"], raw["toss_winner"], raw["match_won_by"]])
        .dropna()
        .astype(str)
        .unique()
    )
    teams = pd.DataFrame(
        {
            "team_id": team_names.astype(str),
            "team_name": team_names.astype(str),
            "team_short_code": pd.NA,
        }
    ).sort_values("team_name").reset_index(drop=True)

    player_names = pd.Index(
        pd.concat(
            [
                raw["batter"],
                raw["non_striker"],
                raw["bowler"],
                raw["player_out"],
                raw["player_of_match"],
            ]
        )
        .dropna()
        .astype(str)
        .unique()
    )
    players = pd.DataFrame(
        {
            "player_id": player_names.astype(str),
            "player_name": player_names.astype(str),
        }
    ).sort_values("player_name").reset_index(drop=True)

    seasons = pd.DataFrame(
        {
            "season_id": sorted(raw["year"].dropna().astype(int).unique().tolist()),
        }
    )
    seasons["season_year"] = seasons["season_id"]

    player_match = pd.DataFrame(
        columns=["match_id", "player_id", "team_id", "is_keeper", "is_captain"]
    )

    return {
        "balls": balls,
        "matches": matches,
        "players": players,
        "player_match": player_match,
        "seasons": seasons,
        "teams": teams,
    }


def load_raw_tables(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load all raw IPL tables into memory."""

    if has_primary_ipl_csv(data_dir / "IPL.csv"):
        return build_tables_from_primary_ipl(data_dir / "IPL.csv")

    return {
        "balls": load_csv_table(data_dir / "Ball_by_Ball.csv"),
        "matches": load_csv_table(data_dir / "Match.csv"),
        "players": load_csv_table(data_dir / "Player.csv"),
        "player_match": load_csv_table(data_dir / "Player_Match.csv"),
        "seasons": load_csv_table(data_dir / "Season.csv"),
        "teams": load_csv_table(data_dir / "Team.csv"),
    }


def describe_external_sources(data_dir: Path = EXTERNAL_DATA_DIR) -> list[SourceAvailability]:
    """Summarize which optional external sources are currently available locally."""

    source_dirs = ensure_external_data_dirs(data_dir)
    availability: list[SourceAvailability] = []
    for source_name, path in source_dirs.items():
        files = sorted(file.name for file in path.glob("*") if file.is_file())
        enabled = bool(files)
        notes = "ready for ingestion" if enabled else "drop files here to enable this source"
        availability.append(
            SourceAvailability(
                source_name=source_name,
                enabled=enabled,
                path=str(path),
                notes=notes if not enabled else f"{notes}: {', '.join(files[:5])}",
            )
        )
    return availability


def ensure_output_dir(output_dir: Path = OUTPUT_DIR) -> Path:
    """Create the processed output directory if needed."""

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def ensure_external_data_dirs(data_dir: Path = EXTERNAL_DATA_DIR) -> dict[str, Path]:
    """Create optional drop-zones for external IPL data sources."""

    source_dirs = {
        "kaggle": data_dir / "kaggle",
        "cricsheet": data_dir / "cricsheet",
        "github": data_dir / "github",
        "api_cache": data_dir / "api_cache",
    }
    for path in source_dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return source_dirs


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
    if pd.api.types.is_datetime64_any_dtype(parsed["match_date"]):
        return parsed
    parsed["match_date"] = pd.to_datetime(parsed["match_date"], format="%d-%b-%y", errors="coerce")
    if parsed["match_date"].isna().any():
        parsed["match_date"] = pd.to_datetime(matches["match_date"], errors="coerce")
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
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned["batsman_scored"] = cleaned["batsman_scored"].fillna(0)
    cleaned["extra_runs"] = cleaned["extra_runs"].fillna(0)
    cleaned["extra_type"] = cleaned["extra_type"].fillna("none").str.lower()
    cleaned["dismissal_type"] = cleaned["dismissal_type"].fillna("none").str.lower()
    cleaned["player_dismissal_id"] = cleaned["player_dismissal_id"].replace(list(STRING_MISSING_VALUES), pd.NA)
    cleaned["fielder_id"] = cleaned["fielder_id"].replace(list(STRING_MISSING_VALUES), pd.NA)

    cleaned["runs"] = cleaned["batsman_scored"]
    cleaned["extras"] = cleaned["extra_runs"]
    cleaned["total_runs"] = cleaned["batsman_scored"] + cleaned["extra_runs"]
    cleaned["is_wicket"] = cleaned["player_dismissal_id"].notna().astype(int)
    if "valid_ball" in cleaned.columns:
        cleaned["is_legal_delivery"] = pd.to_numeric(cleaned["valid_ball"], errors="coerce").fillna(0).astype(int)
    else:
        cleaned["is_legal_delivery"] = (~cleaned["extra_type"].isin({"wides", "noballs"})).astype(int)
    cleaned["over_phase"] = pd.cut(
        cleaned["over_id"],
        bins=[0, 6, 15, 20],
        labels=["powerplay", "middle", "death"],
        include_lowest=True,
    ).astype("string")
    return cleaned


def clean_match_columns(matches: pd.DataFrame) -> pd.DataFrame:
    """Apply match-level normalization for modeling use."""

    cleaned = matches.copy()
    for column in NUMERIC_MATCH_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned["toss_decision"] = cleaned["toss_decision"].fillna("unknown").astype(str).str.lower()
    cleaned["win_type"] = cleaned["win_type"].fillna("unknown").astype(str).str.lower()
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
    return attach_match_context(cleaned)


def attach_match_context(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Attach season and date context to ball-level records."""

    enriched = {name: frame.copy() for name, frame in tables.items()}
    seasons = enriched["seasons"][["season_id", "season_year"]].copy()
    matches = enriched["matches"].copy()
    if "season_year" not in matches.columns:
        matches = matches.merge(seasons, on="season_id", how="left")
    if "source_system" not in matches.columns:
        matches["source_system"] = "legacy_csv"
    if "source_file" not in matches.columns:
        matches["source_file"] = "Match.csv"
    enriched["matches"] = matches

    balls = enriched["balls"].merge(
        matches[["match_id", "match_date", "season_id", "season_year"]],
        on="match_id",
        how="left",
    )
    if "source_system" not in balls.columns:
        balls["source_system"] = "legacy_csv"
    if "source_file" not in balls.columns:
        balls["source_file"] = "Ball_by_Ball.csv"
    enriched["balls"] = balls
    return enriched


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


def standardize_match_export(matches: pd.DataFrame) -> pd.DataFrame:
    """Project matches into the canonical expanded schema."""

    standardized = matches.copy()
    for column in MATCH_EXPORT_COLUMNS:
        if column not in standardized.columns:
            standardized[column] = pd.NA
    return standardized[MATCH_EXPORT_COLUMNS].sort_values(["season_year", "match_date", "match_id"])


def standardize_ball_export(balls: pd.DataFrame) -> pd.DataFrame:
    """Project balls into the canonical expanded schema."""

    standardized = balls.copy()
    for column in BALL_EXPORT_COLUMNS:
        if column not in standardized.columns:
            standardized[column] = pd.NA
    return standardized[BALL_EXPORT_COLUMNS].sort_values(
        ["season_year", "match_date", "match_id", "innings_id", "over_id", "ball_id"]
    )


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
        "external_source_availability": [
            {
                "source_name": source.source_name,
                "enabled": source.enabled,
                "path": source.path,
                "notes": source.notes,
            }
            for source in describe_external_sources()
        ],
    }


def _build_issue(
    name: str,
    severity: str,
    mask: pd.Series,
    **details: Any,
) -> ValidationIssue:
    return ValidationIssue(
        name=name,
        severity=severity,
        rows=int(mask.sum()),
        details=details,
    )


def validate_tables(tables: dict[str, pd.DataFrame]) -> list[ValidationIssue]:
    """Run logical integrity checks across the cleaned tables."""

    balls = tables["balls"]
    matches = tables["matches"]
    critical_match_fields = ["match_id", "match_date", "team_id", "opponent_team_id", "season_year"]
    critical_ball_fields = ["match_id", "innings_id", "over_id", "ball_id", "batting_team_id", "bowling_team_id"]

    issues = [
        _build_issue(
            "negative_total_runs",
            "error",
            balls["total_runs"] < 0,
        ),
        _build_issue(
            "invalid_over_range",
            "error",
            ~balls["over_id"].between(1, 20),
        ),
        _build_issue(
            "invalid_ball_range",
            "error",
            ~balls["ball_id"].between(1, 9),
        ),
        _build_issue(
            "no_result_matches",
            "warning",
            matches["winner_team_id"].isna(),
            match_ids=matches.loc[matches["winner_team_id"].isna(), "match_id"].tolist(),
        ),
        _build_issue(
            "missing_critical_match_fields",
            "error",
            matches[critical_match_fields].isna().any(axis=1),
        ),
        _build_issue(
            "missing_critical_ball_fields",
            "error",
            balls[critical_ball_fields].isna().any(axis=1),
        ),
    ]

    over_events = balls.groupby(["match_id", "innings_id", "over_id"]).size()
    issues.append(
        _build_issue(
            "overs_with_too_many_recorded_events",
            "warning",
            over_events > 9,
        ),
    )
    return issues


def serialize_validation_issues(issues: list[ValidationIssue]) -> list[dict[str, Any]]:
    """Convert validation results into JSON-friendly dictionaries."""

    return [
        {
            "name": issue.name,
            "severity": issue.severity,
            "rows": issue.rows,
            "details": issue.details,
        }
        for issue in issues
    ]


def fetch_match_data(match_id: str) -> dict[str, Any]:
    """Placeholder for Cricinfo/Cricbuzz match-level ingestion."""

    return {
        "match_id": match_id,
        "status": "placeholder",
        "source": "api_fallback",
        "message": "TODO: integrate Cricinfo/Cricbuzz match endpoint or scraper adapter.",
    }


def fetch_ball_by_ball(match_id: str) -> list[dict[str, Any]]:
    """Placeholder for Cricinfo/Cricbuzz ball-by-ball ingestion."""

    return [
        {
            "match_id": match_id,
            "status": "placeholder",
            "source": "api_fallback",
            "message": "TODO: fetch detailed innings commentary and convert it into canonical ball rows.",
        }
    ]


def fetch_match_list_by_season(season_year: int) -> list[str]:
    """Placeholder for season-wise match discovery."""

    return []


def ingest_api_season(season_year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pipeline shell for future Cricinfo/Cricbuzz ingestion."""

    match_ids = fetch_match_list_by_season(season_year)
    match_rows: list[dict[str, Any]] = []
    ball_rows: list[dict[str, Any]] = []
    for match_id in match_ids:
        match_rows.append(fetch_match_data(match_id))
        ball_rows.extend(fetch_ball_by_ball(match_id))
    return pd.DataFrame(match_rows), pd.DataFrame(ball_rows)


def build_api_ingestion_plan(season_start: int = 2017, season_end: int = 2025) -> dict[str, Any]:
    """Describe the fallback live-data ingestion workflow."""

    return {
        "mode": "fallback_api_design",
        "season_range": [season_start, season_end],
        "steps": [
            "fetch match ids for each season",
            "fetch match metadata for every discovered match",
            "fetch ball-by-ball commentary or innings feed",
            "map source fields into canonical match and ball schemas",
            "append deduplicated rows to the expanded dataset",
            "rerun cleaning, validation, and feature generation chronologically",
        ],
        "placeholders": [
            "fetch_match_list_by_season",
            "fetch_match_data",
            "fetch_ball_by_ball",
            "ingest_api_season",
        ],
    }


def build_expansion_status(
    cleaned_tables: dict[str, pd.DataFrame],
    requested_end_year: int = 2025,
) -> dict[str, Any]:
    """Summarize current coverage versus the desired 2008-2025 target."""

    matches = cleaned_tables["matches"]
    available_start = int(matches["season_year"].min())
    available_end = int(matches["season_year"].max())
    availability = describe_external_sources()
    return {
        "target_season_range": [2008, requested_end_year],
        "available_season_range": [available_start, available_end],
        "covers_target_range": available_end >= requested_end_year,
        "gap_seasons": list(range(available_end + 1, requested_end_year + 1)),
        "external_sources": [
            {
                "source_name": source.source_name,
                "enabled": source.enabled,
                "path": source.path,
                "notes": source.notes,
            }
            for source in availability
        ],
        "api_fallback_required": available_end < requested_end_year
        and not any(source.enabled for source in availability if source.source_name != "api_cache"),
    }


def write_json_payload(payload: dict[str, Any] | list[dict[str, Any]], path: Path) -> None:
    """Persist JSON output with stable formatting."""

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
