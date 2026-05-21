"""Shared strategy registries: name -> factory(params).

Single source of truth used by both the Streamlit app and the
experiment scripts, so a new strategy is added in exactly one place.
"""

from src.attacker.greedy_attacker import GreedyAttacker
from src.attacker.random_attacker import RandomAttacker
from src.attacker.shortest_path_attacker import ShortestPathAttacker
from src.defender.centrality_defender import CentralityDefender
from src.defender.greedy_defender import GreedyDefender
from src.defender.minimax_defender import MinimaxDefender
from src.defender.random_defender import RandomDefender
from src.graph_generator import GRAPH_GENERATORS  # re-exported for one import point

ATTACKERS = {
    "Random": lambda p: RandomAttacker(p.attack_budget),
    "Shortest path": lambda p: ShortestPathAttacker(p.attack_budget),
    "Greedy": lambda p: GreedyAttacker(p.attack_budget, p.attack_multiplier),
}

DEFENDERS = {
    "None": lambda p: None,
    "Random": lambda p: RandomDefender(p.defense_budget),
    "Centrality": lambda p: CentralityDefender(p.defense_budget),
    "Greedy": lambda p: GreedyDefender(
        p.defense_budget,
        p.attack_budget,
        p.attack_multiplier,
    ),
    "Minimax": lambda p: MinimaxDefender(
        p.defense_budget,
        p.attack_budget,
        p.attack_multiplier,
    ),
}

__all__ = ["ATTACKERS", "DEFENDERS", "GRAPH_GENERATORS"]
