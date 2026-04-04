# IPL Dataset Pipeline

## Objective

Convert the legacy IPL CSV dump into a leakage-safe training table for predicting match winners with a neural network built from scratch.

## Cleaning rules

- standardize every table to snake_case
- rename typoed dismissal columns into consistent names
- derive `total_runs = batsman_scored + extra_runs`
- derive `is_wicket` from `player_dismissal_id`
- derive `is_legal_delivery` by excluding wides and no-balls
- drop the noisy player column `unnamed_7`

## Validation rules

- reject negative total runs
- flag overs outside `1..20`
- flag balls outside `1..9`
- flag innings with more than 120 legal deliveries
- keep no-result matches out of the final target dataset

## Feature groups

- batting form: run rate, phase run rates, boundary percentage
- bowling form: conceded run rate, wicket rate, dot-ball percentage
- team form: cumulative win rate, last five win rate, short rolling trends
- context: venue familiarity, toss state, head-to-head history
- matchup deltas: team1 minus team2 for key pre-match strengths

## Final dataset

- one row per decided IPL match
- 574 labeled matches from seasons 2008 through 2016
- numeric micrograd input exported separately from the wider analysis dataset
