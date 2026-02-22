# Football Transfer Strategy Simulator

A rule-based football transfer window simulator with AI-powered analysis. Given a club, a season, and a budget, the engine simulates a full transfer window, selling aging or surplus players and buying replacements, then generates structured commentary using Google Gemini.

**Live demo:** https://football-transfer-strategy-simulator.onrender.com

---

## Stack

### Frontend
- Plain HTML, CSS, and JavaScript — no framework
- [Chart.js](https://www.chartjs.org/) (CDN) for squad valuation and budget visualizations

### Backend
- **FastAPI** — REST API and static file serving
- **Uvicorn** — ASGI server
- **Pydantic** — input validation and response schemas
- **python-dotenv** — environment variable management

### Scraper
- **requests** + **BeautifulSoup4** + **lxml** — scrapes squad and transfer data from Transfermarkt
- Anti-scraping measures: randomized delays (2–4s), browser-like headers, retry logic with exponential backoff

### AI
- **Google Gemini 2.0 Flash** (`google-genai`) — generates structured JSON analysis (headline, key observations, financial verdict, squad weakness, per-transfer justifications)

### Data
- Scraped data is cached as JSON files in `data/` and committed to the repository
- Supported: **5 LaLiga clubs × 4 seasons** (2022/23 – 2025/26)

---

## How to Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/88Rehaan88/football-transfer-strategy-simulator.git
cd football-transfer-strategy-simulator
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Gemini API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

You can get a free key at [https://aistudio.google.com](https://aistudio.google.com).

### 5. Start the server

```bash
python main.py serve
```

Open your browser at **http://127.0.0.1:8000**.

---

## Inputs

| Field | Description |
|---|---|
| Club Name | Dropdown — one of the 5 supported LaLiga clubs |
| Season | 2022, 2023, 2024, or 2025 |
| Transfer Budget | Available spend on player fees (€) |
| Salary Budget | Total annual wage bill allowed (€) |
| Strategy Mode | Balanced / Conservative / Win Now |

---

## Strategy Modes

| Mode | Behaviour |
|---|---|
| **Balanced** | Moderate age thresholds, spends full budget |
| **Conservative** | Sells earlier (29+), buys younger (19–24), caps total spend at 50% of budget |
| **Win Now** | Protects experienced players (sells only 35+), spends aggressively |

---

## Limitations & Trade-offs

### Data
- **LaLiga only** — scraped data covers 5 clubs (Real Madrid, FC Barcelona, Atletico Madrid, Real Sociedad, Villarreal) across 4 seasons. Other leagues are defined in the config but have no cached data.
- **Static market pool** — transfer candidates come from the other 4 LaLiga clubs in the same season, not the full global market. This limits the variety of available signings.
- **Transfermarkt dependency** — if the site structure changes, the scraper will need updating. Live scraping is only triggered when no cache exists.

### Simulation
- **One season at a time** — the engine simulates a single transfer window, not multi-year progression.
- **No match simulation** — squad quality is measured by market value, not actual performance metrics (goals, ratings, etc.).
- **Salary estimation** — annual salary is estimated as 10% of market value. Real contracts vary significantly from this.
- **Sell fees** — players are sold at 85% of their Transfermarkt market value. Real negotiations depend on contract length, demand, and other factors.
- **No loan market** — the engine only models permanent transfers.
- **B-team players included** — Transfermarkt squads include youth and reserve players, which inflates squad counts and can affect position group logic.

### AI
- **Gemini output is non-deterministic** — temperature is set to 0.3 for consistency, but responses can vary slightly between runs.
- **No hallucination guard** — the AI is grounded in the structured data passed to it, but is not cross-checked against external sources.
- **Requires API key** — the AI analysis step will fail if `GEMINI_API_KEY` is not set. The simulation itself still runs; only the commentary is affected.
