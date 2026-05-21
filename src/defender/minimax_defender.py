"""Minimax defender strategy."""

from itertools import combinations

import networkx as nx

from src.defender.base_defender import BaseDefender
from src.graph_utils import (
    apply_attack,
    edges_from_path,
    get_shortest_path,
    get_shortest_path_length,
    normalize_edge,
)


class MinimaxDefender(BaseDefender):
    """
    Protect edges that minimize the attacker's best possible response.

    On small graphs this enumerates every defense set and every attack set,
    so it is an exact one-round minimax defender. On larger graphs it narrows
    the search to the shortest-path edges plus high-centrality edges.
    """

    def __init__(
        self,
        budget,
        attacker_budget=None,
        attack_multiplier=5,
        max_exact_edges=14,
        max_candidate_edges=12,
    ):
        super().__init__(budget)
        self.attacker_budget = budget if attacker_budget is None else attacker_budget
        self.attack_multiplier = attack_multiplier
        self.max_exact_edges = max_exact_edges
        self.max_candidate_edges = max_candidate_edges

    def _ranked_candidate_edges(self, G, source, target):
        edges = sorted(normalize_edge(edge) for edge in G.edges())
        if len(edges) <= self.max_exact_edges:
            return edges

        shortest_path_edges = set(edges_from_path(get_shortest_path(G, source, target)))
        scores = nx.edge_betweenness_centrality(G, weight="weight")
        ranked = [
            normalize_edge(edge)
            for edge, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)
        ]

        candidates = list(shortest_path_edges)
        for edge in ranked:
            if edge not in candidates:
                candidates.append(edge)
            if len(candidates) >= self.max_candidate_edges:
                break
        return sorted(candidates)

    def _edge_combinations(self, edges, budget):
        budget = min(budget, len(edges))
        if budget <= 0:
            return [()]
        return list(combinations(edges, budget))

    def _best_attack_length(self, G, source, target, protected, attack_edges):
        best_length = get_shortest_path_length(G, source, target)
        for attacked in self._edge_combinations(attack_edges, self.attacker_budget):
            attacked_graph = apply_attack(
                G,
                attacked,
                protected,
                self.attack_multiplier,
            )
            length = get_shortest_path_length(attacked_graph, source, target)
            if length > best_length:
                best_length = length
        return best_length

    def select_edges(self, G, source, target):
        candidates = self._ranked_candidate_edges(G, source, target)
        if self.budget <= 0 or not candidates:
            return []

        best_protected = ()
        best_worst_length = None

        for protected in self._edge_combinations(candidates, self.budget):
            worst_length = self._best_attack_length(
                G,
                source,
                target,
                protected,
                candidates,
            )
            if best_worst_length is None or worst_length < best_worst_length:
                best_worst_length = worst_length
                best_protected = protected

        return list(best_protected)
