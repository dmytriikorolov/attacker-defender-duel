"""Streamlit UI for one network interdiction simulation."""
 
import random
from types import SimpleNamespace
 
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st
 
from src.attacker.greedy_attacker import GreedyAttacker
from src.attacker.random_attacker import RandomAttacker
from src.attacker.shortest_path_attacker import ShortestPathAttacker
from src.defender.centrality_defender import CentralityDefender
from src.defender.greedy_defender import GreedyDefender
from src.defender.random_defender import RandomDefender
from src.graph_utils import apply_attack, edge_set, edges_from_path, normalize_edge
from src.simulation import run_simulation
 
# name -> factory(params). Adding a strategy = one line here, no UI changes.
ATTACKERS = {
    "Random": lambda p: RandomAttacker(p.attack_budget),
    "Shortest path": lambda p: ShortestPathAttacker(p.attack_budget),
    "Greedy": lambda p: GreedyAttacker(p.attack_budget, p.attack_multiplier),
}
DEFENDERS = {
    "None": lambda p: None,
    "Random": lambda p: RandomDefender(p.defense_budget),
    "Centrality": lambda p: CentralityDefender(p.defense_budget),
    "Greedy": lambda p: GreedyDefender(p.defense_budget, p.attack_budget, p.attack_multiplier),
}
 
 
def generate_connected_graph(node_count, edge_probability, seed):
    """Generate a connected random weighted graph."""
    rng = random.Random(seed)
    for attempt in range(100):
        G = nx.gnp_random_graph(node_count, edge_probability, seed=seed + attempt)
        if nx.is_connected(G):
            break
    else:
        G = nx.path_graph(node_count)
        for u in range(node_count):
            for v in range(u + 2, node_count):
                if rng.random() < edge_probability:
                    G.add_edge(u, v)
    for u, v in G.edges():
        G[u][v]["weight"] = rng.randint(1, 10)
    return G
 
 
def _draw_edges(G, pos, edges, ax, **style):
    """Draw one highlighted edge layer (skips empty layers)."""
    if edges:
        nx.draw_networkx_edges(G, pos, edgelist=list(edges), ax=ax, **style)
 
 
def draw_graph(G, pos, title, protected_edges=None, attacked_edges=None, shortest_path=None):
    """Draw graph with protected, attacked, and shortest-path edges highlighted."""
    protected, attacked = edge_set(protected_edges), edge_set(attacked_edges)
    path_edges = set(edges_from_path(shortest_path))
    highlighted = protected | attacked | path_edges
 
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.set_title(title)
    ax.axis("off")
 
    nx.draw_networkx_nodes(G, pos, node_color="#f8f2dc", edgecolors="#2b2b2b", ax=ax)
    nx.draw_networkx_labels(G, pos, ax=ax)
 
    normal = [e for e in G.edges() if normalize_edge(e) not in highlighted]
    _draw_edges(G, pos, normal, ax, edge_color="#b0b0b0")
    _draw_edges(G, pos, path_edges, ax, edge_color="#2ca02c", width=4)
    _draw_edges(G, pos, protected, ax, edge_color="#1f77b4", width=4)
    _draw_edges(G, pos, attacked, ax, edge_color="#d62728", width=3, style="dashed")
 
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "weight"), ax=ax)
    return fig
 
 
def main():
    st.set_page_config(page_title="Network Interdiction Demo", layout="wide")
    st.title("Network Defense / Network Interdiction Game")
    st.write("A defender protects edges, an attacker raises the cost of unprotected attacked edges, and we compare shortest paths before and after the attack.")
 
    with st.sidebar:
        st.header("Simulation settings")
        node_count = st.slider("Number of nodes", 4, 20, 8)
        edge_probability = st.slider("Edge probability", 0.2, 1.0, 0.35, 0.05)
        seed = int(st.number_input("Random seed", min_value=0, value=7, step=1))
        source = st.selectbox("Source node", list(range(node_count)), index=0)
        target_options = [n for n in range(node_count) if n != source]
        target = st.selectbox("Target node", target_options, index=len(target_options) - 1)
        attack_budget = st.slider("Attack budget", 1, 8, 2)
        defense_budget = st.slider("Defense budget", 0, 8, 2)
        attack_multiplier = st.slider("Attack multiplier", 1.0, 10.0, 5.0, 0.5)
        attacker_name = st.selectbox("Attacker strategy", list(ATTACKERS))
        defender_name = st.selectbox("Defender strategy", list(DEFENDERS))
 
    params = SimpleNamespace(attack_budget=attack_budget, defense_budget=defense_budget, attack_multiplier=attack_multiplier)
 
    G = generate_connected_graph(node_count, edge_probability, seed)
    defender = DEFENDERS[defender_name](params)
    protected_edges = defender.select_edges(G, source, target) if defender else []
 
    attacker = ATTACKERS[attacker_name](params)
    result = run_simulation(G, source, target, attacker, protected_edges=protected_edges, attack_multiplier=attack_multiplier)
    attacked_graph = apply_attack(G, result["attacked_edges"], protected_edges, attack_multiplier)
 
    pos = nx.spring_layout(G, seed=seed)
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
