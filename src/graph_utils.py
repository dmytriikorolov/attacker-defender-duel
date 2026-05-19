"""Utility functions for weighted undirected graphs used in the game."""

import networkx as nx


def normalize_edge(edge):
    """Return an undirected edge in a canonical order."""
    u, v = edge
    return tuple(sorted((u, v)))


def edge_set(edges):
    """Normalize a collection of edges so (u, v) and (v, u) match."""
    if edges is None:
        return set()
    return {normalize_edge(edge) for edge in edges}


def get_shortest_path(G, source, target):
    """Return the weighted shortest path, or None when no path exists."""
    try:
        return nx.shortest_path(G, source=source, target=target, weight="weight")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def get_shortest_path_length(G, source, target):
    """Return the weighted shortest path length, or infinity if unreachable."""
    try:
        return nx.shortest_path_length(G, source=source, target=target, weight="weight")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return float("inf")


def edges_from_path(path):
    """Convert a node path like [0, 1, 3] into normalized edge tuples."""
    if not path or len(path) < 2:
        return []
    return [normalize_edge((path[i], path[i + 1])) for i in range(len(path) - 1)]


def copy_graph(G):
    """Return a copy so simulations do not mutate the original graph."""
    return G.copy()


def apply_attack(G, attacked_edges, protected_edges, attack_multiplier):
    """
    Return a modified copy of G after applying attacks.

    Protected edges keep their original weight. Unprotected attacked edges have
    their weight multiplied by attack_multiplier.
    """
    attacked = edge_set(attacked_edges)
    protected = edge_set(protected_edges)
    attacked_graph = copy_graph(G)

    for edge in attacked:
        if edge in protected:
            continue
        u, v = edge
        if attacked_graph.has_edge(u, v):
            original_weight = get_edge_weight(attacked_graph, edge)
            set_edge_weight(attacked_graph, edge, original_weight * attack_multiplier)

    return attacked_graph


def get_edge_weight(G, edge):
    """Return the weight of an edge, defaulting to 1 if missing."""
    u, v = normalize_edge(edge)
    return G[u][v].get("weight", 1)


def set_edge_weight(G, edge, weight):
    """Set the weight of an existing edge."""
    u, v = normalize_edge(edge)
    G[u][v]["weight"] = weight
