"""Load puzzle CSV data and compute expected outputs."""

import csv
from pathlib import Path
from typing import List, Dict, Any

_DATA_DIR = Path(__file__).resolve().parent / "data"


def load_csv_data(filename: str) -> List[Dict[str, Any]]:
    """Read a CSV file from the data directory into a list of dicts.

    The ``id`` column is automatically converted to int.
    """
    filepath = _DATA_DIR / filename
    rows: List[Dict[str, Any]] = []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "id" in row:
                row["id"] = int(row["id"])
            rows.append(row)
    return rows


def compute_expected_output_group_fruits(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort fruit rows by type (then by id) to produce the expected output."""
    return sorted(data, key=lambda r: (r["type"], r["id"]))


# ------------------------------------------------------------------
# Module-level cache: loaded once at import time
# ------------------------------------------------------------------
_group_fruits_data: List[Dict[str, Any]] = load_csv_data("group_fruits.csv")
_group_fruits_expected: List[Dict[str, Any]] = compute_expected_output_group_fruits(_group_fruits_data)


def get_group_fruits_data() -> List[Dict[str, Any]]:
    return _group_fruits_data


def get_group_fruits_expected() -> List[Dict[str, Any]]:
    return _group_fruits_expected
