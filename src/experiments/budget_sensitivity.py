"""Run a focused attack/defense budget sensitivity sweep."""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.experiments.run_single import run_one_game


RESULTS_DIR = Path(__file__).parent / "results"


def run_budget_sensitivity(args):
    """Return rows for all attack/defense budget pairs and seeds."""
    rows = []
    for seed in range(args.seeds):
        for attack_budget in range(args.max_attack_budget + 1):
            for defense_budget in range(args.max_defense_budget + 1):
                if attack_budget == 0:
                    continue
                row = run_one_game(
                    graph=args.graph,
                    attacker=args.attacker,
                    defender=args.defender,
                    node_count=args.nodes,
                    edge_probability=args.density,
                    seed=seed,
                    attack_budget=attack_budget,
                    defense_budget=defense_budget,
                    attack_multiplier=args.multiplier,
                    rounds=args.rounds,
                )
                rows.append(row)
    return rows


def write_csv(rows, path):
    """Write rows to CSV."""
    if not rows:
        return
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Run budget sensitivity experiments.")
    parser.add_argument("--graph", default="Erdos-Renyi G(n,p)")
    parser.add_argument("--attacker", default="Greedy")
    parser.add_argument("--defender", default="Minimax")
    parser.add_argument("--nodes", type=int, default=8)
    parser.add_argument("--density", type=float, default=0.35)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--max-attack-budget", type=int, default=4)
    parser.add_argument("--max-defense-budget", type=int, default=4)
    parser.add_argument("--multiplier", type=float, default=5.0)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument(
        "--output",
        default=str(RESULTS_DIR / "budget_sensitivity.csv"),
    )
    args = parser.parse_args()

    rows = run_budget_sensitivity(args)
    write_csv(rows, Path(args.output))
    print(f"Saved {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
