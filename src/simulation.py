"""Simulation logic for one network interdiction game."""

from src.graph_utils import apply_attack, get_shortest_path, get_shortest_path_length
from src.metrics import summarize_result


def run_simulation(G, source, target, attacker, protected_edges=None, attack_multiplier=5):
    """
    Run one attack simulation and return all important results.

    The defender is represented only by protected_edges. This keeps the module
    focused on the attack and graph-update logic for this project part.
    """
    protected_edges = protected_edges or []

    baseline_path = get_shortest_path(G, source, target)
    baseline_length = get_shortest_path_length(G, source, target)

    if hasattr(attacker, "attack_multiplier"):
        attacker.attack_multiplier = attack_multiplier

    attacked_edges = attacker.select_edges(G, source, target, protected_edges)
    attacked_graph = apply_attack(
        G,
        attacked_edges,
        protected_edges,
        attack_multiplier,
    )

    attacked_path = get_shortest_path(attacked_graph, source, target)
    attacked_length = get_shortest_path_length(attacked_graph, source, target)

    result = summarize_result(
        baseline_path=baseline_path,
        attacked_path=attacked_path,
        baseline_length=baseline_length,
        attacked_length=attacked_length,
        protected_edges=protected_edges,
        attacked_edges=attacked_edges,
    )
    result["attacked_graph"] = attacked_graph
    return result
