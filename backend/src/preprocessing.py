"""Data loading, cleaning, and validation utilities for the IPL dataset."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "backend" / "data"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "Processed"


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
