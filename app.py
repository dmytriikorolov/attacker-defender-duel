"""Streamlit UI for one network interdiction simulation."""

import time
from types import SimpleNamespace

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

from src.registry import ATTACKERS, DEFENDERS, GRAPH_GENERATORS
from src.graph_utils import edge_set, edges_from_path, normalize_edge
from src.game import play_round, total_attacker_score


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

EDGE_STYLES = {
    "normal": {"edge_color": "#b8b8b8", "width": 1.4},
    "shortest_path": {"edge_color": "#111111", "width": 5.0},
    "protected": {"edge_color": "#2ca02c", "width": 5.0},
    "protected_path_base": {"edge_color": "#111111", "width": 6.0},
    "protected_path_stripe": {"edge_color": "#2ca02c", "width": 4.0, "style": (0, (3, 3))},
    "attacked": {"edge_color": "#d62728", "width": 4.0, "style": "dashed"},
}


def make_params(
    graph_model,
    node_count,
    edge_probability,
    seed,
    attack_budget,
    defense_budget,
    attack_multiplier,
    max_rounds,
):
    """Store UI settings in one object shared by factories."""
    return SimpleNamespace(
        graph_model=graph_model,
        node_count=node_count,
        edge_probability=edge_probability,
        seed=seed,
        attack_budget=attack_budget,
        defense_budget=defense_budget,
        attack_multiplier=attack_multiplier,
        max_rounds=max_rounds,
    )


def settings_key(params, source, target, attacker_name, defender_name):
    """Return a hashable key for settings that require a game reset."""
    return (
        params.graph_model,
        params.node_count,
        params.edge_probability,
        params.seed,
        params.attack_budget,
        params.defense_budget,
        params.attack_multiplier,
        params.max_rounds,
        source,
        target,
        attacker_name,
        defender_name,
    )


def start_game(params, source, target, attacker_name, defender_name):
    """Create a new game state and store it in Streamlit session state."""
    initial_graph = GRAPH_GENERATORS[params.graph_model](params)
    st.session_state.game = {
        "initial_graph": initial_graph,
        "current_graph": initial_graph.copy(),
        "history": [],
        "source": source,
        "target": target,
        "attacker_name": attacker_name,
        "defender_name": defender_name,
        "max_rounds": params.max_rounds,
        "settings_key": settings_key(params, source, target, attacker_name, defender_name),
        "positions": nx.spring_layout(initial_graph, seed=params.seed),
        "blocked_edges": set(),
    }


def play_next_ui_round(params):
    """Advance the session-state game by one round."""
    game = st.session_state.game
    if len(game["history"]) >= game["max_rounds"]:
        return

    round_number = len(game["history"]) + 1

    defender = DEFENDERS[game["defender_name"]](params)
    protected_edges = (
        defender.select_edges(game["current_graph"], game["source"], game["target"])
        if defender
        else []
    )
    attacker = ATTACKERS[game["attacker_name"]](params)
    result = play_round(
        game["current_graph"],
        game["source"],
        game["target"],
        attacker,
        protected_edges=protected_edges,
        blocked_edges=game["blocked_edges"],
        attack_multiplier=params.attack_multiplier,
        round_number=round_number,
    )
    game["history"].append(result)
    game["current_graph"] = result["attacked_graph"]
    game["blocked_edges"].update(edge_set(result["attacked_edges"]))


def _draw_edges(G, pos, edges, ax, **style):
    """Draw one highlighted edge layer (skips empty layers)."""
    if edges:
        nx.draw_networkx_edges(G, pos, edgelist=list(edges), ax=ax, **style)


def draw_graph(G, pos, title, protected_edges=None, attacked_edges=None, shortest_path=None):
    """Draw graph with protected, attacked, and shortest-path edges highlighted."""
    protected, attacked = edge_set(protected_edges), edge_set(attacked_edges)
    path_edges = set(edges_from_path(shortest_path))
    protected_path = protected & path_edges
    path_only = path_edges - protected_path
    protected_only = protected - protected_path
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
    _draw_edges(G, pos, normal, ax, **EDGE_STYLES["normal"])
    _draw_edges(G, pos, path_only, ax, **EDGE_STYLES["shortest_path"])
    _draw_edges(G, pos, protected_only, ax, **EDGE_STYLES["protected"])
    _draw_edges(G, pos, protected_path, ax, **EDGE_STYLES["protected_path_base"])
    _draw_edges(G, pos, protected_path, ax, **EDGE_STYLES["protected_path_stripe"])
    _draw_edges(G, pos, attacked, ax, **EDGE_STYLES["attacked"])

    if show_weights:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "weight"), font_size=font_size, ax=ax)

    ax.set_aspect("equal")
    ax.margins(0.12)
    ax.axis("off")
    return fig


def edge_label(edges):
    """Format edge lists for the UI action log."""
    values = sorted(edge_set(edges))
    if not values:
        return "none"
    return ", ".join(f"{u}-{v}" for u, v in values)


def show_legend():
    """Show graph styling in text so color is not the only signal."""
    st.caption(
        "Legend: shortest path = thick black line; defended/protected edge = "
        "thick green line; protected shortest-path edge = green/black striped "
        "line; attacked edge = red dashed line; normal edge = thin gray."
    )


def show_round_action_log(result):
    """Explain exactly what happened in the last move."""
    st.subheader(f"Round {result['round']} move")
    defender_blocked = edge_set(result["protected_edges"]) & edge_set(result["attacked_edges"])
    st.markdown(
        "\n".join(
            [
                f"- Defender protected: `{edge_label(result['protected_edges'])}`",
                f"- Attacker attacked: `{edge_label(result['attacked_edges'])}`",
                f"- Attacks blocked by protection: `{edge_label(defender_blocked)}`",
                f"- Distance changed: `{result['baseline_length']} -> {result['attacked_length']}`",
                f"- Damage this round: `{result['damage']}`",
            ]
        )
    )


def main():
    st.set_page_config(page_title="Network Interdiction Demo", layout="wide")
    st.title("Network Defense / Network Interdiction Game")
    st.write(
        "Play a multi-round interdiction game. In each round the defender "
        "protects edges, the attacker attacks, and unprotected attacked edges "
        "permanently become more expensive."
    )

    with st.sidebar:
        st.header("Game settings")
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
        max_rounds = st.slider("Number of rounds", 1, 20, 5)
        presentation_mode = st.toggle(
            "Presentation mode",
            help="Automatically play one round after a short delay.",
        )
        presentation_delay = st.slider(
            "Presentation delay (seconds)",
            0.5,
            5.0,
            1.5,
            0.5,
            disabled=not presentation_mode,
        )
        attacker_name = st.selectbox("Attacker strategy", list(ATTACKERS))
        defender_name = st.selectbox(
            "Defender strategy",
            list(DEFENDERS),
            index=list(DEFENDERS).index("Centrality"),
            help="Choose None only if you want no protected edges.",
        )

    params = make_params(
        graph_model,
        node_count,
        edge_probability,
        seed,
        attack_budget,
        defense_budget,
        attack_multiplier,
        max_rounds,
    )
    current_settings_key = settings_key(
        params,
        source,
        target,
        attacker_name,
        defender_name,
    )

    if "game" not in st.session_state:
        start_game(params, source, target, attacker_name, defender_name)

    settings_changed = st.session_state.game["settings_key"] != current_settings_key

    controls = st.columns(3)
    with controls[0]:
        if st.button("Start / restart game", use_container_width=True):
            start_game(params, source, target, attacker_name, defender_name)
            settings_changed = False
    with controls[1]:
        game_complete = (
            len(st.session_state.game["history"])
            >= st.session_state.game["max_rounds"]
        )
        if st.button(
            "Play next round",
            disabled=settings_changed or game_complete,
            use_container_width=True,
        ):
            play_next_ui_round(params)
    with controls[2]:
        if st.button("Reset game", use_container_width=True):
            start_game(params, source, target, attacker_name, defender_name)
            settings_changed = False

    if settings_changed:
        st.warning("Settings changed. Start/restart the game to apply them.")

    game = st.session_state.game
    history = game["history"]
    round_count = len(history)
    active_max_rounds = game["max_rounds"]
    attacker_score = total_attacker_score(history)

    score_cols = st.columns(3)
    score_cols[0].metric("Round", f"{round_count} / {active_max_rounds}")
    score_cols[1].metric("Attacker score", attacker_score)
    score_cols[2].metric("Defender objective", "minimize score")
    if presentation_mode and not settings_changed:
        if round_count < active_max_rounds:
            st.info(f"Presentation mode is running. Next round in {presentation_delay:.1f}s.")
        else:
            st.success("Presentation mode finished all rounds.")
    show_legend()

    pos = game["positions"]
    if history:
        last = history[-1]
        show_round_action_log(last)
        left, right = st.columns(2)
        with left:
            st.pyplot(
                draw_graph(
                    last["start_graph"],
                    pos,
                    f"Round {last['round']} before attack",
                    protected_edges=last["protected_edges"],
                    shortest_path=last["baseline_path"],
                )
            )
        with right:
            st.pyplot(
                draw_graph(
                    game["current_graph"],
                    pos,
                    f"Round {last['round']} after attack",
                    protected_edges=last["protected_edges"],
                    attacked_edges=last["attacked_edges"],
                    shortest_path=last["attacked_path"],
                )
            )

        st.subheader("Last round")
        rows = [
            ("Baseline distance", last["baseline_length"]),
            ("Attacked distance", last["attacked_length"]),
            ("Damage", last["damage"]),
            ("Damage ratio", last["damage_ratio"]),
        ]
        st.dataframe(
            pd.DataFrame([{"Metric": m, "Value": v} for m, v in rows]),
            hide_index=True,
            use_container_width=True,
        )
        st.write(f"Baseline shortest path: `{last['baseline_path']}`")
        st.write(f"Attacked shortest path: `{last['attacked_path']}`")
        st.write(f"Protected edges: `{edge_label(last['protected_edges'])}`")
        st.write(f"Attacked edges: `{edge_label(last['attacked_edges'])}`")
    else:
        _, center, _ = st.columns([1, 2, 1])
        with center:
            st.pyplot(
                draw_graph(game["current_graph"], pos, "Initial graph"),
                clear_figure=True,
                use_container_width=True,
            )
        st.info("Click Play next round to start the game.")

    if history:
        st.subheader("Round history")
        history_rows = [
            {
                "Round": result["round"],
                "Protected edges": edge_label(result["protected_edges"]),
                "Attacked edges": edge_label(result["attacked_edges"]),
                "Before distance": result["baseline_length"],
                "After distance": result["attacked_length"],
                "Damage": result["damage"],
            }
            for result in history
        ]
        st.dataframe(pd.DataFrame(history_rows), hide_index=True, use_container_width=True)

    if presentation_mode and not settings_changed and round_count < active_max_rounds:
        time.sleep(presentation_delay)
        play_next_ui_round(params)
        st.rerun()


if __name__ == "__main__":
    main()
