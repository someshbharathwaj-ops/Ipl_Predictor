"""Pipeline entrypoint for producing IPL training datasets."""

from __future__ import annotations

from dataset_builder import build_feature_manifest, build_match_dataset, extract_model_matrix
from dataset_builder import build_dataset_coverage_summary
from features import build_innings_stats, build_team_history_frame
from preprocessing import (
    build_api_ingestion_plan,
    build_data_audit,
    build_expansion_status,
    clean_tables,
    ensure_output_dir,
    load_raw_tables,
    serialize_validation_issues,
    standardize_ball_export,
    standardize_match_export,
    validate_tables,
    write_json_payload,
)


def main() -> None:
    """Build the IPL feature pipeline in memory."""

    tables = load_raw_tables()
    cleaned = clean_tables(tables)
    output_dir = ensure_output_dir()
    matches_2008_2025 = standardize_match_export(cleaned["matches"])
    ball_by_ball_2008_2025 = standardize_ball_export(cleaned["balls"])
    audit = build_data_audit(cleaned)
    validation_issues = validate_tables(cleaned)
    expansion_status = build_expansion_status(cleaned)
    innings_stats = build_innings_stats(cleaned["balls"])
    team_history = build_team_history_frame(cleaned["matches"], innings_stats)
    match_dataset = build_match_dataset(team_history)
    features, target = extract_model_matrix(match_dataset)
    feature_manifest = build_feature_manifest(match_dataset, features)
    coverage_summary = build_dataset_coverage_summary(
        matches_2008_2025,
        ball_by_ball_2008_2025,
    )
    api_ingestion_plan = build_api_ingestion_plan()

    ball_by_ball_2008_2025.to_csv(output_dir / "ball_by_ball_2008_2025.csv", index=False)
    matches_2008_2025.to_csv(output_dir / "matches_2008_2025.csv", index=False)
    innings_stats.to_csv(output_dir / "innings_stats.csv", index=False)
    team_history.to_csv(output_dir / "team_history_features.csv", index=False)
    match_dataset.to_csv(output_dir / "match_dataset.csv", index=False)
    features.assign(target=target).to_csv(output_dir / "micrograd_model_input.csv", index=False)
    write_json_payload(feature_manifest, output_dir / "feature_manifest.json")
    write_json_payload(coverage_summary, output_dir / "dataset_coverage.json")
    write_json_payload(expansion_status, output_dir / "expansion_status.json")
    write_json_payload(api_ingestion_plan, output_dir / "api_ingestion_plan.json")
    write_json_payload(audit, output_dir / "data_audit.json")
    write_json_payload(
        serialize_validation_issues(validation_issues),
        output_dir / "validation_report.json",
    )

    print(
        {
            "output_dir": str(output_dir),
            "ball_export": ball_by_ball_2008_2025.shape,
            "match_export": matches_2008_2025.shape,
            "innings_stats": innings_stats.shape,
            "team_history": team_history.shape,
            "match_dataset": match_dataset.shape,
            "model_features": features.shape,
            "target_rows": int(target.shape[0]),
        }
    )


if __name__ == "__main__":
    main()
