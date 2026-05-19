"""Turn results.csv into figures.

Pure read-and-visualize: it never runs simulations, it only consumes
what run_batch produced. Two views that actually tell a story:

  1. grouped bars - mean damage_ratio per defender, split by attacker
  2. heatmap     - defender x attacker, color = mean damage_ratio

    python -m experiments.plotting
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RESULTS_CSV = Path(__file__).parent / "results.csv"
FIGURES_DIR = Path(__file__).parent / "figures"


def load_results(path=RESULTS_CSV):
    """Read the sweep output produced by run_batch."""
    return pd.read_csv(path)


def bars_by_defender(df):
    """Grouped bar chart: each defender, one bar per attacker."""
    pivot = df.pivot_table(values="damage_ratio", index="defender", columns="attacker", aggfunc="mean")
    fig, ax = plt.subplots(figsize=(8, 5))
    pivot.plot(kind="bar", ax=ax, edgecolor="#2b2b2b")
    ax.set_ylabel("Mean damage ratio (lower = better defense)")
    ax.set_title("Defender effectiveness by attacker")
    ax.legend(title="Attacker")
    fig.tight_layout()
    return fig


def heatmap_defender_attacker(df):
    """Heatmap of mean damage_ratio over the defender x attacker matrix."""
    pivot = df.pivot_table(values="damage_ratio", index="defender", columns="attacker", aggfunc="mean")
    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns, rotation=20, ha="right")
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            ax.text(j, i, f"{pivot.values[i, j]:.2f}", ha="center", va="center", fontsize=9)
    ax.set_title("Mean damage ratio: defender vs attacker")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    return fig


def main():
    df = load_results()
    FIGURES_DIR.mkdir(exist_ok=True)
    for name, builder in {"bars_by_defender": bars_by_defender, "heatmap": heatmap_defender_attacker}.items():
        path = FIGURES_DIR / f"{name}.png"
        builder(df).savefig(path, dpi=150)
        print(f"Saved {path}")


if __name__ == "__main__":
    main()