"""
Gemini AI analyst for transfer strategy commentary.

Consumes structured SimulationResult objects and returns structured
AI analysis — not free-form text, but typed Pydantic objects.
"""

import json
import os
from google import genai
from google.genai import types

from ai.schemas import SeasonSummary, StrategyComparison, StrategyModeResult
from ai.prompts import build_season_summary_prompt, build_comparison_prompt
from strategy.models import SimulationResult
from strategy.market import get_position_group

_MODEL = "gemini-2.0-flash"  # Fast and cheap; structured JSON output is enough for this task


def _get_client() -> genai.Client:
    """Initialise and return the Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is not set. "
            "Add it to your .env file before running."
        )
    return genai.Client(api_key=api_key)


def _compute_position_stats(result: SimulationResult) -> dict:
    """
    Compute position group counts and average ages from the final squad.

    Returns a dict with:
      "counts":  {"GK": int, "DEF": int, "MID": int, "ATT": int}
      "avg_age": {"GK": float, "DEF": float, "MID": float, "ATT": float}
    """
    groups = ["GK", "DEF", "MID", "ATT"]
    counts: dict[str, int] = {g: 0 for g in groups}
    age_sums: dict[str, list[int]] = {g: [] for g in groups}

    for player in result.squad_after:
        group = get_position_group(player.position)
        if group and group in counts:
            counts[group] += 1
            if player.age is not None:
                age_sums[group].append(player.age)

    avg_age: dict[str, float | str] = {}
    for g in groups:
        ages = age_sums[g]
        avg_age[g] = round(sum(ages) / len(ages), 1) if ages else "N/A"  # N/A if no players in group

    return {"counts": counts, "avg_age": avg_age}


def analyse_season(result: SimulationResult) -> SeasonSummary:
    """
    Generate a structured season summary for a single simulation run.

    Computes position stats from the final squad, then sends all structured
    data to Gemini and parses the response into a SeasonSummary object.

    Args:
        result: Completed SimulationResult from the strategy engine

    Returns:
        SeasonSummary with headline, observations, financial verdict,
        weakness, and per-transfer justifications
    """
    client = _get_client()
    position_stats = _compute_position_stats(result)
    prompt = build_season_summary_prompt(result, position_stats)

    response = client.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",  # Forces JSON output — easier to parse
            temperature=0.3,  # Some variation but mostly consistent structure
        ),
    )

    data = json.loads(response.text.strip())
    return SeasonSummary(**data)  # Pydantic validates and maps to our schema


def compare_strategies(results: list[SimulationResult]) -> StrategyComparison:
    """
    Compare results from multiple strategy modes and produce a recommendation.

    Args:
        results: List of SimulationResult objects, one per strategy mode

    Returns:
        StrategyComparison with recommended mode and tradeoff analysis
    """
    client = _get_client()

    # Two parallel lists: rich summaries for the prompt, typed summaries for the response
    mode_summaries = []
    mode_results: list[StrategyModeResult] = []

    for r in results:
        k = r.kpis
        # Full stats for Gemini to reason over
        summary = {
            "mode": r.sim_input.strategy_mode,
            "net_spend_eur": k.net_spend,
            "valuation_change_eur": k.valuation_change,
            "avg_age_before": k.avg_age_before,
            "avg_age_after": k.avg_age_after,
            "players_bought": len(r.players_bought),
            "players_sold": len(r.players_sold),
            "transfer_budget_remaining_eur": k.transfer_budget_remaining,
            "salary_used_eur": k.salary_used,
            "salary_budget_eur": k.salary_budget,
        }
        mode_summaries.append(summary)
        # Trimmed for StrategyModeResult — headline comes from AI in comparison response, we leave it blank
        mode_results.append(
            StrategyModeResult(
                mode=r.sim_input.strategy_mode,
                headline="",
                net_spend_eur=k.net_spend,
                valuation_change_eur=k.valuation_change,
                avg_age_after=k.avg_age_after,
                players_bought=len(r.players_bought),
                players_sold=len(r.players_sold),
            )
        )

    prompt = build_comparison_prompt(results, mode_summaries)
    response = client.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )

    comparison_data = json.loads(response.text.strip())
    # We already have mode_summaries as StrategyModeResult; AI only returns recommendation + rationale + tradeoffs
    return StrategyComparison(
        recommended_mode=comparison_data["recommended_mode"],
        recommendation_rationale=comparison_data["recommendation_rationale"],
        tradeoff_analysis=comparison_data["tradeoff_analysis"],
        mode_summaries=mode_results,
    )
