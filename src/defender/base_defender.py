"""Base class for defender strategies."""


class BaseDefender:
    """Common interface for all defender strategies."""

    def __init__(self, budget):
        self.budget = budget

    def select_edges(self, G, source, target):
        """Return a list of edges the defender chooses to protect."""
        raise NotImplementedError
