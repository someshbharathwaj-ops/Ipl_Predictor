"""Pipeline entrypoint for producing IPL training datasets."""

from __future__ import annotations

from dataset_builder import build_match_dataset, extract_model_matrix
from features import build_innings_stats, build_team_history_frame
from preprocessing import clean_tables, load_raw_tables


def main() -> None:
    """Build the IPL feature pipeline in memory."""

    tables = load_raw_tables()
    cleaned = clean_tables(tables)
    innings_stats = build_innings_stats(cleaned["balls"])
    team_history = build_team_history_frame(cleaned["matches"], innings_stats)
    match_dataset = build_match_dataset(team_history)
    features, target = extract_model_matrix(match_dataset)

    print(
        {
            "innings_stats": innings_stats.shape,
            "team_history": team_history.shape,
            "match_dataset": match_dataset.shape,
            "model_features": features.shape,
            "target_rows": int(target.shape[0]),
        }
    )


if __name__ == "__main__":
    main()
