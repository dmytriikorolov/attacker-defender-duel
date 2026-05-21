"""Run one multi-round game configuration and return flat statistics."""

import argparse
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.game import run_game
from src.graph_utils import get_shortest_path_length
from src.metrics import compute_vulnerability_metrics
from src.registry import ATTACKERS, DEFENDERS, GRAPH_GENERATORS


DEFAULTS = {
    "node_count": 10,
    "edge_probability": 0.35,
    "seed": 0,
    "attack_budget": 2,
    "defense_budget": 2,
    "attack_multiplier": 5.0,
    "rounds": 5,
}


def build_params(**overrides):
    """Create the shared parameter namespace expected by factories."""
    return SimpleNamespace(**{**DEFAULTS, **overrides})


def run_one_game(
    graph="Erdos-Renyi G(n,p)",
    attacker="Greedy",
    defender="Centrality",
    **overrides,
):
    """Run one game and return a flat dictionary suitable for a CSV row."""
    params = build_params(**overrides)
    source = 0
    target = params.node_count - 1
    G = GRAPH_GENERATORS[graph](params)

    start = time.perf_counter()
    game = run_game(
        G,
        source,
        target,
        attacker_factory=lambda: ATTACKERS[attacker](params),
        defender_factory=lambda: DEFENDERS[defender](params),
        rounds=params.rounds,
        attack_multiplier=params.attack_multiplier,
    )
    runtime_seconds = time.perf_counter() - start

    history = game["history"]
    damages = [result["damage"] for result in history]
    ratios = [result["damage_ratio"] for result in history]
    protected_counts = [len(result["protected_edges"]) for result in history]
    attacked_counts = [len(result["attacked_edges"]) for result in history]

    initial_length = get_shortest_path_length(G, source, target)
    final_length = get_shortest_path_length(game["final_graph"], source, target)
    vulnerability = compute_vulnerability_metrics(G, source, target)

    record = {
        "graph": graph,
        "attacker": attacker,
        "defender": defender,
        "seed": params.seed,
        "nodes": params.node_count,
        "edges": G.number_of_edges(),
        "actual_density": round(G.number_of_edges() / (params.node_count * (params.node_count - 1) / 2), 4),
        "density_parameter": params.edge_probability,
        "attack_budget": params.attack_budget,
        "defense_budget": params.defense_budget,
        "attack_multiplier": params.attack_multiplier,
        "rounds_requested": params.rounds,
        "rounds_played": len(history),
        "initial_length": initial_length,
        "final_length": final_length,
        "total_damage": game["attacker_score"],
        "mean_round_damage": sum(damages) / len(damages) if damages else 0,
        "max_round_damage": max(damages) if damages else 0,
        "mean_damage_ratio": sum(ratios) / len(ratios) if ratios else 1,
        "final_damage_ratio": final_length / initial_length if initial_length else float("inf"),
        "total_attacked_edges": sum(attacked_counts),
        "unique_attacked_edges": len(game["blocked_edges"]),
        "mean_protected_edges": sum(protected_counts) / len(protected_counts) if protected_counts else 0,
        "runtime_seconds": round(runtime_seconds, 4),
    }
    record.update(
        {
            key: round(value, 4) if isinstance(value, float) else value
            for key, value in vulnerability.items()
        }
    )
    return record


def main():
    parser = argparse.ArgumentParser(description="Run one multi-round interdiction game.")
    parser.add_argument("--graph", default="Erdos-Renyi G(n,p)", choices=list(GRAPH_GENERATORS))
    parser.add_argument("--attacker", default="Greedy", choices=list(ATTACKERS))
    parser.add_argument("--defender", default="Centrality", choices=list(DEFENDERS))
    parser.add_argument("--nodes", type=int, default=DEFAULTS["node_count"])
    parser.add_argument("--density", type=float, default=DEFAULTS["edge_probability"])
    parser.add_argument("--seed", type=int, default=DEFAULTS["seed"])
    parser.add_argument("--attack-budget", type=int, default=DEFAULTS["attack_budget"])
    parser.add_argument("--defense-budget", type=int, default=DEFAULTS["defense_budget"])
    parser.add_argument("--multiplier", type=float, default=DEFAULTS["attack_multiplier"])
    parser.add_argument("--rounds", type=int, default=DEFAULTS["rounds"])
    args = parser.parse_args()

    record = run_one_game(
        graph=args.graph,
        attacker=args.attacker,
        defender=args.defender,
        node_count=args.nodes,
        edge_probability=args.density,
        seed=args.seed,
        attack_budget=args.attack_budget,
        defense_budget=args.defense_budget,
        attack_multiplier=args.multiplier,
        rounds=args.rounds,
    )

    width = max(len(key) for key in record)
    for key, value in record.items():
        print(f"{key:<{width}} : {value}")


if __name__ == "__main__":
    main()
