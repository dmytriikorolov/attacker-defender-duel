"""Random defender strategy."""
import random

from src.defender.base_defender import BaseDefender
from src.graph_utils import normalize_edge


class RandomDefender(BaseDefender):
    """Protect random edges up to the defense budget."""

    def select_edges(self, G, source, target):
        candidates = [normalize_edge(edge) for edge in G.edges()]
        random.shuffle(candidates)
        return candidates[: self.budget]
