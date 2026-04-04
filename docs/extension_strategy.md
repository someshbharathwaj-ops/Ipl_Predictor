# Extending Beyond 2016

The repository snapshot bundled in `backend/data` ends at the 2016 IPL season, so current-season prediction needs a fresher ingestion source.

## Recommended options

1. Use Cricsheet JSON downloads as the primary historical source.
2. Use a live cricket API for near-real-time fixture, toss, squad, and result updates.
3. Rebuild the same cleaned tables from those sources before running the feature pipeline.

## Why this is the best path

- the current CSV dump is static and cannot cover IPL 2024 or IPL 2025
- the pipeline already uses rolling historical windows, so the same features can extend naturally once newer matches are ingested
- if live data access is unavailable, the existing rolling features still provide a reasonable proxy for recent form inside the 2008 to 2016 window
