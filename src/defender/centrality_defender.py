"""Centrality-based defender strategy."""
import networkx as nx
 
from src.defender.base_defender import BaseDefender
from src.graph_utils import normalize_edge
 
 
class CentralityDefender(BaseDefender):
    """
    Protect the most "central" edges, no attacker simulation needed.
 
    Intuition: the attacker wants to lengthen the source-target shortest
    path, so the edges that carry the most shortest paths are exactly the
    ones worth shielding. We score every edge by edge-betweenness
    centrality and protect the top-`budget` of them.
 
    By default the scoring is *targeted*: betweenness is computed only over
    shortest paths from `source` to `target`, which is what actually matters
    in this game. Set ``targeted=False`` for plain global edge betweenness
    (the classic textbook centrality), which ignores the specific pair.
 
    Cheaper than GreedyDefender and much smarter than RandomDefender.
    """
 
    def __init__(self, budget, targeted=True, weight="weight"):
        super().__init__(budget)
        self.targeted = targeted
        self.weight = weight
 
    def _edge_scores(self, G, source, target):
        if self.targeted:
            # Only paths that go from source to target count toward the score.
            return nx.edge_betweenness_centrality_subset(
                G,
                sources=[source],
                targets=[target],
                weight=self.weight,
            )
        return nx.edge_betweenness_centrality(G, weight=self.weight)
 
    def select_edges(self, G, source, target):
        scores = self._edge_scores(G, source, target)
 
        # Highest centrality first; protect as many as the budget allows.
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        selected = [normalize_edge(edge) for edge, _ in ranked]
        return selected[: self.budget]
