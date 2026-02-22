"""
Storage module for persisting scraped data to disk.

Writes TeamScrapingResult to JSON in the data/ directory.
Keeps I/O concerns out of the scraper and parser logic.
"""

import json
from pathlib import Path

from .schemas import TeamScrapingResult

DATA_DIR = Path(__file__).parent.parent / "data"


def save_result(result: TeamScrapingResult) -> Path:
    """
    Save a TeamScrapingResult to a JSON file.

    File is named: {team_slug}_{season}.json
    Example: fc-barcelona_2024-25.json

    Args:
        result: Scraped data to persist

    Returns:
        Path to the written file
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    filename = _build_filename(result.team_name, result.season)
    filepath = DATA_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

    print(f"Saved {len(result.players)} players and {len(result.transfers)} transfers to {filepath}")
    return filepath


def _build_filename(team_name: str, season: str) -> str:
    """Build a safe filename from team name and season."""
    import re
    slug = re.sub(r"[^a-z0-9\-]", "-", team_name.lower())
    return f"{slug}_{season}.json"
