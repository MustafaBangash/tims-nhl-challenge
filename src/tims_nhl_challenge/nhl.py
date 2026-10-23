from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SEARCH_URL = "https://search.d3.nhle.com/api/v1/search/player"
PLAYER_URL = "https://api-web.nhle.com/v1/player/{player_id}/landing"
USER_AGENT = "tims-nhl-challenge/0.1"


class NHLAPIError(RuntimeError):
    """Raised when NHL data cannot be retrieved or understood."""


@dataclass(frozen=True)
class PlayerStats:
    player_id: int
    name: str
    team: str
    games_played: int
    goals: int

    @property
    def goals_per_game(self) -> float:
        return self.goals / self.games_played if self.games_played else 0.0


class NHLClient:
    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def _get_json(self, url: str) -> Any:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise NHLAPIError(f"Could not retrieve NHL data: {exc}") from exc

    def find_player(self, name: str) -> dict[str, Any]:
        query = urlencode({"culture": "en-us", "limit": 20, "q": name})
        results = self._get_json(f"{SEARCH_URL}?{query}")
        if not isinstance(results, list) or not results:
            raise NHLAPIError(f'No NHL player found for "{name}".')

        wanted = _normalise_name(name)
        exact = [p for p in results if _normalise_name(str(p.get("name", ""))) == wanted]
        candidates = exact or results
        candidates.sort(
            key=lambda p: (
                bool(p.get("active")),
                SequenceMatcher(None, wanted, _normalise_name(str(p.get("name", "")))).ratio(),
            ),
            reverse=True,
        )
        return candidates[0]

    def get_player_stats(self, name: str) -> PlayerStats:
        match = self.find_player(name)
        player_id = int(match["playerId"])
        payload = self._get_json(PLAYER_URL.format(player_id=player_id))

        first_name = payload.get("firstName", {}).get("default", "")
        last_name = payload.get("lastName", {}).get("default", "")
        resolved_name = f"{first_name} {last_name}".strip() or str(match.get("name", name))
        current = (
            payload.get("featuredStats", {})
            .get("regularSeason", {})
            .get("subSeason", {})
        )
        return PlayerStats(
            player_id=player_id,
            name=resolved_name,
            team=str(payload.get("currentTeamAbbrev") or match.get("teamAbbrev") or "—"),
            games_played=int(current.get("gamesPlayed") or 0),
            goals=int(current.get("goals") or 0),
        )


def rank_players(players: list[PlayerStats]) -> list[PlayerStats]:
    """Rank by goals per game, then goals, then games played."""
    return sorted(
        players,
        key=lambda player: (player.goals_per_game, player.goals, player.games_played),
        reverse=True,
    )


def _normalise_name(name: str) -> str:
    return " ".join(name.casefold().split())

