# Sharko Australia: future-prediction backtest

Trained on 2020-2024, tested on 2025-2026 real sightings, using only information available at the end of 2024. AUC: 0.5 = random, 0.7 = fair, 0.8 = good, 0.9 = excellent. Caught = share of real sightings inside the predicted habitat; false alarm = share of background points flagged as habitat.

## tiger (224 test sightings)

| method | AUC | caught | false alarm |
|---|---|---|---|
| Real conditions (upper bound) | 0.978 | 98% | 7% |
| Outlook 7 days ahead | 0.966 | 89% | 8% |
| Outlook 14 days ahead | 0.970 | 92% | 8% |
| Outlook 30 days ahead | 0.973 | 95% | 8% |
| Outlook 60 days ahead | 0.979 | 99% | 8% |
| Outlook 90 days ahead | 0.980 | 100% | 8% |
| Typical conditions (months/years ahead) | 0.981 | 99% | 8% |
| Place + season only (baseline) | 0.963 | 98% | 9% |

## bull (200 test sightings)

| method | AUC | caught | false alarm |
|---|---|---|---|
| Real conditions (upper bound) | 0.975 | 98% | 11% |
| Outlook 7 days ahead | 0.972 | 99% | 9% |
| Outlook 14 days ahead | 0.971 | 99% | 10% |
| Outlook 30 days ahead | 0.973 | 99% | 10% |
| Outlook 60 days ahead | 0.976 | 99% | 10% |
| Outlook 90 days ahead | 0.977 | 99% | 10% |
| Typical conditions (months/years ahead) | 0.977 | 100% | 10% |
| Place + season only (baseline) | 0.966 | 99% | 12% |

## white (23 test sightings)

| method | AUC | caught | false alarm |
|---|---|---|---|
| Real conditions (upper bound) | 0.934 | 91% | 19% |
| Outlook 7 days ahead | 0.918 | 83% | 20% |
| Outlook 14 days ahead | 0.915 | 87% | 21% |
| Outlook 30 days ahead | 0.927 | 91% | 21% |
| Outlook 60 days ahead | 0.931 | 87% | 22% |
| Outlook 90 days ahead | 0.922 | 91% | 22% |
| Typical conditions (months/years ahead) | 0.925 | 91% | 22% |
| Place + season only (baseline) | 0.852 | 83% | 43% |

## any (4476 test sightings)

| method | AUC | caught | false alarm |
|---|---|---|---|
| Real conditions (upper bound) | 0.941 | 95% | 17% |
| Outlook 7 days ahead | 0.941 | 93% | 13% |
| Outlook 14 days ahead | 0.943 | 94% | 13% |
| Outlook 30 days ahead | 0.947 | 95% | 13% |
| Outlook 60 days ahead | 0.948 | 95% | 14% |
| Outlook 90 days ahead | 0.949 | 95% | 14% |
| Typical conditions (months/years ahead) | 0.949 | 95% | 14% |
| Place + season only (baseline) | 0.937 | 92% | 10% |
