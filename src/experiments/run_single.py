"""Run ONE configuration end to end.

This is the atomic experiment: pick a graph model, an attacker and a
defender, build everything from the shared registries, run a single
simulation and return one flat record. `run_batch` just calls this in a
loop, so all the "how do I wire a run together" logic lives here once.

Run it directly to sanity-check a single setup:

    python -m experiments.run_single --graph "Erdos-Renyi G(n,p)" \
        --attacker Greedy --defender Centrality --seed 7
"""

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # so `import src` works as a script

from src.registry import ATTACKERS, DEFENDERS, GRAPH_GENERATORS
from src.simulation import run_simulation

# Defaults for every knob; any of these can be overridden per call.
DEFAULTS = dict(node_count=10, edge_probability=0.35, seed=7, attack_budget=2, defense_budget=2, attack_multiplier=5.0)


def build_params(**overrides):
    """Merge overrides onto DEFAULTS into the namespace every factory expects."""
    return SimpleNamespace(**{**DEFAULTS, **overrides})


def run_one(graph="Erdos-Renyi G(n,p)", attacker="Greedy", defender="None", **overrides):
    """Run a single graph/attacker/defender combo and return a flat record."""
    params = build_params(**overrides)
    source, target = 0, params.node_count - 1

    G = GRAPH_GENERATORS[graph](params)
    defender_obj = DEFENDERS[defender](params)
    protected = defender_obj.select_edges(G, source, target) if defender_obj else []
    attacker_obj = ATTACKERS[attacker](params)
    result = run_simulation(G, source, target, attacker_obj, protected_edges=protected, attack_multiplier=params.attack_multiplier)

    return {
        "graph": graph, "attacker": attacker, "defender": defender, "seed": params.seed,
        "nodes": params.node_count, "edges": G.number_of_edges(),
        "baseline_length": result["baseline_length"], "attacked_length": result["attacked_length"],
        "damage": result["damage"], "damage_ratio": result["damage_ratio"],
    }


def main():
    parser = argparse.ArgumentParser(description="Run one interdiction simulation.")
    parser.add_argument("--graph", default="Erdos-Renyi G(n,p)", choices=list(GRAPH_GENERATORS))
    parser.add_argument("--attacker", default="Greedy", choices=list(ATTACKERS))
    parser.add_argument("--defender", default="None", choices=list(DEFENDERS))
    parser.add_argument("--nodes", type=int, default=DEFAULTS["node_count"])
    parser.add_argument("--seed", type=int, default=DEFAULTS["seed"])
    args = parser.parse_args()

    record = run_one(args.graph, args.attacker, args.defender, node_count=args.nodes, seed=args.seed)
    width = max(len(k) for k in record)
    for key, value in record.items():
        print(f"{key:<{width}} : {value}")


if __name__ == "__main__":
    main()