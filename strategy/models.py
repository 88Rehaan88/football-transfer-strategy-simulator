"""
Pydantic schemas for the simulation layer.

Separate from scraper schemas — these represent simulation inputs/outputs,
not raw scraped data.
"""

from typing import Literal
from pydantic import BaseModel, Field
from scraper.schemas import Player

StrategyMode = Literal["balanced", "conservative", "win_now"]


class SimulationInput(BaseModel):
    """User-provided parameters for running a simulation."""

    team_name: str = Field(..., description="Human-readable club name, e.g. 'FC Barcelona'")
    season: int = Field(..., description="Season start year, e.g. 2024 for 2024/25")
    transfer_budget: int = Field(..., description="Available transfer spend in euros")
    salary_budget: int = Field(..., description="Total annual salary budget in euros")
    strategy_mode: StrategyMode = Field(
        default="balanced",
        description="Transfer strategy: balanced | conservative (sell earlier, buy young, protect budget) | win_now (keep experience, spend aggressively, allow marquee signings)",
    )
    # Resolved server-side from CLUB_REGISTRY — not required from the user
    club_slug: str = Field(default="", description="Transfermarkt club slug (resolved from team_name)")
    club_id: str = Field(default="", description="Transfermarkt club ID (resolved from team_name)")
    league: str = Field(default="", description="League key (resolved from team_name)")


class KPIs(BaseModel):
    """Before/after key performance indicators for the simulated season."""

    total_valuation_before: int = Field(..., description="Total squad market value before simulation")
    total_valuation_after: int = Field(..., description="Total squad market value after simulation + age progression")
    valuation_change: int = Field(..., description="Absolute change in squad valuation")
    net_spend: int = Field(..., description="Fees paid minus fees received (positive = net spend)")
    avg_age_before: float = Field(..., description="Average squad age before simulation")
    avg_age_after: float = Field(..., description="Average squad age after simulation")
    salary_used: int = Field(..., description="Estimated total annual salary of final squad")
    salary_budget: int = Field(..., description="Total annual salary budget provided")
    salary_budget_remaining: int = Field(..., description="Salary budget left after final squad")
    transfer_budget_remaining: int = Field(..., description="Transfer budget left after all deals")


class SimulationResult(BaseModel):
    """Full output of a completed simulation."""

    sim_input: SimulationInput
    squad_before: list[Player] = Field(default_factory=list)
    squad_after: list[Player] = Field(default_factory=list)
    players_sold: list[Player] = Field(default_factory=list)
    players_bought: list[Player] = Field(default_factory=list)
    kpis: KPIs
