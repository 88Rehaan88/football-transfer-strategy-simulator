"""
HTML parsers for extracting football data from Transfermarkt pages.

Each function takes raw HTML and returns structured schema objects.
All BeautifulSoup logic lives here.
"""

from typing import Optional
from datetime import datetime, date

from bs4 import BeautifulSoup

from .schemas import Player, Transfer, Valuation
from .utils import parse_fee, extract_player_id


def parse_players(html: str, team_name: str) -> list[Player]:
    """
    Extract player data from team squad page (detailed view).

    Squad page columns (td indices):
        0: jersey number, 1: player (inline-table), 2: birth date + age,
        3: nationality flags, 4: 2nd nationality, 5: height,
        6: preferred foot, 7: date joined, 8: contract end, 9: market value

    Args:
        html: Raw HTML from squad page (detailed view, /plus/1)
        team_name: Name of the team (for current_club field)

    Returns:
        List of Player objects
    """
    soup = BeautifulSoup(html, "lxml")
    players = []

    table = soup.find("table", class_="items")
    if not table:
        return players

    tbody = table.find("tbody")
    if not tbody:
        return players

    for row in tbody.find_all("tr", recursive=False):
        try:
            player = _parse_player_row(row, team_name)
            if player:
                players.append(player)
        except Exception:
            continue

    return players


def _parse_player_row(row, team_name: str) -> Optional[Player]:
    """Parse a single squad table row into a Player object."""
    tds = row.find_all("td", recursive=False)
    if len(tds) < 10:
        return None

    # Player link and name from inline-table
    inline_table = row.find("table", class_="inline-table")
    if not inline_table:
        return None

    player_link = inline_table.find("a", href=True)
    if not player_link:
        return None

    player_id = extract_player_id(player_link["href"])
    if not player_id:
        return None

    name = player_link.get_text(strip=True)

    # Position from second row of inline-table
    inline_rows = inline_table.find_all("tr")
    position = None
    if len(inline_rows) >= 2:
        position = inline_rows[1].get_text(strip=True) or None

    # Birth date and age from td[2]: "30/04/1992 (33)"
    dob_text = tds[2].get_text(strip=True)
    birth_date = None
    age = None
    if dob_text:
        # Split "30/04/1992 (33)" into date part and age part
        dob_part = dob_text.split("(")[0].strip()
        birth_date = parse_date(dob_part)
        age_match = dob_text.split("(")[-1].replace(")", "").strip() if "(" in dob_text else None
        age = _safe_int(age_match) if age_match else None

    # Nationality from flag img title attributes in td[3] and td[4]
    nationality = None
    for nat_td in [tds[3], tds[4]]:
        flags = nat_td.find_all("img", class_="flaggenrahmen")
        for flag in flags:
            title = flag.get("title", "").strip()
            if title:
                nationality = title
                break
        if nationality:
            break

    # Preferred foot from td[6]
    preferred_foot = tds[6].get_text(strip=True) or None

    # Market value from td[9]
    mv_text = tds[9].get_text(strip=True)
    market_value = parse_fee(mv_text) if mv_text else None

    return Player(
        player_id=player_id,
        name=name,
        age=age,
        position=position,
        nationality=nationality,
        current_club=team_name,
        birth_date=birth_date,
        preferred_foot=preferred_foot,
        market_value=market_value,
    )


def parse_transfers(html: str, team_name: str) -> list[Transfer]:
    """
    Extract transfer data from club transfers page (Stage 1).

    Parses arrivals and departures sections. Exact transfer_date
    is not available on this page — it will be enriched in Stage 2.

    Note: Transfermarkt uses name="zugaenge" on both section headers.
    We locate them by order: first = arrivals, second = departures.

    Args:
        html: Raw HTML from transfers page
        team_name: Club name used to set from/to club direction

    Returns:
        Combined list of Transfer objects from arrivals and departures
    """
    soup = BeautifulSoup(html, "lxml")

    # Both h2 headers share name="zugaenge" — find by position, not name
    all_headers = soup.find_all("h2", attrs={"name": "zugaenge"})
    arrivals_header = all_headers[0] if len(all_headers) > 0 else None
    departures_header = all_headers[1] if len(all_headers) > 1 else None

    transfers = []
    transfers.extend(_parse_transfer_section(arrivals_header, team_name, direction="in"))
    transfers.extend(_parse_transfer_section(departures_header, team_name, direction="out"))

    return transfers


def _parse_transfer_section(
    header,
    team_name: str,
    direction: str,
) -> list[Transfer]:
    """
    Parse a single transfer section (arrivals or departures).

    Args:
        header: The h2 element marking the section start
        team_name: Club name for from/to logic
        direction: "in" (arrival) or "out" (departure)

    Returns:
        List of Transfer objects for this section
    """
    if not header:
        return []

    table = header.find_next("table", class_="items")
    if not table:
        return []

    tbody = table.find("tbody")
    if not tbody:
        return []

    transfers = []
    for row in tbody.find_all("tr", recursive=False):
        try:
            transfer = _parse_transfer_row(row, team_name, direction)
            if transfer:
                transfers.append(transfer)
        except Exception:
            continue

    return transfers


def _parse_transfer_row(
    row, team_name: str, direction: str
) -> Optional[Transfer]:
    """Parse a single transfer table row into a Transfer object."""
    # Extract player link from nested inline-table
    inline_table = row.find("table", class_="inline-table")
    if not inline_table:
        return None

    player_link = inline_table.find("a", href=True)
    if not player_link:
        return None

    player_id = extract_player_id(player_link["href"])
    if not player_id:
        return None

    player_name = player_link.get_text(strip=True)

    # Position is in the second <tr> of the inline-table
    inline_rows = inline_table.find_all("tr")
    position = None
    if len(inline_rows) >= 2:
        position = inline_rows[1].get_text(strip=True) or None

    # Age is in td[2] (class="zentriert"), td[0]=color-bar, td[1]=player
    tds = row.find_all("td", recursive=False)
    age = _safe_int(tds[2].get_text(strip=True)) if len(tds) > 2 else None

    # Club name: second inline-table, td.hauptlink > a (avoids grabbing the logo link)
    club_name = None
    club_cells = row.find_all("table", class_="inline-table")
    if len(club_cells) >= 2:
        hauptlink_td = club_cells[1].find("td", class_="hauptlink")
        if hauptlink_td:
            club_link = hauptlink_td.find("a")
            if club_link:
                club_name = club_link.get_text(strip=True)

    # Fee is in last cell, inside a link (or just text for free transfers)
    fee_cell = tds[-1] if tds else None
    if fee_cell:
        fee_link = fee_cell.find("a")
        fee_text = fee_link.get_text(strip=True) if fee_link else fee_cell.get_text(strip=True)
    else:
        fee_text = ""
    transfer_fee = parse_fee(fee_text)
    is_loan = "loan" in fee_text.lower()

    # Direction determines from/to
    if direction == "in":
        from_club = club_name
        to_club = team_name
    else:
        from_club = team_name
        to_club = club_name

    return Transfer(
        player_id=player_id,
        player_name=player_name,
        age_at_transfer=age,
        position=position,
        from_club=from_club,
        to_club=to_club,
        transfer_fee=transfer_fee,
        transfer_date=None,  # Stage 2 will enrich this
        is_loan=is_loan,
    )


def _safe_int(value: str) -> Optional[int]:
    """Convert string to int, returning None on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_valuations(html: str, player_id: str, player_name: str) -> list[Valuation]:
    """
    Extract historical market valuations from player profile page.
    
    Args:
        html: Raw HTML from player market value page
        player_id: Player ID for linking
        player_name: Player name for readability
        
    Returns:
        List of Valuation objects with historical snapshots
    """
    soup = BeautifulSoup(html, "lxml")
    valuations = []
    
    # TODO: Implement actual parsing logic
    # Expected structure:
    # - Find market value chart data or table
    # - Extract date and value pairs
    # - Parse valuation_amount using utils.parse_fee()
    # - Extract club at that time if available
    
    return valuations


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """
    Parse Transfermarkt date string to Python date object.

    Handles formats: "30/04/1992", "Jul 1, 2024", "2024-07-01"

    Args:
        date_str: Raw date string from page

    Returns:
        date object or None if parsing fails
    """
    if not date_str or date_str.strip() in ["-", "?", ""]:
        return None

    cleaned = date_str.strip()

    formats = [
        "%d/%m/%Y",   # 30/04/1992 (squad page)
        "%b %d, %Y",  # Jul 1, 2024
        "%d.%m.%Y",   # 01.07.2024
        "%Y-%m-%d",   # 2024-07-01 (ISO)
    ]

    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    return None
