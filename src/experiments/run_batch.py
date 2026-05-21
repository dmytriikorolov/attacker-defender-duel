"""Run parameter sweeps for multi-round network interdiction games.

The literal Cartesian product of every reasonable value can be huge. This
script therefore provides presets:

    smoke     quick correctness check
    standard  broad enough for project statistics
    full      much larger sweep; use --estimate first
"""

import argparse
import csv
import sys
from itertools import product
from pathlib import Path
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.experiments.run_single import run_one_game
from src.registry import ATTACKERS, DEFENDERS, GRAPH_GENERATORS


RESULTS_DIR = Path(__file__).parent / "results"

PRESETS = {
    "smoke": {
        "nodes": [5, 10],
        "densities": [0.35],
        "seeds": [0, 1],
        "attack_budgets": [1, 2],
        "defense_budgets": [0, 2],
        "multipliers": [3.0],
        "rounds": [3],
        "graphs": list(GRAPH_GENERATORS),
        "attackers": list(ATTACKERS),
        "defenders": list(DEFENDERS),
    },
    "standard": {
        "nodes": [5, 10, 15, 20],
        "densities": [0.35, 0.6],
        "seeds": list(range(13)),
        "attack_budgets": [1, 2],
        "defense_budgets": [0, 2],
        "multipliers": [2.0, 5.0],
        "rounds": [5],
        "graphs": list(GRAPH_GENERATORS),
        "attackers": list(ATTACKERS),
        "defenders": list(DEFENDERS),
    },
    "full": {
        "nodes": list(range(5, 21)),
        "densities": [0.2, 0.35, 0.5, 0.7],
        "seeds": list(range(13)),
        "attack_budgets": [1, 2, 3, 4],
        "defense_budgets": [0, 1, 2, 3, 4],
        "multipliers": [2.0, 3.0, 5.0, 10.0],
        "rounds": [5],
        "graphs": list(GRAPH_GENERATORS),
        "attackers": list(ATTACKERS),
        "defenders": list(DEFENDERS),
    },
}


def iter_configs(preset):
    """Yield all configurations in a preset."""
    keys = [
        "graphs",
        "attackers",
        "defenders",
        "nodes",
        "densities",
        "seeds",
        "attack_budgets",
        "defense_budgets",
        "multipliers",
        "rounds",
    ]
    for values in product(*(preset[key] for key in keys)):
        yield dict(zip(keys, values))


def estimate_count(preset):
    """Return how many games a preset will run."""
    total = 1
    for values in preset.values():
        total *= len(values)
    return total


def run_sweep(preset_name, limit=None):
    """Run a preset sweep and return a list of flat records."""
    preset = PRESETS[preset_name]
    rows = []
    total = estimate_count(preset)

    for index, config in enumerate(iter_configs(preset), start=1):
        if limit is not None and index > limit:
            break

        print(
            f"[{index}/{total}] "
            f"{config['graphs']} | {config['attackers']} vs {config['defenders']} | "
            f"n={config['nodes']} density={config['densities']} seed={config['seeds']} | "
            f"a={config['attack_budgets']} d={config['defense_budgets']} m={config['multipliers']}"
        )
        rows.append(
            run_one_game(
                graph=config["graphs"],
                attacker=config["attackers"],
                defender=config["defenders"],
                node_count=config["nodes"],
                edge_probability=config["densities"],
                seed=config["seeds"],
                attack_budget=config["attack_budgets"],
                defense_budget=config["defense_budgets"],
                attack_multiplier=config["multipliers"],
                rounds=config["rounds"],
            )
        )

    return rows


def write_csv(rows, path):
    """Write flat records to a CSV file."""
    if not rows:
        return

    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows):
    """Create compact aggregate statistics for reports."""
    groups = {}
    for row in rows:
        key = (row["graph"], row["attacker"], row["defender"])
        groups.setdefault(key, []).append(row)

    summary = []
    for (graph, attacker, defender), group in sorted(groups.items()):
        summary.append(
            {
                "graph": graph,
                "attacker": attacker,
                "defender": defender,
                "games": len(group),
                "mean_total_damage": round(mean(row["total_damage"] for row in group), 4),
                "median_total_damage": round(median(row["total_damage"] for row in group), 4),
                "mean_final_ratio": round(mean(row["final_damage_ratio"] for row in group), 4),
                "mean_round_damage": round(mean(row["mean_round_damage"] for row in group), 4),
                "mean_runtime_seconds": round(mean(row["runtime_seconds"] for row in group), 4),
            }
        )
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run statistics sweeps.")
    parser.add_argument("--preset", choices=PRESETS, default="smoke")
    parser.add_argument("--estimate", action="store_true", help="Only print number of games.")
    parser.add_argument("--limit", type=int, help="Run only the first N games.")
    parser.add_argument("--output", default=None, help="CSV output path.")
    args = parser.parse_args()

    preset = PRESETS[args.preset]
    count = estimate_count(preset)
    print(f"Preset {args.preset!r} contains {count} games.")
    if args.estimate:
        return

    RESULTS_DIR.mkdir(exist_ok=True)
    output = Path(args.output) if args.output else RESULTS_DIR / f"{args.preset}_results.csv"
    summary_output = output.with_name(output.stem + "_summary.csv")

    rows = run_sweep(args.preset, limit=args.limit)
    write_csv(rows, output)
    write_csv(summarize(rows), summary_output)

    print(f"\nSaved raw results to {output}")
    print(f"Saved summary to {summary_output}")


if __name__ == "__main__":
    main()
