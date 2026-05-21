"""Metrics for measuring graph vulnerability and attack effects."""

import networkx as nx

from src.graph_utils import edge_set, edges_from_path, get_shortest_path, get_shortest_path_length


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


def _safe_edge_connectivity(G, source, target):
    try:
        return nx.edge_connectivity(G, source, target)
    except (nx.NetworkXError, nx.NetworkXException):
        return 0


def _shortest_paths(G, source, target):
    try:
        return list(nx.all_shortest_paths(G, source=source, target=target, weight="weight"))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def compute_vulnerability_metrics(G, source, target):
    """
    Return graph-level signals that explain how fragile the source-target pair is.

    Higher ``alternative_path_ratio`` means the first edge-disjoint alternative
    path is much worse than the current shortest path. ``inf`` means no such
    alternative path exists.
    """
    baseline_length = get_shortest_path_length(G, source, target)
    shortest_paths = _shortest_paths(G, source, target)
    shortest_path = get_shortest_path(G, source, target)
    shortest_path_edges = edges_from_path(shortest_path)

    without_primary_path = G.copy()
    without_primary_path.remove_edges_from(shortest_path_edges)
    alternative_length = get_shortest_path_length(without_primary_path, source, target)

    if baseline_length in (0, float("inf")):
        alternative_path_ratio = float("inf")
    else:
        alternative_path_ratio = alternative_length / baseline_length

    betweenness = nx.edge_betweenness_centrality(G, weight="weight") if G.number_of_edges() else {}
    total_betweenness = sum(betweenness.values())
    max_betweenness = max(betweenness.values(), default=0)

    return {
        "edge_connectivity": _safe_edge_connectivity(G, source, target),
        "shortest_path_count": len(shortest_paths),
        "shortest_path_edge_count": len(shortest_path_edges),
        "bridge_count": len(list(nx.bridges(G))) if not G.is_directed() else 0,
        "betweenness_concentration": (
            max_betweenness / total_betweenness if total_betweenness else 0
        ),
        "alternative_path_ratio": alternative_path_ratio,
    }
