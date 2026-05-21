"""Regenerate experiment CSVs, analyses, and figures with one command."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.experiments import analyze_results, plotting, run_batch


def main():
    parser = argparse.ArgumentParser(description="Run the complete experiment pipeline.")
    parser.add_argument("--preset", choices=run_batch.PRESETS, default="smoke")
    parser.add_argument("--limit", type=int, help="Run only the first N games.")
    parser.add_argument("--threshold", type=float, default=1.5)
    args = parser.parse_args()

    output = run_batch.RESULTS_DIR / f"{args.preset}_results.csv"
    summary_output = output.with_name(output.stem + "_summary.csv")

    rows = run_batch.run_sweep(args.preset, limit=args.limit)
    run_batch.RESULTS_DIR.mkdir(exist_ok=True)
    run_batch.write_csv(rows, output)
    run_batch.write_csv(run_batch.summarize(rows), summary_output)

    analyzed_rows = analyze_results.add_winners(
        analyze_results.load_rows(output),
        args.threshold,
    )
    output_prefix = output.with_name(output.stem + "_analysis")
    summaries = {
        "by_graph": ["graph"],
        "by_attacker": ["attacker"],
        "by_defender": ["defender"],
        "by_matchup": ["attacker", "defender"],
        "by_graph_matchup": ["graph", "attacker", "defender"],
        "by_nodes": ["nodes"],
        "by_edges": ["edges"],
        "by_attack_budget": ["attack_budget"],
        "by_defense_budget": ["defense_budget"],
        "by_multiplier": ["attack_multiplier"],
    }
    for name, fields in summaries.items():
        path = output_prefix.with_name(f"{output_prefix.name}_{name}.csv")
        analyze_results.write_csv(
            analyze_results.summarize_by(analyzed_rows, fields),
            path,
        )

    if plotting.plt is None:
        plotting.save_all_svg_figures(
            plotting.load_results(output, args.threshold),
            plotting.FIGURES_DIR,
        )
    else:
        plotting.save_all_figures(
            plotting.load_results(output, args.threshold),
            plotting.FIGURES_DIR,
        )

    print(f"Saved raw results to {output}")
    print(f"Saved summary to {summary_output}")
    print(f"Saved analysis CSVs under {output_prefix.name}_*.csv")
    print(f"Saved figures to {plotting.FIGURES_DIR}")


if __name__ == "__main__":
    main()
