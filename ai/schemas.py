"""
Pydantic schemas for AI-generated analysis output.

These are the structured responses that Gemini returns — not free-form text,
but typed, validated objects that the frontend can render meaningfully.
"""

from typing import Literal
from pydantic import BaseModel, Field


class TransferJustification(BaseModel):
    """AI reasoning for a single transfer decision (buy or sell)."""

    player_name: str
    decision: Literal["bought", "sold"]
    reasoning: str = Field(
        ...,
        description="1-2 sentences: why the decision was made + tactical/financial impact",
    )


class SeasonSummary(BaseModel):
    """
    Structured AI analysis of a single simulation run.
    Returned by Gemini after analyzing the full SimulationResult.
    """

    headline: str = Field(
        ...,
        description="1-3 sentence narrative summary of the entire transfer window — what happened, why, and what it means for the club",
    )
    key_observations: list[str] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="3-5 concrete bullet-point observations about what the strategy achieved",
    )
    financial_verdict: str = Field(
        ...,
        description="2-3 sentences assessing financial sustainability and value for money",
    )
    weakness: str = Field(
        ...,
        description="1-2 sentences identifying the most significant squad weakness remaining after the window, based on position counts and average ages",
    )
    transfer_justifications: list[TransferJustification] = Field(
        ...,
        description="One entry per player bought or sold, explaining the reasoning",
    )


class StrategyModeResult(BaseModel):
    """Summary of a single strategy mode, used inside a comparison."""

    mode: str = Field(..., description="Strategy mode name: rebuild | balanced | invest")
    headline: str
    net_spend_eur: int
    valuation_change_eur: int
    avg_age_after: float
    players_bought: int
    players_sold: int


class StrategyComparison(BaseModel):
    """
    AI comparison of all three strategy modes run on the same club/season.
    Provides a recommendation and cross-mode analysis.
    """

    recommended_mode: str = Field(
        ...,
        description="Which mode the AI recommends: balanced | conservative | win_now",
    )
    recommendation_rationale: str = Field(
        ...,
        description="2-3 sentences on why this mode best fits the club's situation",
    )
    mode_summaries: list[StrategyModeResult] = Field(
        ...,
        description="One entry per strategy mode with key stats",
    )
    tradeoff_analysis: str = Field(
        ...,
        description="2-3 sentences comparing the key tradeoffs between all three modes",
    )
