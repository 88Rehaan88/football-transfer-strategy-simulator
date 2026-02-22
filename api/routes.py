"""
API route definitions.

Endpoints:
  GET  /health    — liveness check
  POST /simulate  — run strategy engine + AI analysis, return full result
"""

from collections import defaultdict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scraper.schemas import Player
from scraper.config import CLUB_REGISTRY, LEAGUE_TOP_CLUBS
from strategy.models import SimulationInput, KPIs, StrategyMode
from strategy.engine import run_simulation
from ai.schemas import SeasonSummary
from ai.analyst import analyse_season

router = APIRouter()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class AgeDistribution(BaseModel):
    labels: list[str]   # age bucket labels, e.g. ["U21", "21-23", ...]
    before: list[int]   # player counts per bucket before simulation
    after: list[int]    # player counts per bucket after simulation


class ValuationData(BaseModel):
    before: int
    after: int
    change: int


class BudgetData(BaseModel):
    transfer_spent: int
    transfer_remaining: int
    salary_used: int
    salary_remaining: int


class ChartData(BaseModel):
    age_distribution: AgeDistribution
    valuation: ValuationData
    budget: BudgetData


class SimulationResponse(BaseModel):
    club: str
    season: str
    strategy_mode: str
    kpis: KPIs
    players_sold: list[Player]
    players_bought: list[Player]
    analysis: SeasonSummary
    chart_data: ChartData


# ---------------------------------------------------------------------------
# Chart data computation (pure Python, no AI)
# ---------------------------------------------------------------------------

# Buckets match typical football squad analysis breakdowns (youth, prime, decline)
_AGE_BUCKETS = [
    ("U21",   range(0, 21)),
    ("21-23", range(21, 24)),
    ("24-26", range(24, 27)),
    ("27-29", range(27, 30)),
    ("30-32", range(30, 33)),
    ("33+",   range(33, 99)),
]


def _age_bucket(age: int | None) -> str:
    if age is None:
        return "Unknown"
    for label, r in _AGE_BUCKETS:
        if age in r:
            return label
    return "33+"  # Fallback — covers any edge case above the last bucket


def _build_age_distribution(
    squad_before: list[Player],
    squad_after: list[Player],
) -> AgeDistribution:
    labels = [label for label, _ in _AGE_BUCKETS]
    before_counts: dict[str, int] = defaultdict(int)
    after_counts: dict[str, int] = defaultdict(int)

    for p in squad_before:
        before_counts[_age_bucket(p.age)] += 1
    for p in squad_after:
        after_counts[_age_bucket(p.age)] += 1

    return AgeDistribution(
        labels=labels,
        before=[before_counts.get(l, 0) for l in labels],
        after=[after_counts.get(l, 0) for l in labels],
    )


def _build_chart_data(result) -> ChartData:
    k = result.kpis
    # Spent = original budget minus what's left — not tracked directly in KPIs
    transfer_spent = result.sim_input.transfer_budget - k.transfer_budget_remaining

    return ChartData(
        age_distribution=_build_age_distribution(result.squad_before, result.squad_after),
        valuation=ValuationData(
            before=k.total_valuation_before,
            after=k.total_valuation_after,
            change=k.valuation_change,
        ),
        budget=BudgetData(
            transfer_spent=transfer_spent,
            transfer_remaining=k.transfer_budget_remaining,
            salary_used=k.salary_used,
            salary_remaining=k.salary_budget_remaining,
        ),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/clubs")
def list_clubs():
    """
    Return all supported clubs grouped by league.

    Used by the frontend to populate the club dropdown without exposing
    internal slug/id details to the user.
    """
    result = []
    for league, clubs in LEAGUE_TOP_CLUBS.items():
        # Convert internal league keys to display-friendly labels for the frontend
        league_label = {
            "laliga": "LaLiga",
            "premier-league": "Premier League",
            "bundesliga": "Bundesliga",
            "serie-a": "Serie A",
            "ligue-1": "Ligue 1",
        }.get(league, league)
        for club in clubs:
            result.append({"name": club["name"], "league": league_label})
    return result


@router.post("/simulate", response_model=SimulationResponse)
def simulate(sim_input: SimulationInput):
    """
    Run the full simulation pipeline:
      1. Resolve club slug/id/league from team_name
      2. Load/scrape squad and market pool
      3. Apply sell + buy rules based on strategy mode
      4. Apply age progression
      5. Compute KPIs
      6. Generate AI analysis via Gemini
      7. Return structured response with chart data
    """
    # User only sends team_name — we look up slug/id/league so they never need to know them
    club_meta = CLUB_REGISTRY.get(sim_input.team_name)
    if not club_meta:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown club '{sim_input.team_name}'. Use GET /clubs to see supported clubs.",
        )
    sim_input.club_slug = club_meta["slug"]
    sim_input.club_id = club_meta["id"]
    sim_input.league = club_meta["league"]

    try:
        result = run_simulation(sim_input)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {e}")

    try:
        analysis = analyse_season(result)
    except EnvironmentError as e:
        # Missing API key — surface a clear message rather than a generic 500
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis error: {e}")

    chart_data = _build_chart_data(result)
    season_label = f"{sim_input.season}/{str(sim_input.season + 1)[-2:]}"  # e.g. "2024/25"

    return SimulationResponse(
        club=sim_input.team_name,
        season=season_label,
        strategy_mode=sim_input.strategy_mode,
        kpis=result.kpis,
        players_sold=result.players_sold,
        players_bought=result.players_bought,
        analysis=analysis,
        chart_data=chart_data,
    )
