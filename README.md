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


- Squad & Financial KPIs: Tracks key metrics before and after the window — squad valuation change, net spend, average age shift, and salary usage — giving a clear picture of what the strategy achieved.

<img width="1421" height="758" alt="image" src="https://github.com/user-attachments/assets/a383971a-bdbb-43f7-961a-127d01eb2b92" />


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

