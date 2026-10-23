from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from .nhl import NHLAPIError, NHLClient, PlayerStats, rank_players


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tims-nhl",
        description="Recommend Tim's NHL Challenge picks using current-season goals per game.",
    )
    parser.add_argument(
        "-c",
        "--category",
        action="append",
        metavar="PLAYER,PLAYER,...",
        help="Players in one category. Repeat this option for each category.",
    )
    return parser


def parse_category(value: str) -> list[str]:
    names = [name.strip() for name in value.split(",") if name.strip()]
    if not names:
        raise ValueError("A category must contain at least one player.")
    return names


def prompt_for_categories() -> list[list[str]]:
    print("Enter the players shown in each Tim's NHL Challenge category.")
    print("Separate names with commas. The rankings begin after Category 3.\n")
    categories: list[list[str]] = []
    for category_number in range(1, 4):
        value = input(f"Category {category_number}: ").strip()
        while not value:
            print("Please enter at least one player.")
            value = input(f"Category {category_number}: ").strip()
        categories.append(parse_category(value))
    return categories


def fetch_all(client: NHLClient, categories: list[list[str]]) -> tuple[dict[str, PlayerStats], dict[str, str]]:
    unique_names = list(dict.fromkeys(name for category in categories for name in category))
    results: dict[str, PlayerStats] = {}
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=min(8, len(unique_names))) as pool:
        pending = {pool.submit(client.get_player_stats, name): name for name in unique_names}
        for future in as_completed(pending):
            name = pending[future]
            try:
                results[name] = future.result()
            except NHLAPIError as exc:
                errors[name] = str(exc)
            except Exception as exc:  # Keep one failed player from losing every category.
                errors[name] = f"Unexpected error: {exc}"
    return results, errors


def render_category(number: int, names: list[str], results: dict[str, PlayerStats]) -> str:
    ranked = rank_players([results[name] for name in names if name in results])
    lines = [f"Category {number}", "-" * 67]
    if not ranked:
        lines.append("No player statistics were available.")
        return "\n".join(lines)

    lines.append(f"{'Rank':<6}{'Player':<27}{'Team':<7}{'GP':>5}{'G':>5}{'G/GP':>9}")
    for index, player in enumerate(ranked, start=1):
        lines.append(
            f"{index:<6}{player.name:<27}{player.team:<7}"
            f"{player.games_played:>5}{player.goals:>5}{player.goals_per_game:>9.3f}"
        )
    winner = ranked[0]
    lines.extend(
        [
            "",
            f"Recommendation: {winner.name} ({winner.goals} goals in "
            f"{winner.games_played} games; {winner.goals_per_game:.3f} G/GP)",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        categories = (
            [parse_category(value) for value in args.category]
            if args.category
            else prompt_for_categories()
        )
    except (ValueError, EOFError, KeyboardInterrupt) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    print("\nFetching current NHL regular-season statistics...\n")
    results, errors = fetch_all(NHLClient(), categories)
    for index, names in enumerate(categories, start=1):
        print(render_category(index, names, results))
        print()

    if errors:
        print("Players that could not be loaded:", file=sys.stderr)
        for name, message in errors.items():
            print(f"  - {name}: {message}", file=sys.stderr)
        return 1 if not results else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
