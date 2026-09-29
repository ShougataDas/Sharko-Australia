# Sharko Australia: model test report

Integrity = FAIL if broken. Biology / new region = WARN if the model disagrees with known biology or predicts an unseen region poorly (AUC < 0.7).

## any

| group | test | result | detail |
|---|---|---|---|
| integrity | bundle contents | PASS | RandomForest, trained 2026-09-28T02:01:47 |
| integrity | feature list & order | PASS | matches features.py |
| integrity | outputs are probabilities | PASS | range 0.000 to 0.988 |
| integrity | deterministic | PASS | same input -> same output |
| integrity | not constant | PASS | std of predictions 0.378 |
| integrity | threshold valid | PASS | 0.390 |
| integrity | sightings score above background | PASS | mean 0.83 vs 0.17 |
| biology | typical sighting spot | PASS | suitability 0.89 (threshold 0.39) at median conditions: 23.1°C, 5 m deep, 1.6 km offshore |
| biology | deep open ocean less suitable | PASS | 4000 m deep, 300 km offshore -> 0.10 vs 0.89 |
| new region | West (WA) | PASS | AUC 0.869 on 984 sightings never seen in training; 65% of them inside predicted habitat |
| new region | North (NT, Gulf, Torres Strait) | PASS | AUC 0.776 on 4164 sightings never seen in training; 58% of them inside predicted habitat |
| new region | South (SA, Vic, Tas, Bass Strait) | PASS | AUC 0.948 on 1578 sightings never seen in training; 98% of them inside predicted habitat |
| new region | East (Qld, NSW) | PASS | AUC 0.860 on 9814 sightings never seen in training; 81% of them inside predicted habitat |
| new region | average over regions | PASS | AUC 0.863 |
| new records | sightings after training data | INFO | 0 sightings after 2026-09-07 - re-run steps 1-4 later to get more |

## bull

| group | test | result | detail |
|---|---|---|---|
| integrity | bundle contents | PASS | LightGBM, trained 2026-09-28T01:54:43 |
| integrity | feature list & order | PASS | matches features.py |
| integrity | outputs are probabilities | PASS | range 0.000 to 0.980 |
| integrity | deterministic | PASS | same input -> same output |
| integrity | not constant | PASS | std of predictions 0.380 |
| integrity | threshold valid | PASS | 0.233 |
| integrity | sightings score above background | PASS | mean 0.92 vs 0.08 |
| biology | typical sighting spot | PASS | suitability 0.95 (threshold 0.23) at median conditions: 25.2°C, 3 m deep, 1.6 km offshore |
| biology | deep open ocean less suitable | PASS | 4000 m deep, 300 km offshore -> 0.00 vs 0.95 |
| biology | bull sharks prefer warm (27°C) over cold (15°C) water | PASS | 0.95 vs 0.07 |
| new region | West (WA) | INFO | only 5 sightings there - not tested |
| new region | North (NT, Gulf, Torres Strait) | PASS | AUC 0.958 on 367 sightings never seen in training; 92% of them inside predicted habitat |
| new region | South (SA, Vic, Tas, Bass Strait) | INFO | only 1 sightings there - not tested |
| new region | East (Qld, NSW) | PASS | AUC 0.868 on 990 sightings never seen in training; 55% of them inside predicted habitat |
| new region | average over regions | PASS | AUC 0.913 |
| new records | sightings after training data | INFO | 0 sightings after 2026-09-07 - re-run steps 1-4 later to get more |

## tiger

| group | test | result | detail |
|---|---|---|---|
| integrity | bundle contents | PASS | LightGBM, trained 2026-09-28T01:51:38 |
| integrity | feature list & order | PASS | matches features.py |
| integrity | outputs are probabilities | PASS | range 0.000 to 0.977 |
| integrity | deterministic | PASS | same input -> same output |
| integrity | not constant | PASS | std of predictions 0.357 |
| integrity | threshold valid | PASS | 0.519 |
| integrity | sightings score above background | PASS | mean 0.91 vs 0.09 |
| biology | typical sighting spot | PASS | suitability 0.95 (threshold 0.52) at median conditions: 25.7°C, 4 m deep, 1.6 km offshore |
| biology | deep open ocean less suitable | PASS | 4000 m deep, 300 km offshore -> 0.00 vs 0.95 |
| biology | tiger sharks prefer warm (27°C) over cold (15°C) water | PASS | 0.95 vs 0.64 |
| new region | West (WA) | PASS | AUC 0.942 on 173 sightings never seen in training; 49% of them inside predicted habitat |
| new region | North (NT, Gulf, Torres Strait) | PASS | AUC 0.932 on 411 sightings never seen in training; 81% of them inside predicted habitat |
| new region | South (SA, Vic, Tas, Bass Strait) | INFO | only 0 sightings there - not tested |
| new region | East (Qld, NSW) | PASS | AUC 0.922 on 920 sightings never seen in training; 78% of them inside predicted habitat |
| new region | average over regions | PASS | AUC 0.932 |
| new records | sightings after training data | INFO | 0 sightings after 2026-09-07 - re-run steps 1-4 later to get more |

## white

| group | test | result | detail |
|---|---|---|---|
| integrity | bundle contents | PASS | LightGBM, trained 2026-09-28T01:56:57 |
| integrity | feature list & order | PASS | matches features.py |
| integrity | outputs are probabilities | PASS | range 0.001 to 0.976 |
| integrity | deterministic | PASS | same input -> same output |
| integrity | not constant | PASS | std of predictions 0.273 |
| integrity | threshold valid | PASS | 0.200 |
| integrity | sightings score above background | PASS | mean 0.91 vs 0.09 |
| biology | typical sighting spot | PASS | suitability 0.95 (threshold 0.20) at median conditions: 19.9°C, 9 m deep, 6.2 km offshore |
| biology | deep open ocean less suitable | PASS | 4000 m deep, 300 km offshore -> 0.01 vs 0.95 |
| biology | white sharks prefer cool (18°C) over tropical (29°C) water | PASS | 0.95 vs 0.56 |
| new region | West (WA) | INFO | only 1 sightings there - not tested |
| new region | North (NT, Gulf, Torres Strait) | INFO | only 0 sightings there - not tested |
| new region | South (SA, Vic, Tas, Bass Strait) | PASS | AUC 0.856 on 115 sightings never seen in training; 89% of them inside predicted habitat |
| new region | East (Qld, NSW) | PASS | AUC 0.753 on 662 sightings never seen in training; 15% of them inside predicted habitat |
| new region | average over regions | PASS | AUC 0.804 |
| new records | sightings after training data | INFO | 0 sightings after 2026-09-07 - re-run steps 1-4 later to get more |
