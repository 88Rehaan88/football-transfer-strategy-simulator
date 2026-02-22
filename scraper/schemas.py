"""
Pydantic schemas for scraped football data.

Design decisions:
- player_id + player_name: IDs (from Transfermarkt URLs) prevent name collisions,
  names provide readability. Both are stored for correctness and usability.
- int for money: Transfer fees are always whole euros, never fractional.
- Optional fields: Gracefully handle missing data from incomplete web pages.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class Player(BaseModel):
    """A football player's profile data."""

    player_id: str = Field(..., description="Unique player ID from Transfermarkt URL")
    name: str = Field(..., description="Full player name")
    age: Optional[int] = Field(default=None, description="Player age at time of scraping")
    position: Optional[str] = Field(default=None, description="Primary playing position")
    nationality: Optional[str] = Field(default=None, description="Player nationality")
    current_club: Optional[str] = Field(default=None, description="Current club name")
    birth_date: Optional[date] = Field(default=None, description="Date of birth")
    preferred_foot: Optional[str] = Field(default=None, description="Left, Right, or Both")
    market_value: Optional[int] = Field(default=None, description="Current market value in euros")


class Transfer(BaseModel):
    """A single transfer record for a player."""

    player_id: str = Field(..., description="Player ID linking to Player model")
    player_name: str = Field(..., description="Name of the transferred player")
    age_at_transfer: Optional[int] = Field(
        default=None, description="Player age at time of transfer"
    )
    position: Optional[str] = Field(default=None, description="Player position")
    from_club: Optional[str] = Field(default=None, description="Selling club")
    to_club: Optional[str] = Field(default=None, description="Buying club")
    transfer_fee: Optional[int] = Field(
        default=None, description="Transfer fee in euros (None = undisclosed or free)"
    )
    transfer_date: Optional[date] = Field(default=None, description="Date of transfer")
    is_loan: bool = Field(default=False, description="Whether this is a loan move")


class Valuation(BaseModel):
    """A market valuation snapshot for a player at a point in time."""

    player_id: str = Field(..., description="Player ID linking to Player model")
    player_name: str = Field(..., description="Name of the player")
    valuation_amount: Optional[int] = Field(
        default=None, description="Market valuation in euros"
    )
    valuation_date: Optional[date] = Field(
        default=None, description="Date of the valuation"
    )
    current_club: Optional[str] = Field(
        default=None, description="Club at time of valuation"
    )


class TeamScrapingResult(BaseModel):
    """
    Aggregated scraping result for a single team + season.

    This is the top-level container returned by the scraper orchestrator.
    It bundles all entities together with metadata about what was scraped.
    """

    team_name: str = Field(..., description="Name of the team that was scraped")
    season: str = Field(..., description="Season identifier, e.g. '2024-2025'")
    players: list[Player] = Field(default_factory=list)
    transfers: list[Transfer] = Field(default_factory=list)
    valuations: list[Valuation] = Field(default_factory=list)
