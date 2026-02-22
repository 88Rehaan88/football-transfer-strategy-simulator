project-context.md

Football Transfer Simulator - Technical Challenge

Project Overview
This is a two-part technical assessment for a startup interview.
The goal is to demonstrate web scraping capabilities, full-stack engineering, system design, and AI integration.

-------------------------------------
INTERPRETATION OF REQUIREMENTS
-------------------------------------
This project will implement a rule-based transfer strategy simulator.
It is NOT intended to predict real-world outcomes or build a realistic football simulation engine.

Historical data will be used as a starting state.
Transfer decisions will be generated using defined strategy rules under budget constraints.

-------------------------------------
Part 1: Web Scraping Tool
-------------------------------------
Build a scraper that extracts football data from Transfermarkt (or similar site).

Inputs:
- Team Name
- Season (e.g., 2024-2025)

Required Data Entities:
- Players: name, age, current_club, birth_date, preferred_foot, nationality
- Transfers: player_id, from_club, to_club, transfer_fee, transfer_date
- Valuations: player_id, valuation_amount, valuation_date

Output Format:
- Structured JSON (primary)
- CSV export optional

Data will be stored locally (JSON or lightweight database).

-------------------------------------
Part 2: Interactive Web Application
-------------------------------------
Build a football transfer strategy simulator with AI integration.

Inputs:
- Club Name
- Starting Season
- Transfer Budget
- Salary Budget

System Flow:
1. Load historical squad data.
2. Apply rule-based transfer strategy under budget constraints.
3. Update squad state.
4. Compute KPIs (valuation change, net spend, squad age shift).
5. Generate AI-based strategic summary.

Outputs:
- Players bought/sold
- Updated squad list
- Squad valuation changes
- Net financial impact
- AI-generated season analysis

-------------------------------------
AI Component (Required)
-------------------------------------
Primary implementation:
- LLM-generated structured season summary based on simulation results.

Optional enhancements:
- Strategy comparison summaries
- Visualization dashboard of key metrics
- Risk analysis
- Financial sustainability commentary

-------------------------------------
NON-GOALS
-------------------------------------
- No match simulation
- No reinforcement learning
- No real-world prediction
- No multi-agent systems
- No advanced optimization engine

-------------------------------------
Deliverables
-------------------------------------
- Public GitHub repository
- Live deployment URL
- Professional README.md including:
  - Tech stack reasoning
  - Anti-scraping challenges
  - Architecture decisions
  - Limitations & trade-offs
  - Local setup instructions

-------------------------------------
Assessment Focus
-------------------------------------
- Clean architecture
- Modular backend design
- Proper separation of concerns
- Meaningful AI integration
- Code clarity and documentation quality
