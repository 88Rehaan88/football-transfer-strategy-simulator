"""
Age progression and KPI computation.

Age progression is applied once to squad_after at the end of simulation.
KPIs are computed by comparing squad_before to squad_after.
"""

import copy
from scraper.schemas import Player
from strategy.models import KPIs
from strategy.market import estimate_salary


# Market value multipliers by age tier after one season
AGE_VALUE_MULTIPLIERS: list[tuple[range, float]] = [
    (range(0, 21),  1.15),   # <= 20: youth premium
    (range(21, 25), 1.10),   # 21-24: rising
    (range(25, 29), 1.03),   # 25-28: peak stabilization
    (range(29, 31), 0.95),   # 29-30: early decline
    (range(31, 33), 0.90),   # 31-32: decline
    (range(33, 99), 0.80),   # 33+:   steep decline
]


def apply_age_progression(squad: list[Player]) -> list[Player]:
    """
    Project squad forward by one season: increment age and adjust market values.

    Returns a new list of Player objects — original squad is not mutated.

    Args:
        squad: Squad after all transfers are complete

    Returns:
        New list of players with age +1 and adjusted market_value
    """
    progressed = []
    for player in squad:
        updated = player.model_copy()
        updated.age = (player.age or 0) + 1
        if player.market_value:
            multiplier = _get_multiplier(player.age or 0)
            updated.market_value = int(player.market_value * multiplier)
        progressed.append(updated)
    return progressed


def compute_kpis(
    squad_before: list[Player],
    squad_after: list[Player],
    players_bought: list[Player],
    players_sold: list[Player],
    transfer_budget_remaining: int,
    salary_budget: int,
    salary_used: int,
) -> KPIs:
    """
    Compute before/after KPIs for the simulation result.

    Args:
        squad_before: Squad at start of simulation
        squad_after: Squad after transfers + age progression
        players_bought: Players purchased during simulation
        players_sold: Players sold during simulation
        transfer_budget_remaining: Unused transfer budget
        salary_budget: Original salary budget input
        salary_used: Total estimated salary of final squad

    Returns:
        KPIs object
    """
    val_before = _total_valuation(squad_before)
    val_after = _total_valuation(squad_after)

    fees_paid = sum(p.market_value or 0 for p in players_bought)
    fees_received = sum(int((p.market_value or 0) * 0.85) for p in players_sold)
    net_spend = fees_paid - fees_received

    return KPIs(
        total_valuation_before=val_before,
        total_valuation_after=val_after,
        valuation_change=val_after - val_before,
        net_spend=net_spend,
        avg_age_before=_avg_age(squad_before),
        avg_age_after=_avg_age(squad_after),
        salary_used=salary_used,
        salary_budget=salary_budget,
        salary_budget_remaining=salary_budget - salary_used,
        transfer_budget_remaining=transfer_budget_remaining,
    )


# --- Private helpers ---

def _get_multiplier(age: int) -> float:
    """Return the market value multiplier for a given age."""
    for age_range, multiplier in AGE_VALUE_MULTIPLIERS:
        if age in age_range:
            return multiplier
    return 0.80  # fallback for very old players


def _total_valuation(squad: list[Player]) -> int:
    """Sum of all players' market values."""
    return sum(p.market_value or 0 for p in squad)


def _avg_age(squad: list[Player]) -> float:
    """Average age of squad, rounded to 1 decimal."""
    ages = [p.age for p in squad if p.age is not None]
    if not ages:
        return 0.0
    return round(sum(ages) / len(ages), 1)
