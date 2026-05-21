"""Analyze sweep results: win rates and grouped statistics.

Winner rule:
    attacker wins if final_damage_ratio >= threshold
    defender wins otherwise

The threshold is intentionally configurable because "winning" is a modeling
choice. A threshold of 1.5 means the attacker wins if the final shortest path
is at least 50% longer than the initial shortest path.
"""

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


RESULTS_DIR = Path(__file__).parent / "results"

NUMERIC_FIELDS = {
    "seed",
    "nodes",
    "edges",
    "actual_density",
    "density_parameter",
    "attack_budget",
    "defense_budget",
    "attack_multiplier",
    "rounds_requested",
    "rounds_played",
    "initial_length",
    "final_length",
    "total_damage",
    "mean_round_damage",
    "max_round_damage",
    "mean_damage_ratio",
    "final_damage_ratio",
    "total_attacked_edges",
    "unique_attacked_edges",
    "mean_protected_edges",
    "runtime_seconds",
    "edge_connectivity",
    "shortest_path_count",
    "shortest_path_edge_count",
    "bridge_count",
    "betweenness_concentration",
    "alternative_path_ratio",
}


def load_rows(path):
    """Load result rows and convert numeric fields."""
    rows = []
    with Path(path).open() as file:
        for row in csv.DictReader(file):
            for field in NUMERIC_FIELDS:
                row[field] = float(row[field])
            rows.append(row)
    return rows


def add_winners(rows, threshold):
    """Add winner labels to each row."""
    for row in rows:
        row["winner"] = (
            "Attacker"
            if row["final_damage_ratio"] >= threshold
            else "Defender"
        )
    return rows


def summarize_by(rows, group_fields):
    """Aggregate win rates and damage metrics for chosen group fields."""
    groups = defaultdict(list)
    for row in rows:
        key = tuple(row[field] for field in group_fields)
        groups[key].append(row)

    summary = []
    for key, group in sorted(groups.items()):
        wins = Counter(row["winner"] for row in group)
        games = len(group)
        record = dict(zip(group_fields, key))
        record.update(
            {
                "games": games,
                "attacker_wins": wins["Attacker"],
                "defender_wins": wins["Defender"],
                "attacker_win_rate": round(wins["Attacker"] / games, 4),
                "mean_total_damage": round(mean(row["total_damage"] for row in group), 4),
                "mean_final_damage_ratio": round(mean(row["final_damage_ratio"] for row in group), 4),
                "mean_edges": round(mean(row["edges"] for row in group), 4),
            }
        )
        summary.append(record)
    return summary


def write_csv(rows, path):
    """Write summary rows to CSV."""
    if not rows:
        return

    with Path(path).open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def print_overall(rows):
    """Print compact overall results to terminal."""
    wins = Counter(row["winner"] for row in rows)
    games = len(rows)
    print(f"Games: {games}")
    print(f"Attacker wins: {wins['Attacker']} ({wins['Attacker'] / games:.1%})")
    print(f"Defender wins: {wins['Defender']} ({wins['Defender'] / games:.1%})")
    print(f"Mean total damage: {mean(row['total_damage'] for row in rows):.3f}")
    print(f"Mean final damage ratio: {mean(row['final_damage_ratio'] for row in rows):.3f}")


def main():
    parser = argparse.ArgumentParser(description="Analyze game statistics CSV files.")
    parser.add_argument(
        "--input",
        default=str(RESULTS_DIR / "smoke_results.csv"),
        help="Raw results CSV from run_batch.py.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1.5,
        help="Attacker wins if final_damage_ratio is at least this value.",
    )
    args = parser.parse_args()

    rows = add_winners(load_rows(args.input), args.threshold)
    input_path = Path(args.input)
    output_prefix = input_path.with_name(input_path.stem + "_analysis")

    summaries = {
        "by_graph": ["graph"],
        "by_attacker": ["attacker"],
        "by_defender": ["defender"],
        "by_matchup": ["attacker", "defender"],
        "by_graph_matchup": ["graph", "attacker", "defender"],
        "by_nodes": ["nodes"],
        "by_edges": ["edges"],
        "by_attack_budget": ["attack_budget"],
        "by_defense_budget": ["defense_budget"],
        "by_multiplier": ["attack_multiplier"],
    }

    print_overall(rows)
    for name, fields in summaries.items():
        path = output_prefix.with_name(f"{output_prefix.name}_{name}.csv")
        write_csv(summarize_by(rows, fields), path)
        print(f"Saved {path}")


if __name__ == "__main__":
    main()
