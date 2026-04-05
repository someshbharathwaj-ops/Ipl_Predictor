"""Train the micrograd IPL winner model using the processed dataset."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import functools
import math
import os
import pickle
import random
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "backend" / "src"
PROCESSED_DATASET_PATH = PROJECT_ROOT / "backend" / "Processed" / "micrograd_model_input.csv"
TEAM_HISTORY_PATH = PROJECT_ROOT / "backend" / "Processed" / "team_history_features.csv"
MATCH_DATASET_PATH = PROJECT_ROOT / "backend" / "Processed" / "match_dataset.csv"
MODEL_OUTPUT_PATH = PROJECT_ROOT / "backend" / "models" / "model.pkl"
IPL_SOURCE_PATH = PROJECT_ROOT / "backend" / "data" / "IPL.csv"
PIPELINE_ENTRYPOINT = SRC_DIR / "maindataset.py"
REQUIRED_PROCESSED_PATHS = (
    PROCESSED_DATASET_PATH,
    TEAM_HISTORY_PATH,
    MATCH_DATASET_PATH,
)
DELTA_METRICS = [
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
TEAM_SHORTLIST = [
    "Chennai Super Kings",
    "Mumbai Indians",
    "Royal Challengers Bengaluru",
    "Kolkata Knight Riders",
    "Rajasthan Royals",
    "Delhi Capitals",
    "Sunrisers Hyderabad",
    "Punjab Kings",
    "Gujarat Titans",
    "Lucknow Super Giants",
]
KEY_PLAYER_SHORTLIST = {
    "Chennai Super Kings": ["MS Dhoni", "Sanju samson", "Ruturaj Gaikwad", "Ayush Mathare", "Noor Ahemd" , "Khaleel ahemad"],
    "Mumbai Indians": ["Rohit Sharma", "Jasprit Bumrah", "Suryakumar Yadav", "Jasprit Bumrah", "Hardik Pandya"],
    "Royal Challengers Bengaluru": ["Virat Kohli", "Hazlewood", "Duffy", "Phil salt", "Rajat Patidar","jitesh sharma","Krunal pandya"],
    "Kolkata Knight Riders": ["Finn Alen", "Sunil Narine", "Rahuvanshi", "varun", "Rinku Singh"],
    "Rajasthan Royals": ["Vaibhav", "Riyan parag", "Yashasvi Jaiswal", "Archer", "Burger"],
    "Delhi Capitals": ["KL rahul", "Rizvi", "Axar Patel", "Stubbs", "Kuldeep Yadav","Ingidi"],
    "Sunrisers Hyderabad": ["Pat Cummins", "Heinrich Klaasen", "Travis Head", "Abishek", "Unadkat"],
    "Punjab Kings": ["Shreyas Iyer", "Marco jansen", "Arshdeep Singh", "Prabhsimran", "Arya"],
    "Gujarat Titans": ["Shubman Gill", "Rashid Khan", "Sai Sudharsan", "Rabada", "Thevatiya"],
    "Lucknow Super Giants": ["Rishabh pant", "Nicholas Pooran", "Adam markram", "Shami", "Mohsin Khan"],
}
NEUTRAL_CONTEXT_DEFAULTS = {
    "team1_is_toss_winner": 0.0,
    "team2_is_toss_winner": 0.0,
    "team1_home_country": 1.0,
    "team1_won_toss": 0.0,
    "team2_won_toss": 0.0,
    "team1_toss_decision_is_bat": 0.0,
    "team1_toss_decision_is_field": 1.0,
    "team2_toss_decision_is_bat": 0.0,
    "team2_toss_decision_is_field": 1.0,
    "team1_won_toss_and_batted": 0.0,
    "team1_won_toss_and_fielded": 0.0,
    "team2_won_toss_and_batted": 0.0,
    "team2_won_toss_and_fielded": 0.0,
}


@dataclass(slots=True)
class PredictionRequest:
    team1: str
    team2: str
    toss_winner: str
    user_predicted_score_team1: int
    user_predicted_score_team2: int
    key_player_team1: str
    key_player_team2: str


def load_module(name: str, path: Path):
    """Load a Python source file from an explicit path."""

    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None:
        raise ImportError(f"Unable to create import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


micrograd_module = load_module("micrograd", SRC_DIR / "micrograd.py")
network_module = load_module("Neuron", SRC_DIR / "Neuron")

Value = micrograd_module.Value
MLP = network_module.MLP


@functools.lru_cache(maxsize=1)
def ensure_processed_artifacts() -> None:
    """Generate processed datasets from raw IPL data when deployment starts cold."""

    if all(path.exists() for path in REQUIRED_PROCESSED_PATHS):
        return

    result = subprocess.run(
        [sys.executable, str(PIPELINE_ENTRYPOINT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        error_output = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Failed to build processed datasets: {error_output}")

    missing = [str(path) for path in REQUIRED_PROCESSED_PATHS if not path.exists()]
    if missing:
        raise RuntimeError(
            "Processed datasets are still missing after pipeline generation: "
            + ", ".join(missing)
        )


def ensure_model_artifact() -> None:
    """Train a model automatically when deployment has no saved weights yet."""

    ensure_processed_artifacts()
    if MODEL_OUTPUT_PATH.exists():
        return

    epochs = int(os.getenv("MICROGRAD_EPOCHS", "1"))
    learning_rate = float(os.getenv("MICROGRAD_LR", "0.005"))
    batch_size = int(os.getenv("MICROGRAD_BATCH", "16"))
    seed = int(os.getenv("MICROGRAD_SEED", "42"))
    train_model(
        epochs=epochs,
        learning_rate=learning_rate,
        batch_size=batch_size,
        seed=seed,
    )

    if not MODEL_OUTPUT_PATH.exists():
        raise RuntimeError("Model training completed without producing model.pkl")


def load_dataset(path: Path = PROCESSED_DATASET_PATH) -> tuple[pd.DataFrame, pd.Series]:
    """Load the processed micrograd training dataset."""

    ensure_processed_artifacts()
    frame = pd.read_csv(path)
    if "target" not in frame.columns:
        raise ValueError("Expected a target column in micrograd_model_input.csv")

    features = frame.drop(columns=["target"]).copy()
    target = frame["target"].astype(float).copy()
    return features, target


def load_team_history(path: Path = TEAM_HISTORY_PATH) -> pd.DataFrame:
    """Load the processed team history feature table."""

    ensure_processed_artifacts()
    frame = pd.read_csv(path)
    frame["match_date"] = pd.to_datetime(frame["match_date"], errors="coerce")
    return frame.sort_values(["match_date", "match_id"]).reset_index(drop=True)


def load_match_dataset(path: Path = MATCH_DATASET_PATH) -> pd.DataFrame:
    """Load the wide match-level feature dataset."""

    ensure_processed_artifacts()
    frame = pd.read_csv(path)
    frame["match_date"] = pd.to_datetime(frame["match_date"], errors="coerce")
    return frame.sort_values(["match_date", "match_id"]).reset_index(drop=True)


@functools.lru_cache(maxsize=1)
def load_key_players_by_team(path: Path = IPL_SOURCE_PATH) -> dict[str, list[str]]:
    """Return fast key-player options for the UI without blocking metadata."""

    return KEY_PLAYER_SHORTLIST.copy()


def chronological_split(
    features: pd.DataFrame,
    target: pd.Series,
    train_ratio: float = 0.8,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split the dataset by row order to avoid future leakage."""

    split_index = int(len(features) * train_ratio)
    x_train = features.iloc[:split_index].reset_index(drop=True)
    x_val = features.iloc[split_index:].reset_index(drop=True)
    y_train = target.iloc[:split_index].reset_index(drop=True)
    y_val = target.iloc[split_index:].reset_index(drop=True)
    return x_train, x_val, y_train, y_val


def fit_standard_scaler(features: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Compute feature-wise mean and standard deviation."""

    mean = features.mean(axis=0)
    std = features.std(axis=0, ddof=0).replace(0, 1.0)
    return mean, std


def transform_with_scaler(
    features: pd.DataFrame,
    mean: pd.Series,
    std: pd.Series,
    clip_value: float = 5.0,
) -> pd.DataFrame:
    """Apply standard scaling using a precomputed mean and std."""

    scaled = ((features - mean) / std).astype(float)
    scaled = scaled.clip(lower=-clip_value, upper=clip_value)
    return scaled


def validate_numeric_frame(features: pd.DataFrame, target: pd.Series) -> None:
    """Fail fast if the training matrix contains invalid numeric values."""

    if features.isna().any().any():
        raise ValueError("Feature matrix contains NaN values.")
    feature_values = features.to_numpy(dtype=float)
    if not np.isfinite(feature_values).all():
        raise ValueError("Feature matrix contains non-finite values.")
    if target.isna().any():
        raise ValueError("Target vector contains NaN values.")


def row_to_values(row: list[float]) -> list[Any]:
    """Convert a numeric row into the Value objects expected by micrograd."""

    return [Value(float(item)) for item in row]


def predict_probability(model: Any, row: list[float]) -> Any:
    """Run the model forward and map tanh output into [0, 1]."""

    raw_output = model(row_to_values(row))
    return (raw_output + 1.0) * 0.5


def zero_gradients(model: Any) -> None:
    """Reset parameter gradients before a new optimization step."""

    for parameter in model.parameters():
        parameter.grad = 0.0


def apply_parameter_update(model: Any, learning_rate: float, grad_clip: float = 1.0) -> None:
    """Apply a clipped SGD step to keep training numerically stable."""

    for parameter in model.parameters():
        grad = max(min(float(parameter.grad), grad_clip), -grad_clip)
        parameter.data -= learning_rate * grad
        parameter.data = max(min(float(parameter.data), 10.0), -10.0)


def batch_loss(model: Any, batch_x: list[list[float]], batch_y: list[float]) -> Any:
    """Compute mean squared error over a mini-batch."""

    losses = []
    for row, target in zip(batch_x, batch_y):
        prediction = predict_probability(model, row)
        target_value = Value(float(target))
        losses.append((prediction - target_value) ** 2)
    return sum(losses, Value(0.0)) * (1.0 / len(losses))


def evaluate_dataset(model: Any, features: pd.DataFrame, target: pd.Series) -> tuple[float, float]:
    """Measure MSE loss and rounded accuracy on a dataset."""

    rows = features.values.tolist()
    targets = target.tolist()
    mse_total = 0.0
    correct = 0
    for row, actual in zip(rows, targets):
        prediction = predict_probability_numeric(model, row)
        mse_total += (prediction - actual) ** 2
        predicted_label = 1 if prediction >= 0.5 else 0
        correct += int(predicted_label == int(actual))
    mse = mse_total / len(rows) if rows else 0.0
    accuracy = correct / len(rows) if rows else 0.0
    return mse, accuracy


def predict_probability_numeric(model: Any, row: list[float]) -> float:
    """Run a fast inference pass using the trained scalar parameters only."""

    activations = [float(value) for value in row]
    for layer in model.layers:
        next_activations = []
        for neuron in layer.neurons:
            total = neuron.b.data
            for weight, activation in zip(neuron.w, activations):
                total += weight.data * activation
            next_activations.append(math.tanh(total))
        activations = next_activations
    output = activations[0]
    return (output + 1.0) * 0.5


def predict_probability_from_payload(payload: dict[str, Any], row: list[float]) -> float:
    """Run numeric inference using the saved pickle payload."""

    activations = [float(value) for value in row]
    for layer in payload["layers"]:
        next_activations = []
        for neuron in layer["neurons"]:
            total = float(neuron["bias"])
            for weight, activation in zip(neuron["weights"], activations):
                total += float(weight) * activation
            next_activations.append(math.tanh(total))
        activations = next_activations
    output = activations[0]
    return (output + 1.0) * 0.5


def serialize_model(model: Any) -> list[dict[str, Any]]:
    """Extract trainable parameters into a pickle-friendly structure."""

    serialized_layers = []
    for layer in model.layers:
        serialized_neurons = []
        for neuron in layer.neurons:
            serialized_neurons.append(
                {
                    "weights": [weight.data for weight in neuron.w],
                    "bias": neuron.b.data,
                }
            )
        serialized_layers.append({"neurons": serialized_neurons})
    return serialized_layers


def save_model(
    model: Any,
    feature_columns: list[str],
    scaler_mean: pd.Series,
    scaler_std: pd.Series,
    path: Path = MODEL_OUTPUT_PATH,
) -> None:
    """Save the trained network weights and preprocessing metadata."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "architecture": [len(feature_columns), 16, 16, 1],
        "feature_columns": feature_columns,
        "scaler_mean": scaler_mean.to_dict(),
        "scaler_std": scaler_std.to_dict(),
        "layers": serialize_model(model),
    }
    with path.open("wb") as handle:
        pickle.dump(payload, handle)


def load_saved_model(path: Path = MODEL_OUTPUT_PATH) -> dict[str, Any]:
    """Load the serialized model payload from disk."""

    ensure_model_artifact()
    with path.open("rb") as handle:
        return pickle.load(handle)


def train_model(
    epochs: int = 1,
    learning_rate: float = 0.005,
    batch_size: int = 16,
    seed: int = 42,
) -> dict[str, Any]:
    """Train the MLP on the processed IPL dataset."""

    random.seed(seed)

    features, target = load_dataset()
    validate_numeric_frame(features, target)
    x_train, x_val, y_train, y_val = chronological_split(features, target)
    scaler_mean, scaler_std = fit_standard_scaler(x_train)
    x_train = transform_with_scaler(x_train, scaler_mean, scaler_std)
    x_val = transform_with_scaler(x_val, scaler_mean, scaler_std)

    model = MLP(x_train.shape[1], [16, 16, 1])
    train_rows = x_train.values.tolist()
    train_targets = y_train.tolist()

    for epoch in range(1, epochs + 1):
        order = list(range(len(train_rows)))
        random.shuffle(order)

        epoch_loss_total = 0.0
        batch_count = 0
        for batch_start in range(0, len(order), batch_size):
            batch_indices = order[batch_start: batch_start + batch_size]
            batch_x = [train_rows[index] for index in batch_indices]
            batch_y = [train_targets[index] for index in batch_indices]

            zero_gradients(model)
            loss = batch_loss(model, batch_x, batch_y)
            loss.backward()
            apply_parameter_update(model, learning_rate)

            epoch_loss_total += loss.data
            batch_count += 1

        train_mse, train_accuracy = evaluate_dataset(model, x_train, y_train)
        val_mse, val_accuracy = evaluate_dataset(model, x_val, y_val)
        average_batch_loss = epoch_loss_total / batch_count if batch_count else 0.0
        print(
            f"epoch={epoch:03d} "
            f"batch_loss={average_batch_loss:.4f} "
            f"train_mse={train_mse:.4f} "
            f"train_acc={train_accuracy:.3f} "
            f"val_mse={val_mse:.4f} "
            f"val_acc={val_accuracy:.3f}"
        )

    save_model(
        model=model,
        feature_columns=list(features.columns),
        scaler_mean=scaler_mean,
        scaler_std=scaler_std,
    )

    return {
        "train_rows": len(x_train),
        "validation_rows": len(x_val),
        "features": x_train.shape[1],
        "model_path": str(MODEL_OUTPUT_PATH),
    }


def canonicalize_team_name(name: str) -> str:
    """Normalize user-entered team names for matching."""

    return " ".join(name.strip().lower().split())


def build_team_lookup(team_history: pd.DataFrame) -> dict[str, str]:
    """Create a case-insensitive mapping of available team names."""

    unique_teams = sorted(team_history["team_id"].dropna().astype(str).unique().tolist())
    return {canonicalize_team_name(team): team for team in unique_teams}


def shortlisted_teams(team_history: pd.DataFrame) -> list[str]:
    """Return the preferred IPL team shortlist for the product UI."""

    team_lookup = build_team_lookup(team_history)
    shortlisted = []
    for team_name in TEAM_SHORTLIST:
        resolved = team_lookup.get(canonicalize_team_name(team_name))
        if resolved and resolved not in shortlisted:
            shortlisted.append(resolved)
    return shortlisted or sorted(team_lookup.values())


def resolve_team_name(user_input: str, team_lookup: dict[str, str]) -> str:
    """Resolve a user-entered team name to the canonical dataset name."""

    normalized = canonicalize_team_name(user_input)
    if normalized in team_lookup:
        return team_lookup[normalized]

    partial_matches = [
        canonical
        for key, canonical in team_lookup.items()
        if normalized in key or key in normalized
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    raise ValueError("Team name not recognized. Please use a team from the processed dataset.")


def latest_team_row(team_history: pd.DataFrame, team_name: str) -> pd.Series:
    """Get the latest available historical feature row for a franchise."""

    rows = team_history[team_history["team_id"] == team_name]
    if rows.empty:
        raise ValueError(f"No team history found for {team_name}")
    return rows.sort_values(["match_date", "match_id"]).iloc[-1]


def latest_head_to_head_row(team_history: pd.DataFrame, team_name: str, opponent_name: str) -> pd.Series | None:
    """Get the latest team-vs-opponent historical row if available."""

    rows = team_history[
        (team_history["team_id"] == team_name)
        & (team_history["opponent_team_id"] == opponent_name)
    ]
    if rows.empty:
        return None
    return rows.sort_values(["match_date", "match_id"]).iloc[-1]


def latest_matchup_row(match_dataset: pd.DataFrame, team1_name: str, team2_name: str) -> pd.Series | None:
    """Get the latest wide matchup row for two teams, regardless of stored ordering."""

    direct = match_dataset[
        (match_dataset["team1_team_id"] == team1_name)
        & (match_dataset["team2_team_id"] == team2_name)
    ]
    reverse = match_dataset[
        (match_dataset["team1_team_id"] == team2_name)
        & (match_dataset["team2_team_id"] == team1_name)
    ]
    combined = pd.concat([direct, reverse], ignore_index=True)
    if combined.empty:
        return None
    return combined.sort_values(["match_date", "match_id"]).iloc[-1]


def build_prediction_feature_row(
    team_history: pd.DataFrame,
    match_dataset: pd.DataFrame,
    team1_name: str,
    team2_name: str,
    toss_winner: str,
    feature_columns: list[str],
) -> pd.DataFrame:
    """Construct a model-ready single-row feature frame for two teams."""

    team1_latest = latest_team_row(team_history, team1_name)
    team2_latest = latest_team_row(team_history, team2_name)
    team1_h2h = latest_head_to_head_row(team_history, team1_name, team2_name)
    team2_h2h = latest_head_to_head_row(team_history, team2_name, team1_name)
    matchup_row = latest_matchup_row(match_dataset, team1_name, team2_name)
    toss_winner = toss_winner.strip()
    toss_winner_is_team1 = int(toss_winner == team1_name)
    toss_winner_is_team2 = int(toss_winner == team2_name)

    row: dict[str, float] = {}
    for column in feature_columns:
        if column.startswith("team1_"):
            source_column = column.removeprefix("team1_")
            value = team1_latest.get(source_column, 0.0)
            row[column] = float(value) if pd.notna(value) else 0.0
        elif column.startswith("team2_"):
            source_column = column.removeprefix("team2_")
            value = team2_latest.get(source_column, 0.0)
            row[column] = float(value) if pd.notna(value) else 0.0
        elif column.startswith("delta_"):
            metric = column.removeprefix("delta_")
            left = team1_latest.get(metric, 0.0)
            right = team2_latest.get(metric, 0.0)
            row[column] = float(left) - float(right)
        else:
            row[column] = 0.0

    if matchup_row is not None:
        for column in feature_columns:
            if column in matchup_row.index:
                value = matchup_row[column]
                row[column] = float(value) if pd.notna(value) else row.get(column, 0.0)

    if "team1_head_to_head_matches_before" in row and team1_h2h is not None:
        row["team1_head_to_head_matches_before"] = float(team1_h2h["head_to_head_matches_before"])
    if "team1_head_to_head_win_rate_before_match" in row and team1_h2h is not None:
        row["team1_head_to_head_win_rate_before_match"] = float(team1_h2h["head_to_head_win_rate_before_match"])
    if "team2_head_to_head_matches_before" in row and team2_h2h is not None:
        row["team2_head_to_head_matches_before"] = float(team2_h2h["head_to_head_matches_before"])
    if "team2_head_to_head_win_rate_before_match" in row and team2_h2h is not None:
        row["team2_head_to_head_win_rate_before_match"] = float(team2_h2h["head_to_head_win_rate_before_match"])

    for metric in DELTA_METRICS:
        delta_column = f"delta_{metric}"
        team1_column = f"team1_{metric}"
        team2_column = f"team2_{metric}"
        if delta_column in row and team1_column in row and team2_column in row:
            row[delta_column] = row[team1_column] - row[team2_column]

    for column, default_value in NEUTRAL_CONTEXT_DEFAULTS.items():
        if column in row:
            row[column] = default_value

    if "team1_is_toss_winner" in row:
        row["team1_is_toss_winner"] = float(toss_winner_is_team1)
    if "team2_is_toss_winner" in row:
        row["team2_is_toss_winner"] = float(toss_winner_is_team2)
    if "team1_won_toss" in row:
        row["team1_won_toss"] = float(toss_winner_is_team1)
    if "team2_won_toss" in row:
        row["team2_won_toss"] = float(toss_winner_is_team2)
    if "team1_toss_decision_is_field" in row:
        row["team1_toss_decision_is_field"] = 1.0
    if "team2_toss_decision_is_field" in row:
        row["team2_toss_decision_is_field"] = 1.0
    if "team1_won_toss_and_fielded" in row:
        row["team1_won_toss_and_fielded"] = float(toss_winner_is_team1)
    if "team2_won_toss_and_fielded" in row:
        row["team2_won_toss_and_fielded"] = float(toss_winner_is_team2)

    return pd.DataFrame([[row[column] for column in feature_columns]], columns=feature_columns)


def clamp(value: float, lower: float, upper: float) -> float:
    """Clamp a numeric value into a closed interval."""

    return max(lower, min(upper, value))


def estimate_venue_par_score(venue_reference: pd.Series | None) -> float:
    """Estimate a venue baseline from the latest comparable matchup row."""

    if venue_reference is None:
        return 168.0

    score_candidates = []
    for column in ("team1_batting_runs", "team2_batting_runs"):
        value = venue_reference.get(column)
        if pd.notna(value):
            score_candidates.append(float(value))
    if not score_candidates:
        return 168.0
    return sum(score_candidates) / len(score_candidates)


def estimate_team_score(
    batting_row: pd.Series,
    bowling_row: pd.Series,
    venue_reference: pd.Series | None,
    batting_key_player: str,
    is_chasing: bool,
    chase_target: int | None = None,
) -> tuple[int, int]:
    """Estimate a realistic T20 score and wickets using historical strengths."""

    venue_par = estimate_venue_par_score(venue_reference)
    batting_form_runs = float(batting_row.get("batting_run_rate_mean_before_match", 8.2)) * 20.0
    batting_recent_runs = float(batting_row.get("batting_run_rate_last_5", batting_row.get("batting_run_rate_last_3", 8.2))) * 20.0
    opponent_conceded_runs = float(
        bowling_row.get("bowling_run_rate_conceded_mean_before_match", 8.3)
    ) * 20.0

    powerplay_edge = (
        float(batting_row.get("batting_powerplay_run_rate_mean_before_match", 8.0))
        - float(bowling_row.get("bowling_powerplay_run_rate_conceded_mean_before_match", 8.0))
    ) * 3.5
    death_edge = (
        float(batting_row.get("batting_death_over_run_rate_mean_before_match", 9.5))
        - float(bowling_row.get("bowling_death_over_run_rate_conceded_mean_before_match", 9.5))
    ) * 4.0
    boundary_edge = (
        float(batting_row.get("batting_boundary_percentage_mean_before_match", 0.19))
        - float(bowling_row.get("bowling_boundary_percentage_conceded_mean_before_match", 0.19))
    ) * 140.0
    dot_ball_drag = (
        float(bowling_row.get("bowling_dot_ball_percentage_mean_before_match", 0.34))
        - float(batting_row.get("batting_dot_ball_percentage", 0.34))
    ) * 55.0
    key_player_boost = 4.0 if batting_key_player.strip() else 0.0
    chase_adjustment = 6.0 if is_chasing else 0.0

    projected = (
        0.28 * venue_par
        + 0.26 * batting_form_runs
        + 0.18 * batting_recent_runs
        + 0.20 * opponent_conceded_runs
        + powerplay_edge
        + death_edge
        + boundary_edge
        - dot_ball_drag
        + key_player_boost
        + chase_adjustment
    )

    if is_chasing and chase_target is not None:
        projected = 0.55 * projected + 0.45 * chase_target

    opponent_wicket_pressure = float(bowling_row.get("bowling_wicket_rate_mean_before_match", 0.05))
    projected_wickets = (
        0.45 * float(batting_row.get("batting_wickets_lost", 6.0))
        + opponent_wicket_pressure * 55.0
    )

    score = int(round(clamp(projected, 135.0, 215.0)))
    wickets = int(round(clamp(projected_wickets, 4.0, 9.0)))
    return score, wickets


def derive_confidence(probability: float) -> str:
    """Map raw win probability into a simple confidence band."""

    edge = abs(probability - 0.5)
    if edge >= 0.18:
        return "high"
    if edge >= 0.09:
        return "medium"
    return "low"


def predict_match_outcome(request: PredictionRequest) -> dict[str, Any]:
    """Produce the backend response payload for a match simulation request."""

    payload = load_saved_model()
    team_history = load_team_history()
    match_dataset = load_match_dataset()
    team_lookup = build_team_lookup(team_history)

    team1_name = resolve_team_name(request.team1, team_lookup)
    team2_name = resolve_team_name(request.team2, team_lookup)
    toss_winner = resolve_team_name(request.toss_winner, team_lookup)
    if team1_name == team2_name:
        raise ValueError("Please choose two different teams.")
    if toss_winner not in {team1_name, team2_name}:
        raise ValueError("Toss winner must be one of the selected teams.")

    feature_frame = build_prediction_feature_row(
        team_history=team_history,
        match_dataset=match_dataset,
        team1_name=team1_name,
        team2_name=team2_name,
        toss_winner=toss_winner,
        feature_columns=payload["feature_columns"],
    )
    scaler_mean = pd.Series(payload["scaler_mean"], dtype=float)
    scaler_std = pd.Series(payload["scaler_std"], dtype=float)
    scaled_features = transform_with_scaler(feature_frame, scaler_mean, scaler_std)
    probability_team1 = predict_probability_from_payload(payload, scaled_features.iloc[0].tolist())
    probability_team2 = 1.0 - probability_team1
    predicted_winner = team1_name if probability_team1 >= 0.5 else team2_name

    team1_latest = latest_team_row(team_history, team1_name)
    team2_latest = latest_team_row(team_history, team2_name)
    venue_reference = latest_matchup_row(match_dataset, team1_name, team2_name)
    team1_is_chasing = toss_winner == team1_name
    team2_is_chasing = toss_winner == team2_name

    if team1_is_chasing:
        team2_score, team2_wickets = estimate_team_score(
            batting_row=team2_latest,
            bowling_row=team1_latest,
            venue_reference=venue_reference,
            batting_key_player=request.key_player_team2,
            is_chasing=False,
        )
        team1_score, team1_wickets = estimate_team_score(
            batting_row=team1_latest,
            bowling_row=team2_latest,
            venue_reference=venue_reference,
            batting_key_player=request.key_player_team1,
            is_chasing=True,
            chase_target=team2_score + 1,
        )
    else:
        team1_score, team1_wickets = estimate_team_score(
            batting_row=team1_latest,
            bowling_row=team2_latest,
            venue_reference=venue_reference,
            batting_key_player=request.key_player_team1,
            is_chasing=False,
        )
        team2_score, team2_wickets = estimate_team_score(
            batting_row=team2_latest,
            bowling_row=team1_latest,
            venue_reference=venue_reference,
            batting_key_player=request.key_player_team2,
            is_chasing=True,
            chase_target=team1_score + 1,
        )

    win_gap = int(round(clamp(abs(probability_team1 - 0.5) * 60.0, 4.0, 18.0)))
    if predicted_winner == team1_name:
        if team1_is_chasing:
            team1_score = max(team1_score, team2_score + 1)
            team1_score = min(215, team2_score + win_gap)
        else:
            team2_score = min(team2_score, team1_score - win_gap)
    else:
        if team2_is_chasing:
            team2_score = max(team2_score, team1_score + 1)
            team2_score = min(215, team1_score + win_gap)
        else:
            team1_score = min(team1_score, team2_score - win_gap)

    team1_score = int(clamp(team1_score, 125.0, 215.0))
    team2_score = int(clamp(team2_score, 125.0, 215.0))

    winner_key = "team1" if predicted_winner == team1_name else "team2"
    probability = probability_team1 if winner_key == "team1" else probability_team2
    ai_agrees = (
        (request.user_predicted_score_team1 > request.user_predicted_score_team2 and winner_key == "team1")
        or (request.user_predicted_score_team2 > request.user_predicted_score_team1 and winner_key == "team2")
    )

    return {
        "team1": team1_name,
        "team2": team2_name,
        "winner": winner_key,
        "winner_name": predicted_winner,
        "probability": round(float(probability), 3),
        "team1_win_probability": round(float(probability_team1), 3),
        "team2_win_probability": round(float(probability_team2), 3),
        "ai_predicted_score_team1": team1_score,
        "ai_predicted_score_team2": team2_score,
        "ai_predicted_scorecard_team1": f"{team1_score}/{team1_wickets}",
        "ai_predicted_scorecard_team2": f"{team2_score}/{team2_wickets}",
        "user_predicted_score_team1": int(request.user_predicted_score_team1),
        "user_predicted_score_team2": int(request.user_predicted_score_team2),
        "confidence": derive_confidence(probability),
        "key_player_team1": request.key_player_team1,
        "key_player_team2": request.key_player_team2,
        "toss_winner": toss_winner,
        "ai_agrees_with_user": ai_agrees,
    }


def interactive_predict() -> None:
    """Ask the user for two teams and print the predicted winner."""

    payload = load_saved_model()
    team_history = load_team_history()
    match_dataset = load_match_dataset()
    team_lookup = build_team_lookup(team_history)
    available_teams = sorted(team_lookup.values())

    print("Available teams:")
    print(", ".join(available_teams))

    team1_input = input("Enter team 1: ").strip()
    team2_input = input("Enter team 2: ").strip()
    team1_name = resolve_team_name(team1_input, team_lookup)
    team2_name = resolve_team_name(team2_input, team_lookup)

    if team1_name == team2_name:
        raise ValueError("Please choose two different teams.")

    toss_input = input(f"Enter toss winner ({team1_name}/{team2_name}): ").strip()
    toss_winner = resolve_team_name(toss_input or team1_name, team_lookup)
    if toss_winner not in {team1_name, team2_name}:
        raise ValueError("Toss winner must be one of the selected teams.")

    feature_frame = build_prediction_feature_row(
        team_history=team_history,
        match_dataset=match_dataset,
        team1_name=team1_name,
        team2_name=team2_name,
        toss_winner=toss_winner,
        feature_columns=payload["feature_columns"],
    )
    scaler_mean = pd.Series(payload["scaler_mean"], dtype=float)
    scaler_std = pd.Series(payload["scaler_std"], dtype=float)
    scaled_features = transform_with_scaler(feature_frame, scaler_mean, scaler_std)
    probability_team1 = predict_probability_from_payload(
        payload,
        scaled_features.iloc[0].tolist(),
    )
    probability_team2 = 1.0 - probability_team1
    predicted_winner = team1_name if probability_team1 >= 0.5 else team2_name

    print()
    print(f"Toss winner: {toss_winner}")
    print(f"Prediction: {predicted_winner}")
    print(f"{team1_name} win probability: {probability_team1:.3f}")
    print(f"{team2_name} win probability: {probability_team2:.3f}")


def main() -> None:
    """Run interactive prediction by default, with optional training mode."""

    mode = os.getenv("MICROGRAD_MODE", "predict").strip().lower()
    if mode == "train":
        epochs = int(os.getenv("MICROGRAD_EPOCHS", "1"))
        learning_rate = float(os.getenv("MICROGRAD_LR", "0.005"))
        batch_size = int(os.getenv("MICROGRAD_BATCH", "16"))
        seed = int(os.getenv("MICROGRAD_SEED", "42"))
        summary = train_model(
            epochs=epochs,
            learning_rate=learning_rate,
            batch_size=batch_size,
            seed=seed,
        )
        print(summary)
        return

    interactive_predict()


if __name__ == "__main__":
    main()
