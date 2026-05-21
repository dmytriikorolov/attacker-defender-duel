"""Core behavior tests for the interdiction game."""

import unittest
from types import SimpleNamespace

import networkx as nx

from src.attacker.greedy_attacker import GreedyAttacker
from src.defender.minimax_defender import MinimaxDefender
from src.graph_utils import apply_attack, get_edge_weight
from src.metrics import compute_vulnerability_metrics
from src.mixed_strategy import run_mixed_strategy_game


def make_path_graph():
    G = nx.Graph()
    G.add_edge(0, 1, weight=2)
    G.add_edge(1, 2, weight=3)
    G.add_edge(0, 2, weight=10)
    return G


class GraphRuleTests(unittest.TestCase):
    def test_unprotected_attack_multiplies_weight(self):
        G = make_path_graph()

        attacked = apply_attack(G, [(0, 1)], [], 5)

        self.assertEqual(get_edge_weight(attacked, (0, 1)), 10)
        self.assertEqual(get_edge_weight(G, (0, 1)), 2)

    def test_protected_attack_does_not_change_weight(self):
        G = make_path_graph()

        attacked = apply_attack(G, [(0, 1)], [(1, 0)], 5)

        self.assertEqual(get_edge_weight(attacked, (0, 1)), 2)

    def test_greedy_attacker_respects_budget(self):
        G = make_path_graph()
        attacker = GreedyAttacker(budget=1, attack_multiplier=5)

        selected = attacker.select_edges(G, 0, 2)

        self.assertLessEqual(len(selected), 1)


class AdvancedStrategyTests(unittest.TestCase):
    def test_minimax_defender_protects_high_impact_edge(self):
        G = nx.Graph()
        G.add_edge(0, 1, weight=100)
        G.add_edge(1, 2, weight=1)
        G.add_edge(2, 3, weight=1)
        G.add_edge(0, 3, weight=150)

        defender = MinimaxDefender(
            budget=1,
            attacker_budget=1,
            attack_multiplier=2,
        )

        self.assertEqual(defender.select_edges(G, 0, 3), [(0, 1)])

    def test_vulnerability_metrics_describe_graph(self):
        G = make_path_graph()

        metrics = compute_vulnerability_metrics(G, 0, 2)

        self.assertEqual(metrics["edge_connectivity"], 2)
        self.assertEqual(metrics["shortest_path_count"], 1)
        self.assertEqual(metrics["shortest_path_edge_count"], 2)
        self.assertGreater(metrics["alternative_path_ratio"], 1)

    def test_mixed_strategy_game_records_strategy_choices(self):
        G = make_path_graph()
        params = SimpleNamespace(attack_budget=1, attack_multiplier=5)

        game = run_mixed_strategy_game(
            G,
            0,
            2,
            attacker_factories={"Greedy": lambda: GreedyAttacker(params.attack_budget)},
            defender_factories={"None": lambda: None},
            rounds=3,
            attack_multiplier=params.attack_multiplier,
            seed=0,
        )

        self.assertEqual(len(game["history"]), 3)
        self.assertEqual(game["attacker_strategy_counts"], {"Greedy": 3})
        self.assertEqual(game["defender_strategy_counts"], {"None": 3})
        self.assertEqual(game["history"][0]["attacker_strategy"], "Greedy")


if __name__ == "__main__":
    unittest.main()
