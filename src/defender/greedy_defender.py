"""Greedy defender strategy."""
from src.attacker.greedy_attacker import GreedyAttacker
from src.defender.base_defender import BaseDefender
from src.graph_utils import apply_attack, get_shortest_path_length, normalize_edge


class GreedyDefender(BaseDefender):
    """
    Greedily protect the edge that best limits a (modeled) greedy attacker.

    Mirrors GreedyAttacker in spirit: for every protection slot we try
    protecting each still-available edge, let a modeled greedy attacker
    respond to that protection set, and keep the edge whose protection
    yields the *shortest* post-attack source-target distance (the defender
    wants the path short, the attacker wants it long).

    Like the attacker, this is intentionally brute force for a course demo.
    """

    def __init__(self, budget, attacker_budget=None, attack_multiplier=5):
        super().__init__(budget)
        # If we don't know the real attacker's budget, assume it matches ours.
        self.attacker_budget = budget if attacker_budget is None else attacker_budget
        self.attack_multiplier = attack_multiplier

    def _attacked_length(self, G, source, target, protected):
        """Let a modeled greedy attacker respond, then measure the path."""
        attacker = GreedyAttacker(self.attacker_budget, self.attack_multiplier)
        attacked = attacker.select_edges(
            G, source, target, protected_edges=protected
        )
        attacked_graph = apply_attack(
            G, attacked, protected, self.attack_multiplier
        )
        return get_shortest_path_length(attacked_graph, source, target)

    def select_edges(self, G, source, target):
        # Lower bound for the defender: the attacker only ever *increases*
        # weights, so the post-attack path can never be shorter than this.
        # Once we reach it we've fully neutralized the attacker.
        clean_length = get_shortest_path_length(G, source, target)

        selected = []
        for _ in range(self.budget):
            candidates = [
                normalize_edge(edge)
                for edge in G.edges()
                if normalize_edge(edge) not in selected
            ]

            best_edge = None
            best_length = None
            for edge in candidates:
                trial_protected = selected + [edge]
                length = self._attacked_length(
                    G, source, target, trial_protected
                )
                if best_length is None or length < best_length:
                    best_length = length
                    best_edge = edge

            if best_edge is None:
                break

            selected.append(best_edge)

            # Attacker can no longer gain anything -> stop spending budget.
            if best_length is not None and best_length <= clean_length:
                break

        return selected
