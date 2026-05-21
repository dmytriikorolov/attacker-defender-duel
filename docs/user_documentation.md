# User Documentation

## Project Idea

This project is a small network defense game. We have a graph where nodes are
locations and edges are connections between them. Every edge has a weight, which
can be understood as distance, cost, or travel time.

The defender protects some edges. The attacker attacks some edges. If an
attacked edge is not protected, its weight becomes larger. After that, the
program checks how much the shortest path from the source node to the target
node changed.

## Main Game Rule

The important rule is:

```text
attacked + protected edge     -> no weight change
attacked + unprotected edge   -> weight is multiplied
not attacked edge             -> no weight change
```

Example:

If an edge has weight `4` and the attack multiplier is `5`, then a successful
attack changes the weight to:

```text
4 * 5 = 20
```

## How To Start

First install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Then run the visual app:

```bash
streamlit run app.py
```

Or run the simple terminal demo:

```bash
python3 main.py
```

## Streamlit App Controls

The sidebar controls the game.

`Graph model`

Chooses what kind of graph is generated. The project currently supports:

- Erdos-Renyi random graph
- Scale-free graph
- Fixed-edge-count graph
- Geometric graph
- Grid / lattice graph

`Number of nodes`

Controls how many nodes are in the graph.

`Edge density`

Controls how many edges the graph should have. Higher density usually means
more alternative paths between the source and target.

`Random seed`

Controls random generation. If the seed is the same, the graph should be
generated the same way again.

`Source node` and `Target node`

These are the start and end nodes for the shortest path calculation.

`Attack budget`

Maximum number of edges the attacker can attack in one round.

`Defense budget`

Maximum number of edges the defender can protect in one round.

`Attack multiplier`

How much the weight of a successfully attacked edge is multiplied.

`Number of rounds`

How many rounds the iterative game should run.

`Attacker strategy`

Chooses how the attacker picks edges.

`Defender strategy`

Chooses how the defender picks protected edges. Choose `None` only if you want
to run the game without protected edges.

## Buttons

`Start / restart game`

Creates a new graph and resets the game history.

`Play next round`

Runs one round. The defender protects edges, then the attacker attacks edges,
then the graph is updated.

`Reset game`

Starts over with the current settings.

`Presentation mode`

Automatically plays rounds after a small delay. This is useful when presenting
the project because the game progresses without clicking every round manually.

## Graph Colors

The graph is drawn with colors and line styles:

- Thin gray edge: normal edge.
- Thick black edge: current shortest path.
- Thick green edge: protected edge.
- Red dashed edge: attacked edge.
- Black and green striped edge: protected edge that is also on the shortest
  path.

This was chosen so that green and blue are not confused. The red attacked edge
is also dashed, so it is not only identified by color.

## Attacker Strategies

`Random`

Chooses random edges that are not protected.

`Shortest path`

First attacks edges on the current shortest path. If the budget is not used
fully, it fills the rest randomly.

`Greedy`

Tries possible attacks and chooses the edge that gives the largest shortest
path distance after the attack. This is slower but usually stronger.

## Defender Strategies

`None`

No edges are protected.

`Random`

Protects random edges.

`Centrality`

Protects edges that are important for shortest paths. This is a simple and
reasonable defense for the demo.

`Greedy`

Tries possible protected edges and keeps the one that makes the attacker less
effective. This is slower because it simulates attacks while choosing defense.

## How Results Are Measured

`Baseline distance`

The shortest path distance before the attack in that round.

`Attacked distance`

The shortest path distance after the attack.

`Damage`

Difference between attacked distance and baseline distance:

```text
damage = attacked distance - baseline distance
```

`Damage ratio`

How many times larger the attacked distance is:

```text
damage ratio = attacked distance / baseline distance
```

If the damage ratio is high, the attacker did well. If it stays close to `1`,
the defender did well.

## Running Statistics

The experiment scripts run many games and save the results as CSV files.

Small test:

```bash
python3 -B src/experiments/run_batch.py --preset smoke
```

Only estimate how many games would run:

```bash
python3 -B src/experiments/run_batch.py --preset standard --estimate
python3 -B src/experiments/run_batch.py --preset full --estimate
```

Analyze attacker and defender wins:

```bash
python3 -B src/experiments/analyze_results.py --input src/experiments/results/smoke_results.csv --threshold 1.5
```

Generate figures:

```bash
python3 -B src/experiments/plotting.py --input src/experiments/results/smoke_results.csv --threshold 1.5
```

The main output folders are:

```text
src/experiments/results/
src/experiments/figures/
```

## How To Read The Statistics

The statistics are useful for comparing strategies.

Good defender result:

```text
damage ratio close to 1
low attacker win rate
small total damage
```

Good attacker result:

```text
large damage ratio
high attacker win rate
large total damage
```

In our analysis script, the attacker is counted as winning if the final damage
ratio is at least the selected threshold. For example, with threshold `1.5`, the
attacker wins if the final shortest path is at least 50 percent longer than at
the start.

## Common Problems

`streamlit: command not found`

Use:

```bash
python -m streamlit run app.py
```

or reinstall requirements:

```bash
python -m pip install -r requirements.txt
```

NumPy or Matplotlib binary error on macOS:

Delete and recreate the virtual environment:

```bash
deactivate
mv .venv .venv-broken
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Merge conflict markers like `<<<<<<< HEAD`:

The code cannot run while these markers exist. Resolve the merge conflict first,
then run the syntax check.

## Quick Syntax Check

```bash
python3 -B -c "import pathlib; files=[pathlib.Path('main.py'), pathlib.Path('app.py')] + list(pathlib.Path('src').rglob('*.py')); [compile(path.read_text(), str(path), 'exec') for path in files]; print('syntax ok')"
```

If it prints `syntax ok`, the files at least compile.
