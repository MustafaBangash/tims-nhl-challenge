import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tims_nhl_challenge.cli import (  # noqa: E402
    parse_category,
    prompt_for_categories,
    render_category,
)
from tims_nhl_challenge.daily_picks import DailyPicksError, parse_daily_picks  # noqa: E402
from tims_nhl_challenge.nhl import PlayerStats, rank_players  # noqa: E402


def player(name: str, games: int, goals: int) -> PlayerStats:
    return PlayerStats(1, name, "TOR", games, goals)


class NHLTests(unittest.TestCase):
    def test_goals_per_game(self) -> None:
        self.assertEqual(player("Test Player", 10, 4).goals_per_game, 0.4)
        self.assertEqual(player("No Games", 0, 0).goals_per_game, 0.0)

    def test_fetch_stats_by_id_uses_nhl_response(self) -> None:
        from tims_nhl_challenge.nhl import NHLClient

        client = NHLClient()
        client._get_json = lambda _url: {  # type: ignore[method-assign]
            "firstName": {"default": "Fresh"},
            "lastName": {"default": "Stats"},
            "currentTeamAbbrev": "EDM",
            "featuredStats": {
                "regularSeason": {"subSeason": {"gamesPlayed": 12, "goals": 9}}
            },
        }
        stats = client.get_player_stats_by_id(8470000, fallback_name="Old Name")
        self.assertEqual(stats.name, "Fresh Stats")
        self.assertEqual(stats.games_played, 12)
        self.assertEqual(stats.goals, 9)

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

    @patch(
        "builtins.input",
        side_effect=["Player A, Player B", "Player C", "Player D, Player E"],
    )
    def test_interactive_input_stops_after_three_categories(self, mock_input) -> None:
        self.assertEqual(
            prompt_for_categories(),
            [["Player A", "Player B"], ["Player C"], ["Player D", "Player E"]],
        )
        self.assertEqual(mock_input.call_count, 3)

    def test_render_category_recommends_top_player(self) -> None:
        results = {
            "A": player("Player A", 10, 2),
            "B": player("Player B", 10, 5),
        }
        output = render_category(1, ["A", "B"], results)
        self.assertIn("Recommendation: Player B", output)

    def test_parse_daily_picks(self) -> None:
        from datetime import date

        payload = {
            "dateTimeAvailable": "2026-10-23T00:00:00",
            "playerLists": [
                {
                    "players": [
                        {
                            "nhlPlayerId": index,
                            "fullName": f"Player {index}",
                            "team": "TOR",
                            "gamesPlayed": 10,
                            "goals": index,
                        }
                    ]
                }
                for index in range(1, 4)
            ],
        }
        categories, results, available_date = parse_daily_picks(
            payload, expected_date=date(2026, 10, 23)
        )
        self.assertEqual(categories, [["Player 1"], ["Player 2"], ["Player 3"]])
        self.assertEqual(results["Player 3"].goals, 3)
        self.assertEqual(available_date, date(2026, 10, 23))

    def test_parse_daily_picks_rejects_stale_data(self) -> None:
        from datetime import date

        with self.assertRaises(DailyPicksError):
            parse_daily_picks(
                {"dateTimeAvailable": "2026-10-22T00:00:00", "playerLists": []},
                expected_date=date(2026, 10, 23),
            )


if __name__ == "__main__":
    unittest.main()
