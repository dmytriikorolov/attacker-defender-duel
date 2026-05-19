"""Sweep MANY configurations - the tournament.

The interesting question this answers: which defender holds up best,
against which attacker, on which graph topology? We run every
defender x attacker x graph-model combo across several seeds, collect
the metrics into one tidy DataFrame, dump it to results.csv, and print
a quick pivot so you see the answer without opening the file.

    python -m experiments.run_batch

Cost note: GreedyDefender internally simulates a greedy attacker, so
the full grid is the slow part. Shrink the lists below if it drags.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.run_single import run_one
from src.registry import ATTACKERS, DEFENDERS, GRAPH_GENERATORS

# The experiment grid. This *is* the experiment - tweak it freely.
GRAPHS = list(GRAPH_GENERATORS)
ATTACKER_NAMES = list(ATTACKERS)
DEFENDER_NAMES = list(DEFENDERS)
SEEDS = list(range(5))
OVERRIDES = dict(node_count=10, edge_probability=0.35, attack_budget=3, defense_budget=3, attack_multiplier=5.0)

RESULTS_CSV = Path(__file__).parent / "results.csv"


def run_sweep():
    """Run the whole grid and return a tidy DataFrame (one row per run)."""
    combos = [(g, a, d, s) for g in GRAPHS for a in ATTACKER_NAMES for d in DEFENDER_NAMES for s in SEEDS]
    rows = []
    for i, (graph, attacker, defender, seed) in enumerate(combos, start=1):
        print(f"[{i}/{len(combos)}] {graph} | {attacker} vs {defender} | seed {seed}")
        rows.append(run_one(graph, attacker, defender, seed=seed, **OVERRIDES))
    return pd.DataFrame(rows)


def main():
    df = run_sweep()
    df.to_csv(RESULTS_CSV, index=False)

    # Lower damage_ratio = the attack achieved less = the defender did better.
    summary = df.pivot_table(values="damage_ratio", index="defender", columns="attacker", aggfunc="mean").round(3)
    print("\nMean damage_ratio (averaged over graphs and seeds):\n")
    print(summary.to_string())
    print(f"\nSaved {len(df)} runs to {RESULTS_CSV}")


if __name__ == "__main__":
    main()