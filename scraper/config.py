"""
Configuration constants for the scraper.

Single source of truth for URLs, headers, delays, and other settings.
"""

# Transfermarkt base URL
BASE_URL = "https://www.transfermarkt.com"

# HTTP request headers to mimic a real browser
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Delay between requests (min, max) in seconds - randomized to avoid detection
REQUEST_DELAY_RANGE = (2.0, 4.0)

# Maximum retry attempts for failed requests
MAX_RETRIES = 3

# Request timeout in seconds
REQUEST_TIMEOUT = 30

# Manual registry of top clubs per league.
# Slugs and IDs are stable Transfermarkt identifiers — no dynamic scraping needed.
LEAGUE_TOP_CLUBS: dict[str, list[dict]] = {
    "laliga": [
        {"slug": "real-madrid",     "id": "418",   "name": "Real Madrid"},
        {"slug": "fc-barcelona",    "id": "131",   "name": "FC Barcelona"},
        {"slug": "atletico-madrid", "id": "13",    "name": "Atletico Madrid"},
        {"slug": "real-sociedad",   "id": "681",   "name": "Real Sociedad"},
        {"slug": "fc-villarreal",   "id": "1050",  "name": "Villarreal"},
    ],
    "premier-league": [
        {"slug": "manchester-city",   "id": "281",  "name": "Manchester City"},
        {"slug": "arsenal-fc",        "id": "11",   "name": "Arsenal"},
        {"slug": "liverpool-fc",      "id": "31",   "name": "Liverpool"},
        {"slug": "fc-chelsea",        "id": "631",  "name": "Chelsea"},
        {"slug": "tottenham-hotspur", "id": "148",  "name": "Tottenham"},
    ],
    "bundesliga": [
        {"slug": "fc-bayern-munchen",     "id": "27",    "name": "Bayern Munich"},
        {"slug": "borussia-dortmund",     "id": "16",    "name": "Borussia Dortmund"},
        {"slug": "bayer-04-leverkusen",   "id": "15",    "name": "Bayer Leverkusen"},
        {"slug": "rasenballsport-leipzig","id": "23826", "name": "RB Leipzig"},
        {"slug": "eintracht-frankfurt",   "id": "24",    "name": "Eintracht Frankfurt"},
    ],
    "serie-a": [
        {"slug": "inter-mailand",  "id": "46",   "name": "Inter Milan"},
        {"slug": "juventus-turin", "id": "506",  "name": "Juventus"},
        {"slug": "ac-mailand",     "id": "5",    "name": "AC Milan"},
        {"slug": "as-rom",         "id": "12",   "name": "AS Roma"},
        {"slug": "ssn-neapel",     "id": "6195", "name": "Napoli"},
    ],
    "ligue-1": [
        {"slug": "paris-saint-germain", "id": "583",  "name": "PSG"},
        {"slug": "olympique-marseille", "id": "244",  "name": "Marseille"},
        {"slug": "as-monaco",           "id": "162",  "name": "Monaco"},
        {"slug": "olympique-lyon",      "id": "1041", "name": "Lyon"},
        {"slug": "ogc-nice",            "id": "417",  "name": "Nice"},
    ],
}

# Flat registry: club name → {slug, id, league} for API lookups.
# Built automatically from LEAGUE_TOP_CLUBS — single source of truth.
CLUB_REGISTRY: dict[str, dict] = {
    club["name"]: {"slug": club["slug"], "id": club["id"], "league": league}
    for league, clubs in LEAGUE_TOP_CLUBS.items()
    for club in clubs
}
