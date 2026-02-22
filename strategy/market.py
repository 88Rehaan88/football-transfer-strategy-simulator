"""
Transfer market pool.

Wraps the flat list of players scraped from other league clubs.
Provides position-group filtering and purchase tracking.
"""

from scraper.schemas import Player

# Maps Transfermarkt position strings to simplified groups used by the engine
POSITION_MAP: dict[str, str] = {
    "Goalkeeper": "GK",
    "Sweeper": "DEF",
    "Centre-Back": "DEF",
    "Left-Back": "DEF",
    "Right-Back": "DEF",
    "Defensive Midfield": "MID",
    "Central Midfield": "MID",
    "Left Midfield": "MID",
    "Right Midfield": "MID",
    "Attacking Midfield": "MID",
    "Left Winger": "ATT",
    "Right Winger": "ATT",
    "Second Striker": "ATT",
    "Centre-Forward": "ATT",
}

# Position group thresholds: (min, max) players per group.
# Ranges are intentionally wide to accommodate squads scraped from Transfermarkt,
# which include B-team and youth players alongside the first team (typically 30-40 total).
POSITION_THRESHOLDS: dict[str, tuple[int, int]] = {
    "GK":  (2, 3),    # Clubs carry 2-3 GKs; tight range prevents circular sell/buy
    "DEF": (5, 12),   # Wide max to accommodate B-team defenders in scraped data
    "MID": (5, 12),   # Wide max to accommodate B-team midfielders in scraped data
    "ATT": (3, 10),   # Wide max to accommodate B-team attackers in scraped data
}


def get_position_group(position: str | None) -> str | None:
    """Map a Transfermarkt position string to a simplified group (GK/DEF/MID/ATT)."""
    if not position:
        return None
    return POSITION_MAP.get(position)


def estimate_salary(market_value: int | None) -> int:
    """Estimate annual salary as 10% of market value."""
    if not market_value:
        return 0
    return int(market_value * 0.10)


class TransferMarket:
    """
    Represents the pool of available players from other clubs.

    Players are removed from the pool once purchased to prevent
    the same player being bought twice.
    """

    def __init__(self, players: list[Player]):
        # Index by player_id for O(1) removal
        self._pool: dict[str, Player] = {p.player_id: p for p in players}

    def get_candidates(self, position_group: str, max_fee: int) -> list[Player]:
        """
        Return affordable candidates for a position group, sorted by market_value desc.

        Args:
            position_group: One of GK, DEF, MID, ATT
            max_fee: Maximum transfer fee the club can pay (remaining transfer budget)

        Returns:
            List of players matching position and affordable, best value first
        """
        candidates = []
        for player in self._pool.values():
            if get_position_group(player.position) != position_group:
                continue
            fee = player.market_value or 0
            if fee > max_fee:
                continue
            candidates.append(player)

        # Sort by market_value descending — buy the best available
        return sorted(candidates, key=lambda p: p.market_value or 0, reverse=True)

    def remove_player(self, player_id: str) -> None:
        """Remove a purchased player from the pool."""
        self._pool.pop(player_id, None)

    def __len__(self) -> int:
        return len(self._pool)
