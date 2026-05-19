"""Attacker that focuses on the current shortest path."""

import random

from src.attacker.base_attacker import BaseAttacker
from src.graph_utils import edge_set, edges_from_path, get_shortest_path, normalize_edge


class ShortestPathAttacker(BaseAttacker):
    """
    Attack unprotected edges on the current shortest path first.

    If the shortest path has fewer available edges than the budget, fill the
    remaining attack slots with random unprotected edges elsewhere in the graph.
    """

    def select_edges(self, G, source, target, protected_edges=None):
        protected = edge_set(protected_edges)
        path = get_shortest_path(G, source, target)
        selected = []

        for edge in edges_from_path(path):
            if edge not in protected and edge not in selected:
                selected.append(edge)
            if len(selected) == self.budget:
                return selected

        remaining = [
            normalize_edge(edge)
            for edge in G.edges()
            if normalize_edge(edge) not in protected
            and normalize_edge(edge) not in selected
        ]
        random.shuffle(remaining)
        selected.extend(remaining[: self.budget - len(selected)])
        return selected
