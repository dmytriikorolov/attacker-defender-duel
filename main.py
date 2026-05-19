"""Command-line demo for the Network Defense / Interdiction game."""

import networkx as nx

from src.attacker.greedy_attacker import GreedyAttacker
from src.attacker.random_attacker import RandomAttacker
from src.attacker.shortest_path_attacker import ShortestPathAttacker
from src.simulation import run_simulation


def build_demo_graph():
    """Create a small weighted graph with several source-target routes."""
    G = nx.Graph()
    edges = [
        (0, 1, 2),
        (0, 2, 4),
        (1, 2, 1),
        (1, 3, 7),
        (2, 3, 3),
        (2, 4, 5),
        (3, 5, 2),
        (4, 5, 1),
        (1, 4, 6),
    ]
    G.add_weighted_edges_from(edges)
    return G


def print_result(name, result):
    """Print the main outputs of one simulation in a readable format."""
    print(f"\n{name}")
    print("-" * len(name))
    print(f"Baseline path: {result['baseline_path']}")
    print(f"Attacked path: {result['attacked_path']}")
    print(f"Protected edges: {result['protected_edges']}")
    print(f"Attacked edges: {result['attacked_edges']}")
    print(f"Baseline distance: {result['baseline_length']}")
    print(f"Attacked distance: {result['attacked_length']}")
    print(f"Damage: {result['damage']}")
    print(f"Damage ratio: {result['damage_ratio']:.2f}")


def main():
    G = build_demo_graph()
    source = 0
    target = 5
    protected_edges = [(2, 3), (4, 5)]
    attack_budget = 2
    attack_multiplier = 5

    attackers = [
        ("Random Attacker", RandomAttacker(attack_budget)),
        ("Shortest Path Attacker", ShortestPathAttacker(attack_budget)),
        ("Greedy Attacker", GreedyAttacker(attack_budget, attack_multiplier)),
    ]

    print("Network Defense / Network Interdiction Demo")
    print(f"Source: {source}, target: {target}")
    print(f"Attack budget: {attack_budget}, multiplier: {attack_multiplier}")

    for name, attacker in attackers:
        result = run_simulation(
            G,
            source,
            target,
            attacker,
            protected_edges=protected_edges,
            attack_multiplier=attack_multiplier,
        )
        print_result(name, result)


if __name__ == "__main__":
    main()
