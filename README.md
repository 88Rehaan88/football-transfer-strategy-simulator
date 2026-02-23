# Football Transfer Strategy Simulator

A rule-based football transfer window simulator with AI-powered analysis. Given a club, a season, and a budget, the engine simulates a full transfer window, selling aging or surplus players and buying replacements, then generates structured commentary using Google Gemini.

**Live demo:** https://football-transfer-strategy-simulator.onrender.com

---

## Stack Used:

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
## Key Capabilities:

- Rule-Based Transfer Engine: Simulates a full transfer window using deterministic sell and buy rules. Sells aging or surplus players, then fills gaps and upgrades squads within your budget constraints.
  

<img width="1378" height="383" alt="image" src="https://github.com/user-attachments/assets/eed9cb6b-57a3-499d-9576-a1237f28a25c" />

-----

- Squad & Financial KPIs: Tracks key metrics before and after the window — squad valuation change, net spend, average age shift, and salary usage — giving a clear picture of what the strategy achieved.


<img width="1421" height="758" alt="image" src="https://github.com/user-attachments/assets/a383971a-bdbb-43f7-961a-127d01eb2b92" />

-----

- AI-Powered Analysis: After each simulation, Google Gemini analyses the transfers and generates a structured breakdown — including a headline summary, financial verdict, and squad weakness which shows where our team is lacking.


<img width="1420" height="510" alt="image" src="https://github.com/user-attachments/assets/9a530fe9-099b-44b1-b794-0919dd2d3012" />

  
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
| **Balanced** |	A middle-ground approach — moderate squad turnover with no specific spending restrictions |
| **Conservative** | Prioritizes financial caution and long-term squad building by selling aging players and buying young talent |
| **Win Now** | Maximizes short-term competitiveness by protecting experienced players and spending aggressively |

---

## Challenges Faced:
**1.Rate limiting and IP blocking:**
Transfermarkt rate-limits and blocks scrapers. During development we hit cooldown periods and had to switch networks (e.g., mobile hotspot) to continue scraping. The client uses randomized delays, retries with exponential backoff, and Retry-After support to reduce this risk.


**2. Inconsistent table structures:**
Transfermarkt uses nested tables inside <td> cells, repeated zentriert classes, mixed content (links, images, text), and rows with missing links (e.g. free agents). Instead of relying on class names, we anchor parsing to stable markers (h2[name="zugaenge"], table.items) and use positional extraction where structure is consistent. Malformed rows are skipped inside try/except so one bad row does not break the full scrape.

**3. Chart label clipping:**
Chart.js labels were cut off due to fixed heights and limited padding. We removed fixed CSS heights, used aspectRatio in Chart.js, added layout.padding, and switched the budget view from a doughnut to horizontal stacked bars so labels fit.

**4. Performance vs. data depth:**
Fetching extra data (e.g. per-player pages) would increase requests and rate-limiting risk. We kept scraping at club level (transfers + squad), separated HTTP from parsing, and structured the scraper so per-player enrichment could be added later without hard coupling.


## Limitations:

**Data scope** — Only LaLiga is supported (5 clubs: Real Madrid, Barcelona, Atletico Madrid, Real Sociedad, Villarreal) and only seasons 2022/23–2025/26.

**Decision inputs** — Transfer logic is based on age and finances. There is no performance data (goals, ratings, minutes), so the engine cannot incorporate recent form or in-game impact.

**Single data source** — All data comes from Transfermarkt. Layout or schema changes there would require scraper updates, and there is no fallback source.

**Market pool** — Buy options are limited to the other four LaLiga top clubs in the same season. There is no global transfer market or other leagues.

**No loan market** — Only permanent transfers are simulated; loans are ignored.

**Salary and fees** — Salary is estimated as 10% of market value; sell fees use 85% of market value. These are approximations, not real contract or negotiation data.


## Trade-offs:
**Static scraper** — We use requests + BeautifulSoup instead of a browser-based scraper. This reduces complexity and avoids headless Chrome/Playwright, but we cannot run JavaScript or handle heavily dynamic pages.

**Cached data in repo** — Scraped JSON is committed under data/ so deployment does not require live scraping. This increases repo size and makes updates manual, but avoids Transfermarkt calls in production.

**Simplified financial model** — Fixed rules (e.g. 85% sell fee, 10% salary) make the simulation fast and transparent, but less realistic than negotiation-based models.

## Future Work:
**Additional data sources** — Integrate performance stats (e.g. FBref, Opta) so decisions use form and output metrics, not just age and market value.

**More leagues and seasons** — Expand beyond LaLiga. The config already includes Premier League, Bundesliga, Serie A, and Ligue 1; only scraping and data need to be added.

**Multi-season runs** — Chain multiple transfer windows so users can simulate 2–3 seasons and see long-term squad evolution.

**Strategy comparison mode** — Run all three strategies and have the AI compare results and suggest the best fit for the club’s situation.

**Per-player enrichment (optional)** — Add optional per-player page scraping for richer data (e.g. valuation history), while keeping it modular and rate-limit aware.


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

