"""
CLI entry point.

Commands:
  scrape    — Scrape a club's squad and transfers, save to data/
  simulate  — Run a full transfer simulation for a club and season
  serve     — Start the FastAPI web server

Usage examples:
  python main.py scrape --club-slug fc-barcelona --club-id 131 --team-name "FC Barcelona" --season 2024
  python main.py simulate --club-slug fc-barcelona --club-id 131 --team-name "FC Barcelona" --season 2024 --league laliga --transfer-budget 100000000 --salary-budget 300000000
  python main.py serve
  python main.py serve --port 8080
"""

import argparse
import json
import sys
from dotenv import load_dotenv

# Load .env file before any module that reads environment variables
load_dotenv()

# Force UTF-8 output on Windows to handle special characters in player names
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from scraper.scraper import scrape_team
from scraper.storage import save_result
from strategy.engine import run_simulation
from strategy.models import SimulationInput


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Football Transfer Simulator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- scrape command ---
    scrape = subparsers.add_parser("scrape", help="Scrape squad and transfers for a club")
    scrape.add_argument("--club-slug", required=True)
    scrape.add_argument("--club-id", required=True)
    scrape.add_argument("--team-name", required=True)
    scrape.add_argument("--season", required=True, type=int)

    # --- simulate command ---
    sim = subparsers.add_parser("simulate", help="Run a transfer simulation")
    sim.add_argument("--club-slug", required=True)
    sim.add_argument("--club-id", required=True)
    sim.add_argument("--team-name", required=True)
    sim.add_argument("--season", required=True, type=int)
    sim.add_argument("--league", required=True, help="League key, e.g. laliga")
    sim.add_argument("--transfer-budget", required=True, type=int, help="Transfer budget in euros")
    sim.add_argument("--salary-budget", required=True, type=int, help="Annual salary budget in euros")
    sim.add_argument("--strategy-mode", default="balanced", choices=["balanced", "conservative", "win_now"])

    # --- serve command ---
    serve = subparsers.add_parser("serve", help="Start the FastAPI web server")
    serve.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    serve.add_argument("--port", default=8000, type=int, help="Port to listen on (default: 8000)")
    serve.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    return parser


def cmd_scrape(args: argparse.Namespace) -> None:
    result = scrape_team(
        club_slug=args.club_slug,
        club_id=args.club_id,
        team_name=args.team_name,
        season_start_year=args.season,
    )
    print(f"Scraped: {len(result.players)} players, {len(result.transfers)} transfers")
    filepath = save_result(result)
    print(f"Saved to: {filepath}")


def cmd_simulate(args: argparse.Namespace) -> None:
    sim_input = SimulationInput(
        club_slug=args.club_slug,
        club_id=args.club_id,
        team_name=args.team_name,
        season=args.season,
        league=args.league,
        transfer_budget=args.transfer_budget,
        salary_budget=args.salary_budget,
        strategy_mode=args.strategy_mode,
    )

    result = run_simulation(sim_input)

    print("\n" + "=" * 50)
    print("SIMULATION COMPLETE")
    print("=" * 50)
    print(f"Club:            {sim_input.team_name} ({sim_input.season}/{str(sim_input.season + 1)[-2:]})")
    print(f"Players sold:    {len(result.players_sold)}")
    print(f"Players bought:  {len(result.players_bought)}")
    print(f"Squad size:      {len(result.squad_before)} -> {len(result.squad_after)}")
    print()
    print("--- KPIs ---")
    k = result.kpis
    print(f"Squad valuation: EUR {k.total_valuation_before:,} -> EUR {k.total_valuation_after:,}  (change: EUR {k.valuation_change:,})")
    print(f"Net spend:       EUR {k.net_spend:,}")
    print(f"Avg age:         {k.avg_age_before} -> {k.avg_age_after}")
    print(f"Salary used:     EUR {k.salary_used:,} / EUR {sim_input.salary_budget:,}")
    print(f"Transfer budget: EUR {k.transfer_budget_remaining:,} remaining")

    if result.players_sold:
        print("\n--- Sold ---")
        for p in result.players_sold:
            print(f"  {p.name} ({p.age}, {p.position}) - EUR {p.market_value:,}" if p.market_value else f"  {p.name}")

    if result.players_bought:
        print("\n--- Bought ---")
        for p in result.players_bought:
            print(f"  {p.name} ({p.age}, {p.position}) - EUR {p.market_value:,}" if p.market_value else f"  {p.name}")


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn
    print(f"Starting server at http://{args.host}:{args.port}")
    print("Open your browser at the URL above to use the simulator.")
    uvicorn.run(
        "api.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scrape":
        cmd_scrape(args)
    elif args.command == "simulate":
        cmd_simulate(args)
    elif args.command == "serve":
        cmd_serve(args)


if __name__ == "__main__":
    main()
