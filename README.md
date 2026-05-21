# Network Defense / Network Interdiction Game

This is a small Python project for a Discrete Optimization course. The project
models a weighted network where a defender protects some edges and an attacker
tries to make the shortest path from a source node to a target node more
expensive.

The main goal is not to build a perfect real-world security model. The goal is
to show the idea of network interdiction in a simple and visual way.

## What The Program Does

The graph is undirected and every edge has a weight. At the start there is a
shortest path from source `s` to target `t`.

In each simulation or game round:

1. The defender chooses edges to protect.
2. The attacker chooses edges to attack.
3. If an attacked edge is protected, nothing happens to that edge.
4. If an attacked edge is not protected, its weight is multiplied by the attack
   multiplier.
5. The program computes the new shortest path and compares it with the old one.

The attacker wants the shortest path distance to increase. The defender wants
to keep the shortest path distance as small as possible.

## Main Features

- Weighted undirected graph utilities.
- Three attacker strategies:
  - Random attacker
  - Shortest-path attacker
  - Greedy attacker
- Defender strategies used for the game/demo:
  - None
  - Random defender
  - Centrality defender
  - Greedy defender
- Single-run command line demo.
- Interactive Streamlit UI.
- Multi-round game mode.
- Presentation mode that plays rounds automatically.
- Batch experiments for statistics.
- Plot generation for experiment results.

## Project Structure

```text
.
├── app.py                         # Streamlit user interface
├── main.py                        # Simple command-line demo
├── requirements.txt               # Python dependencies
├── docs/
│   └── user_documentation.md      # More detailed user guide
├── src/
│   ├── graph_utils.py             # Helper functions for graph operations
│   ├── graph_generator.py         # Random graph models
│   ├── game.py                    # Multi-round game logic
│   ├── metrics.py                 # Damage and summary metrics
│   ├── registry.py                # Strategy and graph registries
│   ├── simulation.py              # One-round simulation logic
│   ├── attacker/                  # Attacker strategies
│   ├── defender/                  # Defender strategies
│   └── experiments/               # Statistics scripts
└── report/
    └── notes.md
```

## Installation

Use Python 3.12 if possible.

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If NumPy or Matplotlib gives a binary architecture error on macOS, recreate the
virtual environment and reinstall the requirements. This usually happens when
an `arm64` package is installed into an `x86_64` Python environment, or the
other way around.

## Run The Command-Line Demo

```bash
python3 main.py
```

This runs a small manually defined graph and prints the results for the
attacker strategies.

## Run The Streamlit App

```bash
streamlit run app.py
```

If `streamlit` is not found, use:

```bash
python -m streamlit run app.py
```

The app lets the user choose the graph model, number of nodes, density, source,
target, budgets, multiplier, attacker strategy, defender strategy, and number
of rounds.

## Run Statistics

Quick smoke test:

```bash
python3 -B src/experiments/run_batch.py --preset smoke
```

Analyze the results:

```bash
python3 -B src/experiments/analyze_results.py --input src/experiments/results/smoke_results.csv --threshold 1.5
```

Create graphs from the results:

```bash
python3 -B src/experiments/plotting.py --input src/experiments/results/smoke_results.csv --threshold 1.5
```

The generated statistics files are saved in:

```text
src/experiments/results/
src/experiments/figures/
```

## Basic Testing

Check that the Python files compile:

```bash
python3 -B -c "import pathlib; files=[pathlib.Path('main.py'), pathlib.Path('app.py')] + list(pathlib.Path('src').rglob('*.py')); [compile(path.read_text(), str(path), 'exec') for path in files]; print('syntax ok')"
```

Run a small experiment:

```bash
python3 -B src/experiments/run_batch.py --preset smoke --limit 5
```

Run the UI:

```bash
streamlit run app.py
```

## Notes For Git

Do not commit virtual environments or cache files:

```text
.venv/
venv/
__pycache__/
*.pyc
```

Before committing, check the status:

```bash
git status
```

Add only project files:

```bash
git add README.md docs app.py main.py requirements.txt src report
git commit -m "Add network interdiction game documentation"
```

## Current Limitations

- The model is simplified for a course project.
- The greedy strategies are understandable but not optimized for very large
  graphs.
- Batch experiments can become slow because they run many graph and strategy
  combinations.
- The defender strategies are included for the game demo, but the main focus of
  this part of the project is graph utilities, attackers, simulation logic,
  statistics, and UI.
