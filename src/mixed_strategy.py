"""Mixed-strategy simulation helpers."""

import random
from collections import Counter

from src.game import play_round, total_attacker_score
from src.graph_utils import copy_graph, edge_set


def weighted_choice(names, weights, rng):
    """Choose one name using optional probability weights."""
    if not weights:
        return rng.choice(list(names))

    total = sum(weights.get(name, 0) for name in names)
    if total <= 0:
        return rng.choice(list(names))

    threshold = rng.random() * total
    running = 0
    for name in names:
        running += weights.get(name, 0)
        if running >= threshold:
            return name
    return list(names)[-1]


def run_mixed_strategy_game(
    G,
    source,
    target,
    attacker_factories,
    defender_factories,
    attacker_weights=None,
    defender_weights=None,
    rounds=20,
    attack_multiplier=5,
    seed=0,
):
    """
    Run a multi-round game where both players sample strategies each round.

    ``attacker_factories`` and ``defender_factories`` map strategy names to
    callables returning fresh strategy objects. A defender factory may return
    ``None`` to represent no defense.
    """
    rng = random.Random(seed)
    current_graph = copy_graph(G)
    history = []
    blocked_edges = set()
    attacker_counts = Counter()
    defender_counts = Counter()

    attacker_names = list(attacker_factories)
    defender_names = list(defender_factories)

    for round_number in range(1, rounds + 1):
        attacker_name = weighted_choice(attacker_names, attacker_weights, rng)
        defender_name = weighted_choice(defender_names, defender_weights, rng)
        attacker_counts[attacker_name] += 1
        defender_counts[defender_name] += 1

        defender = defender_factories[defender_name]()
        protected_edges = (
            defender.select_edges(current_graph, source, target)
            if defender
            else []
        )
        attacker = attacker_factories[attacker_name]()
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
        result["attacker_strategy"] = attacker_name
        result["defender_strategy"] = defender_name
        history.append(result)
        current_graph = result["attacked_graph"]
        blocked_edges.update(edge_set(result["attacked_edges"]))

    return {
        "initial_graph": copy_graph(G),
        "final_graph": current_graph,
        "history": history,
        "attacker_score": total_attacker_score(history),
        "blocked_edges": sorted(blocked_edges),
        "attacker_strategy_counts": dict(attacker_counts),
        "defender_strategy_counts": dict(defender_counts),
    }
