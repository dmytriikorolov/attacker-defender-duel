"""Random attacker strategy."""

import random

from src.attacker.base_attacker import BaseAttacker
from src.graph_utils import edge_set, normalize_edge


class RandomAttacker(BaseAttacker):
    """Choose random unprotected edges up to the attack budget."""

    def select_edges(self, G, source, target, protected_edges=None):
        protected = edge_set(protected_edges)
        candidates = [
            normalize_edge(edge)
            for edge in G.edges()
            if normalize_edge(edge) not in protected
        ]
        random.shuffle(candidates)
        return candidates[: self.budget]
