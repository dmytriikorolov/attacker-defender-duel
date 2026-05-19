"""Multi-round game logic for the network interdiction project."""

from src.graph_utils import (
    apply_attack,
    copy_graph,
    edge_set,
    get_shortest_path,
    get_shortest_path_length,
)
from src.metrics import compute_damage, summarize_result


def _add_score_fields(result, round_number):
    """Add round number and scoring fields to a simulation result."""
    damage = compute_damage(result["baseline_length"], result["attacked_length"])
    attacker_points = damage if damage != float("inf") else float("inf")

    result["round"] = round_number
    result["attacker_points"] = attacker_points
    return result


def play_round(
    current_graph,
    source,
    target,
    attacker,
    protected_edges=None,
    blocked_edges=None,
    attack_multiplier=5,
    round_number=1,
):
    """
    Play one round from the current graph state.

    Attacks are permanent because the returned ``attacked_graph`` already has
    increased edge weights. Protected edges only matter for this single round.
    Blocked edges are already-damaged edges that cannot be attacked again.
    """
    protected_edges = protected_edges or []
    blocked_edges = blocked_edges or []
    selection_blocked = edge_set(protected_edges) | edge_set(blocked_edges)

    baseline_path = get_shortest_path(current_graph, source, target)
    baseline_length = get_shortest_path_length(current_graph, source, target)

    if hasattr(attacker, "attack_multiplier"):
        attacker.attack_multiplier = attack_multiplier

    attacked_edges = attacker.select_edges(
        current_graph,
        source,
        target,
        protected_edges=selection_blocked,
    )
    attacked_graph = apply_attack(
        current_graph,
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
    result["start_graph"] = copy_graph(current_graph)
    return _add_score_fields(result, round_number)


def run_game(
    G,
    source,
    target,
    attacker_factory,
    defender_factory=None,
    rounds=5,
    attack_multiplier=5,
):
    """
    Run a complete automated multi-round game.

    Factories are callables that return a fresh attacker/defender for each
    round. Passing factories avoids hidden state carrying between rounds.
    """
    current_graph = copy_graph(G)
    history = []
    blocked_edges = set()

    for round_number in range(1, rounds + 1):
        defender = defender_factory() if defender_factory else None
        protected_edges = (
            defender.select_edges(current_graph, source, target)
            if defender
            else []
        )
        attacker = attacker_factory()
        result = play_round(
            current_graph,
            source,
            target,
            attacker,
            protected_edges=protected_edges,
            blocked_edges=blocked_edges,
            attack_multiplier=attack_multiplier,
            round_number=round_number,
        )
        history.append(result)
        current_graph = result["attacked_graph"]
        blocked_edges.update(edge_set(result["attacked_edges"]))

    return {
        "initial_graph": copy_graph(G),
        "final_graph": current_graph,
        "history": history,
        "attacker_score": total_attacker_score(history),
        "blocked_edges": sorted(blocked_edges),
    }


def total_attacker_score(history):
    """Return total damage accumulated by the attacker across rounds."""
    total = 0
    for result in history:
        points = result.get("attacker_points", 0)
        if points == float("inf"):
            return float("inf")
        total += points
    return total
