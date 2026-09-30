"""Shared settings for the Sharko Australia data pipeline."""
import os
from datetime import date

# Study area: a box around Australia (lon 110–160 E, lat 46–9 S)
LON_MIN, LON_MAX = 110.0, 160.0
LAT_MIN, LAT_MAX = -46.0, -9.0
# WKT polygon, counter-clockwise (required by GBIF)
BBOX_WKT = (f"POLYGON(({LON_MIN} {LAT_MIN},{LON_MAX} {LAT_MIN},{LON_MAX} {LAT_MAX},"
            f"{LON_MIN} {LAT_MAX},{LON_MIN} {LAT_MIN}))")

# Time range
START_DATE = "2020-01-01"
END_DATE = date.today().isoformat()

# Folders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
OCEAN_DIR = os.path.join(DATA_DIR, "ocean")
for d in (DATA_DIR, RAW_DIR, OCEAN_DIR):
    os.makedirs(d, exist_ok=True)

# All shark orders (sharks only, no rays/skates)
SHARK_ORDERS = [
    "Carcharhiniformes", "Lamniformes", "Orectolobiformes", "Heterodontiformes",
    "Hexanchiformes", "Squaliformes", "Squatiniformes", "Pristiophoriformes",
    "Echinorhiniformes",
]

# OBIS/WoRMS taxon id for Selachii (all sharks)
OBIS_SHARK_TAXON_ID = 368408
