from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .nhl import PlayerStats


PICKS_URL = "https://api.hockeychallengehelper.com/api/picks"


class DailyPicksError(RuntimeError):
    """Raised when today's challenge choices cannot be safely loaded."""


def fetch_daily_picks(
    *, timeout: float = 10.0, expected_date: date | None = None
) -> tuple[list[list[str]], dict[str, PlayerStats], date]:
    request = Request(
        PICKS_URL,
        headers={
            "Origin": "https://hockeychallengehelper.com",
            "Referer": "https://hockeychallengehelper.com/",
            "User-Agent": "Mozilla/5.0 tims-nhl-challenge/0.1",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise DailyPicksError(f"Could not retrieve today's choices: {exc}") from exc
    return parse_daily_picks(payload, expected_date=expected_date)


def parse_daily_picks(
    payload: Any, *, expected_date: date | None = None
) -> tuple[list[list[str]], dict[str, PlayerStats], date]:
    if not isinstance(payload, dict):
        raise DailyPicksError("The daily choices response was not a JSON object.")

    try:
        available_date = datetime.fromisoformat(payload["dateTimeAvailable"]).date()
    except (KeyError, TypeError, ValueError) as exc:
        raise DailyPicksError("The daily choices response has no valid date.") from exc

    expected = expected_date or date.today()
    if available_date != expected:
        raise DailyPicksError(
            f"The available choices are dated {available_date.isoformat()}, "
            f"not {expected.isoformat()}."
        )

    player_lists = payload.get("playerLists")
    if not isinstance(player_lists, list) or len(player_lists) != 3:
        raise DailyPicksError("Expected exactly three daily player categories.")

    categories: list[list[str]] = []
    results: dict[str, PlayerStats] = {}
    for category_number, group in enumerate(player_lists, start=1):
        players = group.get("players") if isinstance(group, dict) else None
        if not isinstance(players, list) or not players:
            raise DailyPicksError(f"Category {category_number} contains no players.")

        names: list[str] = []
        for raw_player in players:
            try:
                name = str(raw_player["fullName"]).strip()
                stats = PlayerStats(
                    player_id=int(raw_player["nhlPlayerId"]),
                    name=name,
                    team=str(raw_player.get("team") or "—"),
                    games_played=int(raw_player["gamesPlayed"]),
                    goals=int(raw_player["goals"]),
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise DailyPicksError(
                    f"Category {category_number} contains invalid player data."
                ) from exc
            if not name:
                raise DailyPicksError(
                    f"Category {category_number} contains a player without a name."
                )
            names.append(name)
            results[name] = stats
        categories.append(names)

    return categories, results, available_date

