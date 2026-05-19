"""Streamlit UI for one network interdiction simulation."""

import random

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

from src.attacker.greedy_attacker import GreedyAttacker
from src.attacker.random_attacker import RandomAttacker
from src.attacker.shortest_path_attacker import ShortestPathAttacker
from src.graph_utils import apply_attack, edge_set, edges_from_path, normalize_edge
from src.simulation import run_simulation


def generate_connected_graph(node_count, edge_probability, seed):
    """Generate a connected random weighted graph."""
    rng = random.Random(seed)

    for attempt in range(100):
        G = nx.gnp_random_graph(
            node_count,
            edge_probability,
            seed=seed + attempt,
        )
        if nx.is_connected(G):
            break
    else:
        # Fallback: a path guarantees connectivity, then random extra edges.
        G = nx.path_graph(node_count)
        for u in range(node_count):
            for v in range(u + 2, node_count):
                if rng.random() < edge_probability:
                    G.add_edge(u, v)

    for u, v in G.edges():
        G[u][v]["weight"] = rng.randint(1, 10)
    return G


def make_attacker(name, budget, attack_multiplier):
    """Create an attacker strategy from the UI selection."""
    if name == "Random":
        return RandomAttacker(budget)
    if name == "Shortest path":
        return ShortestPathAttacker(budget)
    return GreedyAttacker(budget, attack_multiplier)


def draw_graph(
    G,
    pos,
    title,
    protected_edges=None,
    attacked_edges=None,
    shortest_path=None,
):
    """Draw graph with protected, attacked, and shortest-path edges highlighted."""
    protected = edge_set(protected_edges)
    attacked = edge_set(attacked_edges)
    path_edges = set(edges_from_path(shortest_path))

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.set_title(title)

    nx.draw_networkx_nodes(G, pos, node_color="#f8f2dc", edgecolors="#2b2b2b", ax=ax)
    nx.draw_networkx_labels(G, pos, ax=ax)

    normal_edges = []
    for edge in G.edges():
        normalized = normalize_edge(edge)
        if normalized not in protected and normalized not in attacked and normalized not in path_edges:
            normal_edges.append(edge)
    nx.draw_networkx_edges(G, pos, edgelist=normal_edges, edge_color="#b0b0b0", ax=ax)

    if path_edges:
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=list(path_edges),
            edge_color="#2ca02c",
            width=4,
            ax=ax,
        )
    if protected:
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=list(protected),
            edge_color="#1f77b4",
            width=4,
            ax=ax,
        )
    if attacked:
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=list(attacked),
            edge_color="#d62728",
            width=3,
            style="dashed",
            ax=ax,
        )

    labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, ax=ax)
    ax.axis("off")
    return fig


def format_edge(edge):
    """Human-readable edge label for the multiselect widget."""
    u, v = edge
    return f"{u} - {v}"


def main():
    st.set_page_config(page_title="Network Interdiction Demo", layout="wide")
    st.title("Network Defense / Network Interdiction Game")
    st.write(
        "A defender protects selected edges, an attacker increases the cost of "
        "unprotected attacked edges, and we compare shortest paths before and "
        "after the attack."
    )

    with st.sidebar:
        st.header("Simulation settings")
        node_count = st.slider("Number of nodes", 4, 20, 8)
        edge_probability = st.slider("Edge probability", 0.2, 1.0, 0.35, 0.05)
        seed = st.number_input("Random seed", min_value=0, value=7, step=1)
        source = st.selectbox("Source node", list(range(node_count)), index=0)
        target_options = [node for node in range(node_count) if node != source]
        target = st.selectbox("Target node", target_options, index=len(target_options) - 1)
        attack_budget = st.slider("Attack budget", 1, 8, 2)
        attack_multiplier = st.slider("Attack multiplier", 1.0, 10.0, 5.0, 0.5)
        strategy = st.selectbox("Attacker strategy", ["Random", "Shortest path", "Greedy"])

    G = generate_connected_graph(node_count, edge_probability, int(seed))
    sorted_edges = sorted(edge_set(G.edges()))
    edge_labels = {format_edge(edge): edge for edge in sorted_edges}

    default_protected = []
    baseline_path = nx.shortest_path(G, source=source, target=target, weight="weight")
    for edge in edges_from_path(baseline_path)[:1]:
        default_protected.append(format_edge(edge))

    selected_labels = st.multiselect(
        "Protected edges",
        list(edge_labels.keys()),
        default=default_protected,
        help="This is a simple placeholder for the defender decision.",
    )
    protected_edges = [edge_labels[label] for label in selected_labels]

    attacker = make_attacker(strategy, attack_budget, attack_multiplier)
    result = run_simulation(
        G,
        source,
        target,
        attacker,
        protected_edges=protected_edges,
        attack_multiplier=attack_multiplier,
    )
    attacked_graph = apply_attack(
        G,
        result["attacked_edges"],
        protected_edges,
        attack_multiplier,
    )

    pos = nx.spring_layout(G, seed=int(seed))
    left, right = st.columns(2)
    with left:
        st.pyplot(
            draw_graph(
                G,
                pos,
                "Before attack",
                protected_edges=protected_edges,
                shortest_path=result["baseline_path"],
            )
        )
    with right:
        st.pyplot(
            draw_graph(
                attacked_graph,
                pos,
                "After attack",
                protected_edges=protected_edges,
                attacked_edges=result["attacked_edges"],
                shortest_path=result["attacked_path"],
            )
        )

    metrics = pd.DataFrame(
        [
            {"Metric": "Baseline distance", "Value": result["baseline_length"]},
            {"Metric": "Attacked distance", "Value": result["attacked_length"]},
            {"Metric": "Damage", "Value": result["damage"]},
            {"Metric": "Damage ratio", "Value": result["damage_ratio"]},
        ]
    )
    st.subheader("Results")
    st.dataframe(metrics, hide_index=True, use_container_width=True)
    st.write(f"Baseline shortest path: `{result['baseline_path']}`")
    st.write(f"Attacked shortest path: `{result['attacked_path']}`")
    st.write(f"Protected edges: `{result['protected_edges']}`")
    st.write(f"Attacked edges: `{result['attacked_edges']}`")


if __name__ == "__main__":
    main()
