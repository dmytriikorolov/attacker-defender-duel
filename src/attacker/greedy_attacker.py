"""Greedy attacker strategy."""

from src.attacker.base_attacker import BaseAttacker
from src.graph_utils import (
    apply_attack,
    edge_set,
    get_shortest_path_length,
    normalize_edge,
)


class GreedyAttacker(BaseAttacker):
    """
    Greedily choose the edge that maximizes the resulting shortest path length.

    This is intentionally simple for a course demo: each slot tests every
    currently available edge by applying a temporary attack and measuring the
    new source-target distance.
    """

    def __init__(self, budget, attack_multiplier=5):
        super().__init__(budget)
        self.attack_multiplier = attack_multiplier

    def select_edges(self, G, source, target, protected_edges=None):
        protected = edge_set(protected_edges)
        selected = []

        for _ in range(self.budget):
            current_graph = apply_attack(
                G,
                selected,
                protected,
                self.attack_multiplier,
            )
            current_length = get_shortest_path_length(current_graph, source, target)

            best_edge = None
            best_length = current_length

            candidates = [
                normalize_edge(edge)
                for edge in G.edges()
                if normalize_edge(edge) not in protected
                and normalize_edge(edge) not in selected
            ]

            for edge in candidates:
                trial_edges = selected + [edge]
                trial_graph = apply_attack(
                    G,
                    trial_edges,
                    protected,
                    self.attack_multiplier,
                )
                trial_length = get_shortest_path_length(trial_graph, source, target)

                if trial_length > best_length:
                    best_length = trial_length
                    best_edge = edge

            if best_edge is None:
                break
            selected.append(best_edge)

        return selected
