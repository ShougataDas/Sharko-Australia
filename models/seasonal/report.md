# Sharko Australia: model comparison

Spatial AUC = tested on 2x2 degree regions the model never saw. Future AUC = trained on 2020-2024, tested on 2025-2026. AUC 0.5 = random, 0.7 = fair, 0.8 = good, 0.9 = excellent.

| species | model | spatial_auc | spatial_pr_auc | spatial_tss | future_auc | n_presences |
|---|---|---|---|---|---|---|
| Galeocerdo cuvier (tiger) - seasonal | GLM | 0.806 | 0.250 | 0.629 | 0.932 | 1504 |
| Galeocerdo cuvier (tiger) - seasonal | RandomForest | 0.851 | 0.509 | 0.732 | 0.983 | 1504 |
| Galeocerdo cuvier (tiger) - seasonal | **LightGBM** (best) | 0.877 | 0.535 | 0.744 | 0.981 | 1504 |
| Carcharhinus leucas (bull) - seasonal | GLM | 0.843 | 0.323 | 0.628 | 0.921 | 1363 |
| Carcharhinus leucas (bull) - seasonal | RandomForest | 0.933 | 0.597 | 0.838 | 0.980 | 1363 |
| Carcharhinus leucas (bull) - seasonal | **LightGBM** (best) | 0.936 | 0.589 | 0.823 | 0.977 | 1363 |
| Carcharodon carcharias (white) - seasonal | GLM | 0.722 | 0.078 | 0.489 | 0.876 | 778 |
| Carcharodon carcharias (white) - seasonal | RandomForest | 0.746 | 0.123 | 0.259 | 0.933 | 778 |
| Carcharodon carcharias (white) - seasonal | **LightGBM** (best) | 0.818 | 0.311 | 0.595 | 0.922 | 778 |
| All sharks - seasonal | GLM | 0.802 | 0.765 | 0.453 | 0.815 | 16540 |
| All sharks - seasonal | RandomForest | 0.903 | 0.876 | 0.701 | 0.952 | 16540 |
| All sharks - seasonal | **LightGBM** (best) | 0.904 | 0.876 | 0.698 | 0.949 | 16540 |
