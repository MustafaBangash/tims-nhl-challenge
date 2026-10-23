# Tim's NHL Challenge

A small Python command-line tool that ranks the players in each Tim Hortons NHL
Challenge category by their current regular-season goals per game (G/GP), then
recommends the highest-ranked player.

It uses the NHL's public JSON endpoints and needs no API key or third-party
Python packages.

## Requirements

- Python 3.10 or newer
- An internet connection while fetching player statistics

## Run it

From this project directory:

```bash
python3 tims_nhl.py
```

The interactive version asks for exactly three categories. Enter the player
names for each category on one line, separated by commas:

```text
Category 1: Connor McDavid, Auston Matthews, Nathan MacKinnon
Category 2: Leon Draisaitl, David Pastrnak, Kyle Connor
Category 3: William Nylander, Jack Hughes, Kirill Kaprizov
```

After you submit Category 3, the program immediately fetches the current NHL
statistics, ranks the players in each category, and prints one recommendation
per category. You do not need to enter a blank line or a fourth category.

Example result:

```text
Category 1
-------------------------------------------------------------------
Rank  Player                     Team      GP    G     G/GP
1     Connor McDavid             EDM       10    8    0.800
2     Auston Matthews            TOR       12    8    0.667
3     Nathan MacKinnon           COL       10    6    0.600

Recommendation: Connor McDavid (8 goals in 10 games; 0.800 G/GP)
```

You can also provide all categories in one command:

```bash
python3 tims_nhl.py \
  --category "Connor McDavid,Auston Matthews,Nathan MacKinnon" \
  --category "Leon Draisaitl,David Pastrnak,Kyle Connor" \
  --category "William Nylander,Jack Hughes,Kirill Kaprizov"
```

## Optional installation

Installing in an isolated environment gives you the shorter `tims-nhl` command:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
tims-nhl
```

## How the recommendation works

For every entered name, the tool:

1. Resolves the name through the NHL player-search service.
2. Fetches that player's current-season regular-season totals.
3. Calculates `goals / games played`.
4. Sorts each category by G/GP, then total goals, then games played.

This is a simple historical-rate recommendation. It does not account for the
day's opponent, starting goalie, injuries, line combinations, or recent form,
so it cannot guarantee that a player will score in the next game.

## Run tests

The test suite uses Python's built-in `unittest` runner and does not call the NHL API:

```bash
python3 -m unittest discover -s tests -v
```

## Data sources

- Player search: `https://search.d3.nhle.com/api/v1/search/player`
- Player statistics: `https://api-web.nhle.com/v1/player/{playerId}/landing`

These public endpoints do not require an API key, but the NHL does not publish a
formal stability guarantee for them.
