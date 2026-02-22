"""
Scraper orchestrator.

Builds Transfermarkt URLs, fetches pages via the HTTP client,
and passes HTML to parsers. Returns a TeamScrapingResult.

Stage 1: Scrape club transfers page → transfers list
Stage 2: Scrape club squad page → players list with detailed data

URL patterns:
  Transfers: /{slug}/transfers/verein/{id}/saison_id/{year}
  Squad:     /{slug}/kader/verein/{id}/saison_id/{year}/plus/1
"""

from .client import ScraperClient
from .parsers import parse_transfers, parse_players
from .schemas import TeamScrapingResult, Player
from .config import BASE_URL, LEAGUE_TOP_CLUBS


def scrape_team(
    club_slug: str,
    club_id: str,
    team_name: str,
    season_start_year: int,
) -> TeamScrapingResult:
    """
    Full scrape for a club and season (Stage 1 + Stage 2).

    Args:
        club_slug: URL slug for the club, e.g. "fc-barcelona"
        club_id: Transfermarkt club ID, e.g. "131"
        team_name: Human-readable club name, e.g. "FC Barcelona"
        season_start_year: Starting year of the season, e.g. 2024 for 2024/25

    Returns:
        TeamScrapingResult with players and transfers populated
    """
    client = ScraperClient()
    season = _format_season(season_start_year)

    # Stage 1: transfers page gives us historical in/out moves for the season
    transfers = _scrape_transfers(client, club_slug, club_id, team_name, season_start_year)

    # Stage 2: squad page gives us the current roster with market values and ages
    players = _scrape_squad(client, club_slug, club_id, team_name, season_start_year)

    return TeamScrapingResult(
        team_name=team_name,
        season=season,
        players=players,
        transfers=transfers,
    )


def _scrape_transfers(client, club_slug, club_id, team_name, season_start_year):
    """Stage 1: Fetch and parse the transfers page."""
    url = (
        f"{BASE_URL}/{club_slug}/transfers/verein/{club_id}"
        f"/saison_id/{season_start_year}"
    )
    print(f"[Stage 1] Fetching transfers: {url}")

    html = client.get(url)
    if not html:
        print("[Stage 1] Failed to fetch transfers page")
        return []

    transfers = parse_transfers(html, team_name)
    print(f"[Stage 1] Found {len(transfers)} transfers")
    return transfers


def _scrape_squad(client, club_slug, club_id, team_name, season_start_year):
    """Stage 2: Fetch and parse the squad page (detailed view)."""
    url = (
        f"{BASE_URL}/{club_slug}/kader/verein/{club_id}"
        f"/saison_id/{season_start_year}/plus/1"
    )
    print(f"[Stage 2] Fetching squad: {url}")

    html = client.get(url)
    if not html:
        print("[Stage 2] Failed to fetch squad page")
        return []

    players = parse_players(html, team_name)
    print(f"[Stage 2] Found {len(players)} players")
    return players


def scrape_market_pool(
    league: str,
    season_start_year: int,
    exclude_club_id: str,
) -> list[Player]:
    """
    Scrape squad players from all top clubs in a league, excluding the user's club.

    Uses the LEAGUE_TOP_CLUBS manual registry — no dynamic league table scraping.
    Each club's squad page is fetched with delays between requests.

    Args:
        league: League key from LEAGUE_TOP_CLUBS, e.g. "laliga"
        season_start_year: Season start year, e.g. 2024
        exclude_club_id: Club ID to skip (the user's own club)

    Returns:
        Flat list of Player objects from all other clubs combined
    """
    clubs = LEAGUE_TOP_CLUBS.get(league, [])
    if not clubs:
        print(f"[Market Pool] Unknown league: {league}")
        return []

    # One shared client so delays are applied across all club requests, not per-club
    client = ScraperClient()
    all_players: list[Player] = []

    for club in clubs:
        # Skip the user's own club — they're not available to buy from themselves
        if club["id"] == exclude_club_id:
            print(f"[Market Pool] Skipping {club['name']} (user's club)")
            continue

        players = _scrape_squad(client, club["slug"], club["id"], club["name"], season_start_year)
        print(f"[Market Pool] {club['name']}: {len(players)} players")
        all_players.extend(players)

    print(f"[Market Pool] Total: {len(all_players)} players from {league}")
    return all_players


def _format_season(season_start_year: int) -> str:
    """Format season start year into display string, e.g. 2024 → '2024-25'."""
    return f"{season_start_year}-{str(season_start_year + 1)[-2:]}"
