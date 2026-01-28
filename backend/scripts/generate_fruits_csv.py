"""Generate the group_fruits.csv data file with ~10,000 rows."""

import csv
import random
from pathlib import Path

random.seed(42)

FRUITS = {
    "apple":  {"colors": ["red", "green", "yellow"], "weight": 40},
    "banana": {"colors": ["yellow", "green"],        "weight": 35},
    "cherry": {"colors": ["red", "purple"],           "weight": 25},
}

# Build weighted choices
fruit_types = []
fruit_weights = []
for fruit, info in FRUITS.items():
    fruit_types.append(fruit)
    fruit_weights.append(info["weight"])

NUM_ROWS = 10_000

output_path = Path(__file__).resolve().parent.parent / "app" / "puzzles" / "data" / "group_fruits.csv"

with open(output_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "type", "color"])
    for i in range(1, NUM_ROWS + 1):
        fruit = random.choices(fruit_types, weights=fruit_weights, k=1)[0]
        color = random.choice(FRUITS[fruit]["colors"])
        writer.writerow([i, fruit, color])

print(f"Generated {NUM_ROWS} rows -> {output_path}")
