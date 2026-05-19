"""Streamlit UI for one network interdiction simulation."""

from types import SimpleNamespace

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

from src.graph_utils import apply_attack, edge_set, edges_from_path, normalize_edge
from src.registry import ATTACKERS, DEFENDERS, GRAPH_GENERATORS
from src.simulation import run_simulation


def compute_layout(G, seed):
    """Stable, evenly spread positions; reuse geometric coords if present."""
    pos = nx.get_node_attributes(G, "pos")
    if len(pos) == G.number_of_nodes():
        return {n: tuple(xy) for n, xy in pos.items()}
    try:
        # Deterministic (no random jitter between reruns), even spacing,
        # and weight=None so random edge weights don't fling nodes away.
        return nx.kamada_kawai_layout(G, weight=None)
    except Exception:
        return nx.spring_layout(G, weight=None, iterations=200, seed=seed)


def _draw_edges(G, pos, edges, ax, **style):
    """Draw one highlighted edge layer (skips empty layers)."""
    if edges:
        nx.draw_networkx_edges(G, pos, edgelist=list(edges), ax=ax, **style)


def draw_graph(G, pos, title, protected_edges=None, attacked_edges=None, shortest_path=None):
    """Draw graph with protected, attacked, and shortest-path edges highlighted."""
    protected, attacked = edge_set(protected_edges), edge_set(attacked_edges)
    path_edges = set(edges_from_path(shortest_path))
    highlighted = protected | attacked | path_edges

    n = G.number_of_nodes()
    node_size = max(250, 1100 - 45 * n)
    font_size = 11 if n <= 10 else 8
    show_weights = G.number_of_edges() <= 25

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.set_title(title)

    nx.draw_networkx_nodes(G, pos, node_size=node_size, node_color="#f8f2dc", edgecolors="#2b2b2b", ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=font_size, ax=ax)

    normal = [e for e in G.edges() if normalize_edge(e) not in highlighted]
    _draw_edges(G, pos, normal, ax, edge_color="#b0b0b0", width=1.0)
    _draw_edges(G, pos, path_edges, ax, edge_color="#2ca02c", width=4)
    _draw_edges(G, pos, protected, ax, edge_color="#1f77b4", width=4)
    _draw_edges(G, pos, attacked, ax, edge_color="#d62728", width=3, style="dashed")

    if show_weights:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "weight"), font_size=font_size, ax=ax)

    ax.set_aspect("equal")
    ax.margins(0.12)
    ax.axis("off")
    return fig


def main():
    st.set_page_config(page_title="Network Interdiction Demo", layout="wide")
    st.title("Network Defense / Network Interdiction Game")
    st.write("A defender protects edges, an attacker raises the cost of unprotected attacked edges, and we compare shortest paths before and after the attack.")

    with st.sidebar:
        st.header("Simulation settings")
        graph_model = st.selectbox("Graph model", list(GRAPH_GENERATORS))
        node_count = st.slider("Number of nodes", 4, 20, 8)
        edge_probability = st.slider("Edge density", 0.2, 1.0, 0.35, 0.05, help="Drives each model: edge probability, attachment, edge count or radius.")
        seed = int(st.number_input("Random seed", min_value=0, value=7, step=1))
        source = st.selectbox("Source node", list(range(node_count)), index=0)
        target_options = [n for n in range(node_count) if n != source]
        target = st.selectbox("Target node", target_options, index=len(target_options) - 1)
        attack_budget = st.slider("Attack budget", 1, 8, 2)
        defense_budget = st.slider("Defense budget", 0, 8, 2)
        attack_multiplier = st.slider("Attack multiplier", 1.0, 10.0, 5.0, 0.5)
        attacker_name = st.selectbox("Attacker strategy", list(ATTACKERS))
        defender_name = st.selectbox("Defender strategy", list(DEFENDERS))

    params = SimpleNamespace(node_count=node_count, edge_probability=edge_probability, seed=seed, attack_budget=attack_budget, defense_budget=defense_budget, attack_multiplier=attack_multiplier)

    G = GRAPH_GENERATORS[graph_model](params)
    defender = DEFENDERS[defender_name](params)
    protected_edges = defender.select_edges(G, source, target) if defender else []

    attacker = ATTACKERS[attacker_name](params)
    result = run_simulation(G, source, target, attacker, protected_edges=protected_edges, attack_multiplier=attack_multiplier)
    attacked_graph = apply_attack(G, result["attacked_edges"], protected_edges, attack_multiplier)

    pos = compute_layout(G, seed)
    left, right = st.columns(2)
    with left:
        st.pyplot(draw_graph(G, pos, "Before attack", protected_edges=protected_edges, shortest_path=result["baseline_path"]))
    with right:
        st.pyplot(draw_graph(attacked_graph, pos, "After attack", protected_edges=protected_edges, attacked_edges=result["attacked_edges"], shortest_path=result["attacked_path"]))

    rows = [("Baseline distance", result["baseline_length"]), ("Attacked distance", result["attacked_length"]), ("Damage", result["damage"]), ("Damage ratio", result["damage_ratio"])]
    st.subheader("Results")
    st.dataframe(pd.DataFrame([{"Metric": m, "Value": v} for m, v in rows]), hide_index=True, use_container_width=True)
    st.write(f"Baseline shortest path: `{result['baseline_path']}`")
    st.write(f"Attacked shortest path: `{result['attacked_path']}`")
    st.write(f"Protected edges: `{result['protected_edges']}`")
    st.write(f"Attacked edges: `{result['attacked_edges']}`")


if __name__ == "__main__":
    main()