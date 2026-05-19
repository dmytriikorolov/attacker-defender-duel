"""Metrics for measuring the effect of an attack."""

from src.graph_utils import edge_set


def compute_damage(baseline_length, attacked_length):
    """Return the absolute increase in shortest path length."""
    if baseline_length == float("inf") or attacked_length == float("inf"):
        return float("inf")
    return attacked_length - baseline_length


def compute_damage_ratio(baseline_length, attacked_length):
    """Return attacked_length / baseline_length when it is well-defined."""
    if baseline_length == 0:
        return float("inf")
    if baseline_length == float("inf") and attacked_length == float("inf"):
        return 1
    return attacked_length / baseline_length


def summarize_result(
    baseline_path,
    attacked_path,
    baseline_length,
    attacked_length,
    protected_edges,
    attacked_edges,
):
    """Collect paths, selected edges, and damage metrics in one dictionary."""
    return {
        "baseline_path": baseline_path,
        "attacked_path": attacked_path,
        "baseline_length": baseline_length,
        "attacked_length": attacked_length,
        "protected_edges": sorted(edge_set(protected_edges)),
        "attacked_edges": sorted(edge_set(attacked_edges)),
        "damage": compute_damage(baseline_length, attacked_length),
        "damage_ratio": compute_damage_ratio(baseline_length, attacked_length),
    }
