# Sharko Australia: pipeline test report

Run 2026-09-30 03:23 (full). PASS 28, WARN 0, SKIP 0, FAIL 0

| group | check | result | detail |
|---|---|---|---|
| environment | required packages import | PASS | all present (2.2s) |
| data | raw shark downloads present | PASS | obis 38,629, gbif 40,022, qld 4,815 (0.3s) |
| data | merged shark records are clean | PASS | 29,230 records, 137 species (0.1s) |
| data | daily model dataset is complete and balanced | PASS | 33,341 rows, 50% sightings (0.1s) |
| data | seasonal dataset matches the daily one row for row | PASS | same points, typical ocean inputs (0.2s) |
| data | bathymetry depth / distance ranges | PASS | depth to 7248 m, ocean 62% (0.4s) |
| features | satellite archive has no missing days | PASS | sst to 2026-09-26, ssh to 2026-09-27, chl to 2026-09-26 (0.4s) |
| features | re-computed inputs equal the training values | PASS | 200 random rows identical (max diff 6.2e-05) (16.0s) |
| climatology | typical conditions are physically realistic | PASS | years 2020-2026, 114,633 ocean cells x 52 weeks (3.4s) |
| climatology | seasons and latitudes make sense | PASS | Sydney Jan 23.0 C, Hobart Jan/Jul 16.8/12.7 C, Cairns Jan 29.3 C (0.0s) |
| climatology | unusual conditions fade over time | PASS | sst anomaly kept after 1 wk / 1 mo / 3 mo: [0.79, 0.43, 0.16] (0.0s) |
| climatology | backtest climatology contains no 2025-26 data | PASS | 2020-2024 (3.0s) |
| climatology | seasonal dataset = climatology at each point | PASS | 500 rows match (max diff 3.6e-15) (0.0s) |
| forecast | forecast covers the coming days | PASS | 2026-09-23 -> 2026-10-08, 8 days ahead (5.0s) |
| forecast | bias-corrected forecast agrees with satellite | PASS | 2026-09-26: SST error 0.27 C (typical-conditions guess: 0.62 C) (1.4s) |
| models | daily and seasonal models load and output probabilities | PASS | daily: any, bull, tiger, white; seasonal: any, bull, tiger, white (0.1s) |
| models | models beat 0.7 AUC on unseen regions | PASS | daily/any 0.90, daily/bull 0.93, daily/tiger 0.89, daily/white 0.81, seasonal/any 0.90, seasonal/bull 0.94, seasonal/tiger 0.88, seasonal/white 0.82 (0.0s) |
| predictor | right mode for each kind of date | PASS | 2030-06-01->typical, 2025-01-15->observed, 2026-10-08->forecast, 2026-11-07->outlook, 2027-04-26->typical (0.0s) |
| predictor | point prediction has all fields and valid numbers | PASS | 4 species, mode typical (0.1s) |
| predictor | land and out-of-area positions return an error | PASS | Alice Springs and Gulf of Thailand rejected (0.0s) |
| predictor | same question, same answer | PASS | identical (0.1s) |
| predictor | predictor == models on training rows (observed mode) | PASS | 25 sightings: inputs max diff 1.4e-05, prediction max diff 1.2e-03 (41.4s) |
| predictor | outlook starts at the last known ocean and fades to typical | PASS | day +1 differs 0.03 C from forecast; day +89 within 0.11 C of typical (0.0s) |
| predictor | future predictions follow known biology | PASS | white Jul NSW 0.93 > Cairns 0.00; tiger Jan Cairns 0.90 > Tas 0.00; bull Jan Cairns 0.84 > Tas 0.00 (0.1s) |
| predictor | no habitat predicted far outside a species' recorded range | PASS | 497 Gulf/Arafura cells: white shark likelihood 0 (outside recorded range) (0.0s) |
| predictor | whole-Australia map for a future date | PASS | 114,633 cells in 8s; habitat share any 3.0%, bull 1.3%, tiger 0.9%, white 1.4% (7.5s) |
| predictor | single prediction is fast | PASS | 35 ms per future prediction (0.1s) |
| backtest | honest future accuracy (trained to 2024, tested on 2025-26) | PASS | future AUC (typical conditions): tiger 0.98, bull 0.98, white 0.93, any 0.95 (0.0s) |
