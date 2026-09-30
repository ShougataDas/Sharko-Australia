# Sharko Australia: model comparison

Spatial AUC = tested on 2x2 degree regions the model never saw. Future AUC = trained on 2020-2024, tested on 2025-2026. AUC 0.5 = random, 0.7 = fair, 0.8 = good, 0.9 = excellent.

| species | model | spatial_auc | spatial_pr_auc | spatial_tss | future_auc | n_presences |
|---|---|---|---|---|---|---|
| Galeocerdo cuvier (tiger) | GLM | 0.768 | 0.236 | 0.616 | 0.926 | 1504 |
| Galeocerdo cuvier (tiger) | RandomForest | 0.863 | 0.552 | 0.748 | 0.979 | 1504 |
| Galeocerdo cuvier (tiger) | **LightGBM** (best) | 0.886 | 0.561 | 0.766 | 0.978 | 1504 |
| Carcharhinus leucas (bull) | GLM | 0.864 | 0.383 | 0.649 | 0.929 | 1363 |
| Carcharhinus leucas (bull) | RandomForest | 0.930 | 0.594 | 0.821 | 0.977 | 1363 |
| Carcharhinus leucas (bull) | **LightGBM** (best) | 0.932 | 0.581 | 0.804 | 0.975 | 1363 |
| Carcharodon carcharias (white) | GLM | 0.757 | 0.135 | 0.619 | 0.927 | 778 |
| Carcharodon carcharias (white) | RandomForest | 0.796 | 0.172 | 0.389 | 0.949 | 778 |
| Carcharodon carcharias (white) | **LightGBM** (best) | 0.814 | 0.251 | 0.543 | 0.934 | 778 |
| All sharks | GLM | 0.779 | 0.735 | 0.400 | 0.814 | 16540 |
| All sharks | **RandomForest** (best) | 0.899 | 0.864 | 0.694 | 0.944 | 16540 |
| All sharks | LightGBM | 0.898 | 0.867 | 0.689 | 0.941 | 16540 |
