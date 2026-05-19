"""Random graph generators for the interdiction game.

Every generator takes the shared `params` namespace (it needs
`node_count`, `edge_probability`, `seed`) and returns a *connected,
weighted, undirected* graph whose nodes are the integers
0..node_count-1. Keeping that contract identical for every model lets
the rest of the app treat them all the same way.
"""

import math
import random

import networkx as nx

WEIGHT_RANGE = (1, 10)


def _connect(G, rng):
    """Bridge separate components so an s-t path always exists."""
    comps = [list(c) for c in nx.connected_components(G)]
    for a, b in zip(comps, comps[1:]):
        G.add_edge(rng.choice(a), rng.choice(b))
    return G


def _finalize(G, rng):
    """Relabel to 0..n-1 ints, force connectivity, assign weights."""
    G = nx.convert_node_labels_to_integers(G, ordering="sorted")
    _connect(G, rng)
    for u, v in G.edges():
        G[u][v]["weight"] = rng.randint(*WEIGHT_RANGE)
    return G


def erdos_renyi(p):
    """G(n, p): each possible edge appears independently with prob p."""
    G = nx.gnp_random_graph(p.node_count, p.edge_probability, seed=p.seed)
    return _finalize(G, random.Random(p.seed))


def scale_free(p):
    """Barabasi-Albert preferential attachment - produces hub nodes."""
    m = min(max(1, round(p.edge_probability * (p.node_count - 1))), p.node_count - 1)
    G = nx.barabasi_albert_graph(p.node_count, m, seed=p.seed)
    return _finalize(G, random.Random(p.seed))


def fixed_edges(p):
    """G(n, m): a fixed edge count derived from the density slider."""
    max_edges = p.node_count * (p.node_count - 1) // 2
    m = min(max(p.node_count - 1, round(p.edge_probability * max_edges)), max_edges)
    G = nx.gnm_random_graph(p.node_count, m, seed=p.seed)
    return _finalize(G, random.Random(p.seed))


def geometric(p):
    """Random geometric graph - nodes close in the unit square connect."""
    radius = 2.0 * math.sqrt(p.edge_probability) / math.sqrt(p.node_count)
    G = nx.random_geometric_graph(p.node_count, radius, seed=p.seed)
    return _finalize(G, random.Random(p.seed))


def grid(p):
    """2D lattice closest to square, trimmed to exactly node_count nodes."""
    rows = max(1, math.isqrt(p.node_count))
    cols = math.ceil(p.node_count / rows)
    G = nx.convert_node_labels_to_integers(nx.grid_2d_graph(rows, cols), ordering="sorted")
    G.remove_nodes_from(range(p.node_count, rows * cols))
    return _finalize(G, random.Random(p.seed))


# name -> generator(params). Add a model = one line here, no UI changes.
GRAPH_GENERATORS = {
    "Erdos-Renyi G(n,p)": erdos_renyi,
    "Scale-free (Barabasi-Albert)": scale_free,
    "Fixed edge count G(n,m)": fixed_edges,
    "Geometric": geometric,
    "Grid / lattice": grid,
}