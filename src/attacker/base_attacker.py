"""Base class for attacker strategies."""


class BaseAttacker:
    """Common interface for all attacker strategies."""

    def __init__(self, budget):
        self.budget = budget

    def select_edges(self, G, source, target, protected_edges=None):
        """Return a list of edges selected for attack."""
        raise NotImplementedError
