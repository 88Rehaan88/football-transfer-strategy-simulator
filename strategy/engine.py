"""
Simulation engine orchestrator.

Runs the full simulation pipeline:
  1. Scrape user squad
  2. Scrape market pool from other league clubs
  3. Sell phase
  4. Buy phase
  5. Age progression
  6. KPI computation
"""

import json
from pathlib import Path

from scraper.scraper import scrape_team, scrape_market_pool
from scraper.schemas import Player
from scraper.config import LEAGUE_TOP_CLUBS
from strategy.models import SimulationInput, SimulationResult
from strategy.market import TransferMarket
from strategy.rules import sell_phase, buy_phase
from strategy.kpi import apply_age_progression, compute_kpis

DATA_DIR = Path(__file__).parent.parent / "data"


def run_simulation(sim_input: SimulationInput) -> SimulationResult:
    """
    Run a full transfer simulation for a club and season.

    Scrapes fresh data if no cached file exists for the club/season.
    Market pool is always scraped fresh (other clubs' squads).

    Args:
        sim_input: User-provided simulation parameters

    Returns:
        SimulationResult with full before/after state and KPIs
    """
    # Step 1: Load or scrape user squad
    squad = _load_or_scrape_squad(sim_input)
    if not squad:
        raise ValueError(f"No squad data found for {sim_input.team_name}")

    # Step 2: Load or scrape market pool from other league clubs
    print(f"\n[Engine] Building market pool for {sim_input.league}...")
    market_players = _load_or_scrape_market_pool(sim_input)
    market = TransferMarket(market_players)
    print(f"[Engine] Market pool: {len(market)} players available")

    # Step 3: Snapshot squad before any changes
    squad_before = list(squad)

    # Step 4: Sell phase
    print(f"\n[Engine] Running sell phase ({sim_input.strategy_mode} mode)...")
    squad, players_sold, transfer_budget = sell_phase(
        squad, sim_input.transfer_budget, mode=sim_input.strategy_mode
    )
    print(f"[Engine] Sold {len(players_sold)} players | Budget now: €{transfer_budget:,}")

    # Step 5: Buy phase
    print(f"\n[Engine] Running buy phase ({sim_input.strategy_mode} mode)...")
    squad, players_bought, transfer_budget, salary_used = buy_phase(
        squad, market, transfer_budget, sim_input.salary_budget,
        original_transfer_budget=sim_input.transfer_budget,
        mode=sim_input.strategy_mode,
    )
    print(f"[Engine] Bought {len(players_bought)} players | Budget remaining: €{transfer_budget:,}")

    # Step 6: Age progression on final squad
    squad_after = apply_age_progression(squad)

    # Step 7: Compute KPIs
    kpis = compute_kpis(
        squad_before=squad_before,
        squad_after=squad_after,
        players_bought=players_bought,
        players_sold=players_sold,
        transfer_budget_remaining=transfer_budget,
        salary_budget=sim_input.salary_budget,
        salary_used=salary_used,
    )

    return SimulationResult(
        sim_input=sim_input,
        squad_before=squad_before,
        squad_after=squad_after,
        players_sold=players_sold,
        players_bought=players_bought,
        kpis=kpis,
    )


def _load_or_scrape_market_pool(sim_input: SimulationInput) -> list[Player]:
    """
    Load market pool from cache if available, otherwise scrape and cache it.

    Cache file: market_{league}_{season}.json  e.g. market_laliga_2024-25.json
    Excludes the user's own club from the pool.
    """
    season_str = f"{sim_input.season}-{str(sim_input.season + 1)[-2:]}"
    cache_path = DATA_DIR / f"market_{sim_input.league}_{season_str}.json"

    if cache_path.exists():
        print(f"[Engine] Loading market pool from cache: {cache_path.name}")
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
        players = [Player(**p) for p in data]
        # Always exclude user's own club from pool (even from cache)
        return [p for p in players if p.current_club != sim_input.team_name]

    # Try to build pool from individually cached club files first
    players = _build_pool_from_cached_clubs(sim_input)
    if not players:
        print(f"[Engine] No cached clubs found — scraping {sim_input.league} clubs...")
        players = scrape_market_pool(
            league=sim_input.league,
            season_start_year=sim_input.season,
            exclude_club_id=sim_input.club_id,
        )

    # Cache to disk for reuse
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump(mode="json") for p in players], f, indent=2, ensure_ascii=False)
    print(f"[Engine] Market pool cached: {cache_path.name}")

    return players


def _build_pool_from_cached_clubs(sim_input: SimulationInput) -> list[Player]:
    """
    Build market pool from individually cached club JSON files.

    Uses the same naming convention as storage.py:
      {team-slug}_{season}.json  e.g. real-madrid_2024-25.json

    Returns empty list if any club in the league has no cached file,
    so the caller falls back to live scraping.
    """
    season_str = f"{sim_input.season}-{str(sim_input.season + 1)[-2:]}"
    clubs = LEAGUE_TOP_CLUBS.get(sim_input.league, [])
    all_players: list[Player] = []

    for club in clubs:
        if club["id"] == sim_input.club_id:
            continue  # Skip user's own club

        slug = club["name"].lower().replace(" ", "-")
        cache_path = DATA_DIR / f"{slug}_{season_str}.json"

        if not cache_path.exists():
            print(f"[Engine] No cache for {club['name']} — will scrape fresh")
            return []  # Trigger full live scrape

        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
        players = [Player(**p) for p in data.get("players", [])]
        print(f"[Engine] Loaded {len(players)} players from cache: {cache_path.name}")
        all_players.extend(players)

    return all_players


def _load_or_scrape_squad(sim_input: SimulationInput) -> list[Player]:
    """
    Load squad from cached JSON if available, otherwise scrape fresh.

    Cache file naming matches storage.py convention:
      {team-slug}_{season}.json  e.g. fc-barcelona_2024-25.json
    """
    season_str = f"{sim_input.season}-{str(sim_input.season + 1)[-2:]}"
    slug = sim_input.team_name.lower().replace(" ", "-")
    cache_path = DATA_DIR / f"{slug}_{season_str}.json"

    if cache_path.exists():
        print(f"[Engine] Loading squad from cache: {cache_path.name}")
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
        return [Player(**p) for p in data.get("players", [])]

    print(f"[Engine] No cache found — scraping {sim_input.team_name}...")
    result = scrape_team(
        club_slug=sim_input.club_slug,
        club_id=sim_input.club_id,
        team_name=sim_input.team_name,
        season_start_year=sim_input.season,
    )
    return result.players
