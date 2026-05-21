"""Create report-ready plots from experiment CSV files.

Run after generating results:

    python3 -B src/experiments/run_batch.py --preset smoke
    python3 -B src/experiments/plotting.py --input src/experiments/results/smoke_results.csv
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None


RESULTS_DIR = Path(__file__).parent / "results"
FIGURES_DIR = Path(__file__).parent / "figures"

NUMERIC_FIELDS = {
    "seed",
    "nodes",
    "edges",
    "actual_density",
    "density_parameter",
    "attack_budget",
    "defense_budget",
    "attack_multiplier",
    "rounds_requested",
    "rounds_played",
    "initial_length",
    "final_length",
    "total_damage",
    "mean_round_damage",
    "max_round_damage",
    "mean_damage_ratio",
    "final_damage_ratio",
    "total_attacked_edges",
    "unique_attacked_edges",
    "mean_protected_edges",
    "runtime_seconds",
    "edge_connectivity",
    "shortest_path_count",
    "shortest_path_edge_count",
    "bridge_count",
    "betweenness_concentration",
    "alternative_path_ratio",
}


def load_results(path, threshold):
    """Load raw CSV rows and add a winner label."""
    rows = []
    with Path(path).open() as file:
        for row in csv.DictReader(file):
            for field in NUMERIC_FIELDS:
                row[field] = float(row[field])
            row["winner"] = (
                "Attacker"
                if row["final_damage_ratio"] >= threshold
                else "Defender"
            )
            rows.append(row)
    return rows


def unique_values(rows, field):
    """Return sorted unique values for a field."""
    return sorted({row[field] for row in rows})


def mean(values):
    """Small local mean helper to avoid a dependency."""
    return sum(values) / len(values) if values else 0


def grouped_mean(rows, group_fields, value_field):
    """Return {group_tuple: mean(value_field)}."""
    values = defaultdict(list)
    for row in rows:
        key = tuple(row[field] for field in group_fields)
        values[key].append(row[value_field])
    return {key: mean(items) for key, items in values.items()}


def grouped_attacker_win_rate(rows, group_fields):
    """Return {group_tuple: attacker win rate}."""
    values = defaultdict(list)
    for row in rows:
        key = tuple(row[field] for field in group_fields)
        values[key].append(1 if row["winner"] == "Attacker" else 0)
    return {key: mean(items) for key, items in values.items()}


def save_grouped_bar(rows, x_field, series_field, value_field, output, title, ylabel):
    """Grouped bar chart for mean metric values."""
    x_values = unique_values(rows, x_field)
    series_values = unique_values(rows, series_field)
    grouped = grouped_mean(rows, [x_field, series_field], value_field)

    width = 0.8 / max(1, len(series_values))
    fig, ax = plt.subplots(figsize=(10, 5.5))
    positions = list(range(len(x_values)))

    for index, series in enumerate(series_values):
        offsets = [pos + index * width for pos in positions]
        values = [grouped.get((x, series), 0) for x in x_values]
        ax.bar(offsets, values, width=width, edgecolor="#2b2b2b", label=series)

    ax.set_xticks(
        [pos + width * (len(series_values) - 1) / 2 for pos in positions],
        x_values,
        rotation=20,
        ha="right",
    )
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(title=series_field.replace("_", " ").title())
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def save_win_rate_bar(rows, x_field, output, title):
    """Single bar chart of attacker win rate."""
    x_values = unique_values(rows, x_field)
    grouped = grouped_attacker_win_rate(rows, [x_field])
    values = [grouped.get((x,), 0) for x in x_values]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x_values, values, color="#d62728", edgecolor="#2b2b2b")
    ax.axhline(0.5, color="#111111", linestyle="--", linewidth=1)
    ax.set_ylim(0, 1)
    ax.set_title(title)
    ax.set_ylabel("Attacker win rate")
    ax.grid(axis="y", alpha=0.25)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def save_heatmap(rows, row_field, col_field, metric, output, title, color_label):
    """Heatmap for pairwise strategy or budget comparisons."""
    row_values = unique_values(rows, row_field)
    col_values = unique_values(rows, col_field)
    if metric == "attacker_win_rate":
        grouped = grouped_attacker_win_rate(rows, [row_field, col_field])
    else:
        grouped = grouped_mean(rows, [row_field, col_field], metric)

    matrix = [
        [grouped.get((row, col), 0) for col in col_values]
        for row in row_values
    ]

    fig, ax = plt.subplots(figsize=(8, 5.5))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(col_values)), col_values, rotation=20, ha="right")
    ax.set_yticks(range(len(row_values)), row_values)
    ax.set_title(title)

    for row_index, row in enumerate(row_values):
        for col_index, _ in enumerate(col_values):
            value = matrix[row_index][col_index]
            label = f"{value:.0%}" if metric == "attacker_win_rate" else f"{value:.2f}"
            ax.text(col_index, row_index, label, ha="center", va="center", fontsize=8)

    fig.colorbar(im, ax=ax, shrink=0.82, label=color_label)
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def save_line_by_group(rows, x_field, series_field, value_field, output, title, ylabel):
    """Line chart for trends across numeric settings."""
    x_values = unique_values(rows, x_field)
    series_values = unique_values(rows, series_field)
    grouped = grouped_mean(rows, [x_field, series_field], value_field)

    fig, ax = plt.subplots(figsize=(9, 5))
    for series in series_values:
        values = [grouped.get((x, series), 0) for x in x_values]
        ax.plot(x_values, values, marker="o", linewidth=2, label=series)

    ax.set_title(title)
    ax.set_xlabel(x_field.replace("_", " ").title())
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)
    ax.legend(title=series_field.replace("_", " ").title())
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def save_all_figures(rows, figures_dir):
    """Generate the main report figures."""
    figures_dir.mkdir(exist_ok=True)

    save_win_rate_bar(
        rows,
        "graph",
        figures_dir / "01_attacker_win_rate_by_graph.png",
        "Attacker Win Rate by Graph Type",
    )
    save_win_rate_bar(
        rows,
        "defender",
        figures_dir / "02_attacker_win_rate_by_defender.png",
        "Attacker Win Rate by Defender Strategy",
    )
    save_grouped_bar(
        rows,
        "defender",
        "attacker",
        "total_damage",
        figures_dir / "03_total_damage_by_strategy.png",
        "Mean Total Damage by Strategy Matchup",
        "Mean total damage",
    )
    save_heatmap(
        rows,
        "defender",
        "attacker",
        "attacker_win_rate",
        figures_dir / "04_strategy_win_rate_heatmap.png",
        "Attacker Win Rate by Strategy Matchup",
        "Attacker win rate",
    )
    save_heatmap(
        rows,
        "defender",
        "attacker",
        "final_damage_ratio",
        figures_dir / "05_strategy_damage_ratio_heatmap.png",
        "Final Damage Ratio by Strategy Matchup",
        "Mean final damage ratio",
    )
    save_line_by_group(
        rows,
        "nodes",
        "defender",
        "final_damage_ratio",
        figures_dir / "06_damage_ratio_by_nodes.png",
        "Final Damage Ratio by Number of Nodes",
        "Mean final damage ratio",
    )
    save_line_by_group(
        rows,
        "edges",
        "defender",
        "final_damage_ratio",
        figures_dir / "07_damage_ratio_by_edges.png",
        "Final Damage Ratio by Number of Edges",
        "Mean final damage ratio",
    )
    save_heatmap(
        rows,
        "defense_budget",
        "attack_budget",
        "attacker_win_rate",
        figures_dir / "08_budget_win_rate_heatmap.png",
        "Attacker Win Rate by Attack/Defense Budget",
        "Attacker win rate",
    )
    save_line_by_group(
        rows,
        "attack_multiplier",
        "attacker",
        "total_damage",
        figures_dir / "09_damage_by_multiplier.png",
        "Total Damage by Attack Multiplier",
        "Mean total damage",
    )
    save_grouped_bar(
        rows,
        "graph",
        "attacker",
        "final_damage_ratio",
        figures_dir / "10_damage_ratio_by_graph_attacker.png",
        "Final Damage Ratio by Graph and Attacker",
        "Mean final damage ratio",
    )


def svg_text(x, y, text, size=12, anchor="middle", weight="normal", rotate=None):
    """Return an SVG text element."""
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate else ""
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
        f'font-family="Arial" font-weight="{weight}"{transform}>{text}</text>'
    )


def save_svg_bar(labels, values, output, title, ylabel, value_as_percent=False):
    """Dependency-free SVG bar chart."""
    width, height = 1000, 620
    left, right, top, bottom = 90, 30, 70, 150
    plot_w = width - left - right
    plot_h = height - top - bottom
    max_value = max(values) if values else 1
    if value_as_percent:
        max_value = max(1, max_value)
    max_value = max(max_value, 0.001)
    bar_w = plot_w / max(1, len(values)) * 0.72

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        svg_text(width / 2, 32, title, size=20, weight="bold"),
        svg_text(22, height / 2, ylabel, size=13, rotate=-90),
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#333"/>',
    ]

    for i in range(6):
        value = max_value * i / 5
        y = top + plot_h - (value / max_value) * plot_h
        label = f"{value:.0%}" if value_as_percent else f"{value:.1f}"
        parts.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#eee"/>')
        parts.append(svg_text(left - 10, y + 4, label, size=11, anchor="end"))

    for index, (label, value) in enumerate(zip(labels, values)):
        x = left + (index + 0.5) * plot_w / len(values) - bar_w / 2
        h = (value / max_value) * plot_h
        y = top + plot_h - h
        shown = f"{value:.0%}" if value_as_percent else f"{value:.2f}"
        parts.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" fill="#d95f02" stroke="#222"/>')
        parts.append(svg_text(x + bar_w / 2, y - 8, shown, size=11))
        parts.append(svg_text(x + bar_w / 2, top + plot_h + 28, label, size=11, rotate=-30))

    parts.append("</svg>")
    Path(output).write_text("\n".join(parts))


def save_svg_heatmap(row_labels, col_labels, matrix, output, title, value_as_percent=False):
    """Dependency-free SVG heatmap."""
    cell_w, cell_h = 130, 58
    left, top = 190, 90
    width = left + cell_w * len(col_labels) + 60
    height = top + cell_h * len(row_labels) + 80
    flat = [value for row in matrix for value in row]
    max_value = max(flat) if flat else 1
    min_value = min(flat) if flat else 0
    span = max(max_value - min_value, 0.001)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        svg_text(width / 2, 32, title, size=20, weight="bold"),
    ]

    for col, label in enumerate(col_labels):
        parts.append(svg_text(left + col * cell_w + cell_w / 2, top - 18, label, size=11, rotate=-20))

    for row, label in enumerate(row_labels):
        parts.append(svg_text(left - 10, top + row * cell_h + cell_h / 2 + 4, label, size=12, anchor="end"))
        for col, _ in enumerate(col_labels):
            value = matrix[row][col]
            intensity = int(245 - 170 * ((value - min_value) / span))
            color = f"rgb(255,{intensity},{intensity})"
            x = left + col * cell_w
            y = top + row * cell_h
            shown = f"{value:.0%}" if value_as_percent else f"{value:.2f}"
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{color}" stroke="#444"/>')
            parts.append(svg_text(x + cell_w / 2, y + cell_h / 2 + 4, shown, size=12, weight="bold"))

    parts.append("</svg>")
    Path(output).write_text("\n".join(parts))


def save_svg_line(rows, x_field, series_field, value_field, output, title, ylabel):
    """Dependency-free line chart."""
    x_values = unique_values(rows, x_field)
    series_values = unique_values(rows, series_field)
    grouped = grouped_mean(rows, [x_field, series_field], value_field)
    all_values = [grouped.get((x, s), 0) for x in x_values for s in series_values]
    max_value = max(all_values) if all_values else 1
    max_value = max(max_value, 0.001)

    width, height = 1000, 620
    left, right, top, bottom = 90, 180, 70, 90
    plot_w = width - left - right
    plot_h = height - top - bottom
    colors = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e"]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        svg_text(width / 2, 32, title, size=20, weight="bold"),
        svg_text(22, height / 2, ylabel, size=13, rotate=-90),
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#333"/>',
    ]

    for index, x_value in enumerate(x_values):
        x = left + index * plot_w / max(1, len(x_values) - 1)
        parts.append(svg_text(x, top + plot_h + 28, str(int(x_value) if float(x_value).is_integer() else x_value), size=11))

    for series_index, series in enumerate(series_values):
        color = colors[series_index % len(colors)]
        points = []
        for index, x_value in enumerate(x_values):
            x = left + index * plot_w / max(1, len(x_values) - 1)
            value = grouped.get((x_value, series), 0)
            y = top + plot_h - (value / max_value) * plot_h
            points.append((x, y))
            parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')
        point_text = " ".join(f"{x},{y}" for x, y in points)
        parts.append(f'<polyline points="{point_text}" fill="none" stroke="{color}" stroke-width="3"/>')
        legend_y = top + 24 * series_index
        parts.append(f'<rect x="{left + plot_w + 30}" y="{legend_y - 11}" width="14" height="14" fill="{color}"/>')
        parts.append(svg_text(left + plot_w + 52, legend_y, series, size=12, anchor="start"))

    parts.append("</svg>")
    Path(output).write_text("\n".join(parts))


def save_all_svg_figures(rows, figures_dir):
    """Generate useful SVG figures without Matplotlib."""
    figures_dir.mkdir(exist_ok=True)

    graph_win = grouped_attacker_win_rate(rows, ["graph"])
    graph_labels = unique_values(rows, "graph")
    save_svg_bar(
        graph_labels,
        [graph_win.get((graph,), 0) for graph in graph_labels],
        figures_dir / "01_attacker_win_rate_by_graph.svg",
        "Attacker Win Rate by Graph Type",
        "Attacker win rate",
        value_as_percent=True,
    )

    defender_win = grouped_attacker_win_rate(rows, ["defender"])
    defender_labels = unique_values(rows, "defender")
    save_svg_bar(
        defender_labels,
        [defender_win.get((defender,), 0) for defender in defender_labels],
        figures_dir / "02_attacker_win_rate_by_defender.svg",
        "Attacker Win Rate by Defender Strategy",
        "Attacker win rate",
        value_as_percent=True,
    )

    defenders = unique_values(rows, "defender")
    attackers = unique_values(rows, "attacker")
    matchup_win = grouped_attacker_win_rate(rows, ["defender", "attacker"])
    save_svg_heatmap(
        defenders,
        attackers,
        [[matchup_win.get((d, a), 0) for a in attackers] for d in defenders],
        figures_dir / "03_strategy_win_rate_heatmap.svg",
        "Attacker Win Rate by Strategy Matchup",
        value_as_percent=True,
    )

    ratio = grouped_mean(rows, ["defender", "attacker"], "final_damage_ratio")
    save_svg_heatmap(
        defenders,
        attackers,
        [[ratio.get((d, a), 0) for a in attackers] for d in defenders],
        figures_dir / "04_strategy_damage_ratio_heatmap.svg",
        "Final Damage Ratio by Strategy Matchup",
    )

    save_svg_line(
        rows,
        "nodes",
        "defender",
        "final_damage_ratio",
        figures_dir / "05_damage_ratio_by_nodes.svg",
        "Final Damage Ratio by Number of Nodes",
        "Mean final damage ratio",
    )

    save_svg_line(
        rows,
        "edges",
        "defender",
        "final_damage_ratio",
        figures_dir / "06_damage_ratio_by_edges.svg",
        "Final Damage Ratio by Number of Edges",
        "Mean final damage ratio",
    )


def main():
    parser = argparse.ArgumentParser(description="Create report-ready plots from sweep results.")
    parser.add_argument(
        "--input",
        default=str(RESULTS_DIR / "smoke_results.csv"),
        help="Raw results CSV from run_batch.py.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1.5,
        help="Attacker wins if final_damage_ratio is at least this value.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(FIGURES_DIR),
        help="Directory where figures should be saved.",
    )
    args = parser.parse_args()

    rows = load_results(args.input, args.threshold)
    if plt is None:
        save_all_svg_figures(rows, Path(args.output_dir))
        print(f"Matplotlib is unavailable; saved SVG figures to {args.output_dir}")
    else:
        save_all_figures(rows, Path(args.output_dir))
        print(f"Saved {10} PNG figures to {args.output_dir}")


if __name__ == "__main__":
    main()
