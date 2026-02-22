"""
Prompt templates for Gemini AI analysis.

All prompts are deterministic and reproducible — they take structured data in
and request structured JSON out. No open-ended generation.
"""

import json
from strategy.models import SimulationResult


def build_season_summary_prompt(
    result: SimulationResult,
    position_stats: dict,
) -> str:
    """
    Build the prompt for a single-mode season analysis.

    Feeds structured simulation data (KPIs, transfers, position stats) to Gemini
    and requests a structured SeasonSummary JSON response.

    Args:
        result: Completed SimulationResult from the strategy engine
        position_stats: Dict with 'counts' and 'avg_age' keyed by position group
                        e.g. {"counts": {"GK": 2, "DEF": 5, ...}, "avg_age": {"GK": 31.0, ...}}
    """
    kpis = result.kpis

    # Format sold/bought lists so the model can reference names and numbers in its reply
    sold_lines = [
        f"  - {p.name} (age {p.age}, {p.position}, MV €{(p.market_value or 0):,})"
        for p in result.players_sold
    ]
    bought_lines = [
        f"  - {p.name} (age {p.age}, {p.position}, MV €{(p.market_value or 0):,})"
        for p in result.players_bought
    ]
    sold_block = "\n".join(sold_lines) if sold_lines else "  (none)"
    bought_block = "\n".join(bought_lines) if bought_lines else "  (none)"

    counts = position_stats.get("counts", {})
    avg_ages = position_stats.get("avg_age", {})
    position_counts_line = "  ".join(f"{g}: {counts.get(g, 0)}" for g in ["GK", "DEF", "MID", "ATT"])
    avg_age_line = "  ".join(
        f"{g}: {avg_ages.get(g, 'N/A')}" for g in ["GK", "DEF", "MID", "ATT"]
    )

    # One justification per transfer — we list them so the model doesn't miss anyone
    all_transfers = (
        [f"{p.name} (sold)" for p in result.players_sold]
        + [f"{p.name} (bought)" for p in result.players_bought]
    )
    transfers_list = "\n".join(f"  - {t}" for t in all_transfers) if all_transfers else "  (none)"

    prompt = f"""You are a football transfer analyst. Analyze the following transfer window simulation for {result.sim_input.team_name} ({result.sim_input.season}/{result.sim_input.season + 1} season).

== SIMULATION DATA ==

Club: {result.sim_input.team_name}
League: {result.sim_input.league}
Strategy mode: {result.sim_input.strategy_mode}

Transfer budget: €{result.sim_input.transfer_budget:,}
Salary budget:   €{result.sim_input.salary_budget:,}

Players sold ({len(result.players_sold)}):
{sold_block}

Players bought ({len(result.players_bought)}):
{bought_block}

KPIs:
  Squad valuation before: €{kpis.total_valuation_before:,}
  Squad valuation after:  €{kpis.total_valuation_after:,}
  Valuation change:       €{kpis.valuation_change:,}
  Net spend:              €{kpis.net_spend:,}
  Average age before:     {kpis.avg_age_before:.1f}
  Average age after:      {kpis.avg_age_after:.1f}
  Salary used:            €{kpis.salary_used:,} / €{kpis.salary_budget:,}
  Transfer budget remaining: €{kpis.transfer_budget_remaining:,}

Final squad position breakdown:
  Position counts: {position_counts_line}
  Average age by position: {avg_age_line}

Transfers requiring justification:
{transfers_list}

== TASK ==

Return ONLY a valid JSON object matching this exact schema. No markdown, no explanation outside the JSON (so we can parse it reliably):

{{
  "headline": "<1-3 sentence narrative summary of the entire transfer window — what happened, the strategic direction, and what it means for the club going forward>",
  "key_observations": [
    "<specific observation referencing actual players or numbers>",
    "<specific observation>",
    "<specific observation>"
  ],
  "financial_verdict": "<2-3 sentences assessing net spend, value for money, and salary sustainability>",
  "weakness": "<1-2 sentences identifying the most significant remaining squad weakness based on the position counts and average ages above>",
  "transfer_justifications": [
    {{
      "player_name": "<exact player name>",
      "decision": "<bought | sold>",
      "reasoning": "<1-2 sentences: why this decision was made + tactical or financial impact>"
    }}
  ]
}}

Rules:
- Include one entry in transfer_justifications for EVERY player sold and EVERY player bought.
- Be specific: reference player names, ages, fees, and position data.
- Do not be generic. Every sentence should be grounded in the numbers above.
"""
    return prompt  # Single string — no chat history; each run is independent


def build_comparison_prompt(
    results: list[SimulationResult],
    mode_summaries: list[dict],
) -> str:
    """
    Build the prompt for cross-strategy comparison.

    Receives summaries of all three strategy runs and asks Gemini to
    recommend the best mode with clear reasoning.
    """
    # All results share the same club/season — we only need the first
    club = results[0].sim_input.team_name
    league = results[0].sim_input.league
    season = results[0].sim_input.season

    summaries_block = json.dumps(mode_summaries, indent=2)  # Pre-formatted for the prompt

    prompt = f"""You are a football director advising {club} ({league}, {season}/{season + 1}).

Three transfer strategies were simulated for the same club with the same budget. Here are the results:

{summaries_block}

== TASK ==

Return ONLY a valid JSON object matching this exact schema. No markdown, no explanation outside the JSON:

{{
  "recommended_mode": "<balanced | conservative | win_now>",
  "recommendation_rationale": "<2-3 sentences on why this mode best fits the club's situation>",
  "tradeoff_analysis": "<2-3 sentences comparing the key tradeoffs between all three modes>"
}}

Be direct. Reference the actual numbers (net spend, valuation change, average age) to justify your recommendation.
"""
    return prompt
