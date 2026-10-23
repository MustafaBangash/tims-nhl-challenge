import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tims_nhl_challenge.cli import parse_category, render_category  # noqa: E402
from tims_nhl_challenge.nhl import PlayerStats, rank_players  # noqa: E402


def player(name: str, games: int, goals: int) -> PlayerStats:
    return PlayerStats(1, name, "TOR", games, goals)


class NHLTests(unittest.TestCase):
    def test_goals_per_game(self) -> None:
        self.assertEqual(player("Test Player", 10, 4).goals_per_game, 0.4)
        self.assertEqual(player("No Games", 0, 0).goals_per_game, 0.0)

    def test_rank_players_uses_rate_then_goals(self) -> None:
        ranked = rank_players(
            [
                player("Ten Goals", 40, 10),
                player("Fast Start", 10, 4),
                player("Tie Break", 20, 8),
            ]
        )
        self.assertEqual(
            [item.name for item in ranked],
            ["Tie Break", "Fast Start", "Ten Goals"],
        )

    def test_parse_category_ignores_empty_items(self) -> None:
        self.assertEqual(
            parse_category("Auston Matthews, , Connor McDavid"),
            ["Auston Matthews", "Connor McDavid"],
        )

    def test_render_category_recommends_top_player(self) -> None:
        results = {
            "A": player("Player A", 10, 2),
            "B": player("Player B", 10, 5),
        }
        output = render_category(1, ["A", "B"], results)
        self.assertIn("Recommendation: Player B", output)


if __name__ == "__main__":
    unittest.main()
