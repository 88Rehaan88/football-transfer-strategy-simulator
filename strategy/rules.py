"""
Transfer strategy rules — sell phase and buy phase.

Rules are deterministic and conflict-free:
- Sell phase always completes before buy phase starts.
- Neither phase can violate position group minimums.
- Buy phase has two hard budget gates (transfer + salary).

Sell rule 1 (decline):       sell players above decline-age threshold if group stays above min.
Sell rule 2 (bloat):         trim position groups over max, lowest value first, never below min.
Sell rule 3 (window cap):    never sell more than MAX_SELLS_PER_WINDOW players in one window.
Buy rule 1  (gap fill):      fill position groups below min, best affordable first.
Buy rule 2  (opportunistic): buy prime-age players for groups below max while budget allows.

Strategy modes:
  balanced     — moderate thresholds, balanced age/budget targets, spend full budget
  conservative — sell earlier (29+), buy younger (19-24), cap total spend at 50% of original budget
  win_now      — protect experience (35+ only), allow marquee signings, spend full budget aggressively
"""

from scraper.schemas import Player
from strategy.market import (
    TransferMarket,
    POSITION_THRESHOLDS,
    get_position_group,
    estimate_salary,
)
from strategy.models import StrategyMode

# Selling: clubs receive 85% of market value (realistic discount)
SELL_FEE_FACTOR = 0.85

# Prospect protection: never sell players younger than this with value above threshold
PROSPECT_AGE = 21
PROSPECT_VALUE_THRESHOLD = 3_000_000

# Maximum strategic (decline) sells per window — keeps high-profile exits realistic
MAX_DECLINE_SELLS = 6

# Maximum low-value bloat players released per window (youth/surplus clearance)
MAX_BLOAT_SELLS = 6

# Per-mode parameters: (decline_age, prime_age_min, prime_age_max, max_single_signing_ratio, max_total_spend_ratio)
#   max_total_spend_ratio: max fraction of original transfer budget that can be spent on buys
#   1.0 = no cap (spend everything available), 0.5 = at most half the original budget on purchases
_MODE_PARAMS: dict[str, tuple[int, int, int, float, float]] = {
    "balanced":     (32, 22, 27, 0.40, 1.00),  # no spend cap
    "conservative": (29, 19, 24, 0.25, 0.50),  # spend at most 50% of original budget — financially cautious
    "win_now":      (35, 22, 30, 0.60, 1.00),  # protect players under 35, no spend cap — spend aggressively
}


def _get_mode_params(mode: StrategyMode) -> tuple[int, int, int, float, float]:
    """Return (decline_age, prime_age_min, prime_age_max, max_single_signing_ratio, max_total_spend_ratio)."""
    return _MODE_PARAMS.get(mode, _MODE_PARAMS["balanced"])  # type: ignore[arg-type]


def sell_phase(
    squad: list[Player],
    transfer_budget: int,
    mode: StrategyMode = "balanced",
) -> tuple[list[Player], list[Player], int]:
    """
    Run the sell phase on the current squad.

    Rule 1 — Decline sell: sell players above decline age threshold if position
              group count remains above minimum after the sale.
    Rule 2 — Bloat sell: trim any position group over its maximum,
              removing lowest-value players first, never below minimum.

    Args:
        squad: Current list of Player objects (will not be mutated)
        transfer_budget: Current remaining transfer budget in euros
        mode: Strategy mode controlling decline age threshold

    Returns:
        Tuple of (updated_squad, players_sold, updated_transfer_budget)
    """
    decline_age, _, _, _, _ = _get_mode_params(mode)
    squad = list(squad)
    sold: list[Player] = []
    decline_sold: list[Player] = []

    # Rule 1: Decline sell — remove aging players while group stays above minimum.
    for player in sorted(squad, key=lambda p: p.age or 0, reverse=True):
        if len(decline_sold) >= MAX_DECLINE_SELLS:
            break
        if (player.age or 0) < decline_age:
            break
        group = get_position_group(player.position)
        if not group:
            continue
        min_count, _ = POSITION_THRESHOLDS[group]
        if _count_group(squad, group) > min_count:
            squad.remove(player)
            decline_sold.append(player)
            fee = int((player.market_value or 0) * SELL_FEE_FACTOR)
            transfer_budget += fee

    sold.extend(decline_sold)

    # Rule 2: Bloat sell — trim groups that are still over max after decline sells.
    # Target is max-2 so the buy phase always has at least 2 open slots per group.
    # Capped at MAX_BLOAT_SELLS total to prevent mass youth clearances.
    bloat_sold_count = 0
    for group, (min_count, max_count) in POSITION_THRESHOLDS.items():
        if bloat_sold_count >= MAX_BLOAT_SELLS:
            break
        group_players = _get_group(squad, group)
        bloat_target = max(min_count, max_count - 2)
        if len(group_players) <= bloat_target:
            continue
        # Sort by market_value ascending — sell least valuable first
        group_players.sort(key=lambda p: p.market_value or 0)
        for player in group_players:
            if bloat_sold_count >= MAX_BLOAT_SELLS:
                break
            if _count_group(squad, group) <= bloat_target:
                break
            # Protect prospects: young players with meaningful value are assets, not surplus
            if (player.age or 99) < PROSPECT_AGE and (player.market_value or 0) >= PROSPECT_VALUE_THRESHOLD:
                continue
            squad.remove(player)
            sold.append(player)
            bloat_sold_count += 1
            fee = int((player.market_value or 0) * SELL_FEE_FACTOR)
            transfer_budget += fee

    return squad, sold, transfer_budget


def buy_phase(
    squad: list[Player],
    market: TransferMarket,
    transfer_budget: int,
    salary_budget: int,
    original_transfer_budget: int,
    mode: StrategyMode = "balanced",
) -> tuple[list[Player], list[Player], int, int]:
    """
    Run the buy phase: two-pass buying strategy.

    Pass 1 — Gap fill: buy best affordable player for any group below min.
    Pass 2 — Opportunistic: buy prime-age players for groups below max,
              as long as both budgets allow.

    Both passes respect the max cap, hard budget gates, single-signing cap, and total spend cap.
    Age range and spend limits are controlled by the strategy mode.

    Args:
        squad: Current squad after sell phase
        market: TransferMarket pool of available players
        transfer_budget: Remaining transfer budget in euros (after sells)
        salary_budget: Total annual salary budget in euros
        original_transfer_budget: Original budget before any spending (used for caps)
        mode: Strategy mode controlling buy age range, signing cap, and total spend cap

    Returns:
        Tuple of (updated_squad, players_bought, updated_transfer_budget, salary_budget_used)
    """
    _, prime_age_min, prime_age_max, single_signing_ratio, max_total_spend_ratio = _get_mode_params(mode)
    squad = list(squad)
    bought: list[Player] = []
    salary_used = _total_salary(squad)
    max_single_fee = int(original_transfer_budget * single_signing_ratio)
    # Total fees paid on purchases must not exceed this amount (conservative budget cap)
    max_total_fees = int(original_transfer_budget * max_total_spend_ratio)
    total_fees_paid = 0

    # Pass 1: Fill gaps (below min) — highest priority, no age filter
    made_purchase = True
    while made_purchase:
        made_purchase = False
        if total_fees_paid >= max_total_fees:
            break
        for group, (min_count, _) in POSITION_THRESHOLDS.items():
            if _count_group(squad, group) >= min_count:
                continue
            effective_cap = min(max_single_fee, max_total_fees - total_fees_paid)
            player, transfer_budget, salary_used, fee_paid = _buy_best_candidate(
                market, group, transfer_budget, salary_budget, salary_used,
                age_min=None, age_max=None, max_single_fee=effective_cap,
            )
            if player:
                squad.append(player)
                bought.append(player)
                total_fees_paid += fee_paid
                made_purchase = True

    # Pass 2: Opportunistic — buy within mode's prime age range while budget allows
    made_purchase = True
    while made_purchase:
        made_purchase = False
        if total_fees_paid >= max_total_fees:
            break
        for group, (_, max_count) in POSITION_THRESHOLDS.items():
            if _count_group(squad, group) >= max_count:
                continue
            effective_cap = min(max_single_fee, max_total_fees - total_fees_paid)
            player, transfer_budget, salary_used, fee_paid = _buy_best_candidate(
                market, group, transfer_budget, salary_budget, salary_used,
                age_min=prime_age_min, age_max=prime_age_max, max_single_fee=effective_cap,
            )
            if player:
                squad.append(player)
                bought.append(player)
                total_fees_paid += fee_paid
                made_purchase = True

    return squad, bought, transfer_budget, salary_used


def _buy_best_candidate(
    market: TransferMarket,
    group: str,
    transfer_budget: int,
    salary_budget: int,
    salary_used: int,
    age_min: int | None,
    age_max: int | None,
    max_single_fee: int,
) -> tuple[Player | None, int, int, int]:
    """
    Find and purchase the best affordable candidate for a position group.

    Filters by age range (for opportunistic buying) and single-signing fee cap.
    Returns (purchased_player_or_None, updated_transfer_budget, updated_salary_used, fee_paid).
    """
    salary_remaining = salary_budget - salary_used
    candidates = market.get_candidates(group, max_fee=transfer_budget)

    for candidate in candidates:
        fee = candidate.market_value or 0

        if fee > max_single_fee:
            continue

        # Age filter for opportunistic pass
        age = candidate.age or 0
        if age_min is not None and age < age_min:
            continue
        if age_max is not None and age > age_max:
            continue

        candidate_salary = estimate_salary(candidate.market_value)
        if candidate_salary > salary_remaining:
            continue

        # Purchase
        market.remove_player(candidate.player_id)
        transfer_budget -= fee
        salary_used += candidate_salary
        return candidate, transfer_budget, salary_used, fee

    return None, transfer_budget, salary_used, 0


# --- Private helpers ---

def _count_group(squad: list[Player], group: str) -> int:
    """Count players in a position group."""
    return sum(1 for p in squad if get_position_group(p.position) == group)


def _get_group(squad: list[Player], group: str) -> list[Player]:
    """Return players belonging to a position group."""
    return [p for p in squad if get_position_group(p.position) == group]


def _total_salary(squad: list[Player]) -> int:
    """Compute total estimated annual salary for a squad."""
    return sum(estimate_salary(p.market_value) for p in squad)
