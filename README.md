# AfconPulse 🏆🇲🇦
<!-- This app was built by CeeJay for Chinedum Aranotu – 2026 -->

![Status](https://img.shields.io/badge/status-live-brightgreen)
![Stack](https://img.shields.io/badge/stack-React%20%2B%20FastAPI%20%2B%20ntscraper-blue)
![AI](https://img.shields.io/badge/AI-Claude%20Sonnet%204-purple)
![License](https://img.shields.io/badge/license-MIT-green)

> Real-time Twitter/X sentiment analysis dashboard tracking the AFCON 2025 controversy — 
> Morocco awarded the title by CAF after Senegal forfeited, two months after the final.

## 🔑 Why ntscraper Instead of the Twitter API

The Twitter/X free tier only allows **posting** — no search, no read access.
Basic tier is $100/month. We use **[ntscraper](https://github.com/bocchilorenzo/ntscraper)** instead:
- Scrapes [Nitter](https://nitter.net) (a Twitter frontend proxy)
- Zero API keys, zero cost
- Searches by term, hashtag, or user
- Returns tweets with full stats (likes, retweets, etc.)

> ⚠️ Nitter instances go up and down. If scraping fails, the backend retries with the next instance.
> The `utils/nitter_health.py` module checks instance health automatically.

---

## 📁 Project Structure

```
afcon-pulse/
├── backend/                    ← Python FastAPI + ntscraper
│   ├── main.py                 ← API server, scraper, sentiment engine
│   ├── utils/
│   │   └── nitter_health.py    ← Nitter instance health-checker
│   ├── requirements.txt
│   ├── Procfile                ← Railway deploy
│   ├── railway.json
│   └── .env                    ← ANTHROPIC_API_KEY
│
├── frontend/                   ← React + Vite dashboard
│   ├── src/
│   │   ├── components/
│   │   │   └── AFCONDashboard.jsx
│   │   ├── hooks/
│   │   │   └── useAfconData.js ← Connects to backend
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── .env                    ← VITE_API_URL
│   └── vite.config.js
│
└── README.md
```

---

## 🚀 Local Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env

# Run server
uvicorn main:app --reload --port 8000
```

Test it:
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/tweets/afcon
```

> ⏱ First request takes 30–90 seconds (scraping + Claude analysis). Subsequent requests hit the 5-min cache instantly.

### 2. Frontend

```bash
cd frontend
npm create vite@latest . -- --template react
npm install recharts

# Copy AFCONDashboard.jsx → src/components/
# Copy useAfconData.js    → src/hooks/

# Create .env
echo "VITE_API_URL=http://localhost:8000" > .env

# Run
npm run dev
```

---

## 🌐 Deploy

### Backend → Railway

```bash
cd backend
railway login
railway new afcon-pulse-backend
railway up

# Set env vars in Railway dashboard:
# ANTHROPIC_API_KEY = sk-ant-...
# FRONTEND_URL = https://afcon-pulse.vercel.app
```

### Frontend → Vercel

```bash
cd frontend
vercel --prod

# Set env var in Vercel dashboard:
# VITE_API_URL = https://afcon-pulse-backend.railway.app
```

---

## 📊 Metrics Explained

| Metric | What It Measures |
|---|---|
| **Sentiment Score** | -1 (pure anger) to +1 (pure joy). Average across all tweets. |
| **Weighted Score** | Engagement-weighted — Drogba's 234K-like tweet counts more than a 5-like tweet. |
| **Controversy Index** | 0–100. Based on pos/neg balance + negative ratio. >60 = very controversial. |
| **Stance Split** | Pro-Morocco / Pro-Senegal / Neutral-Observer. More useful than raw +/- here. |
| **Sentiment Velocity** | Rate of change per hour — shows when news events spike. |
| **Emotion Breakdown** | joy, anger, pride, disbelief, frustration extracted by Claude from tweet text. |
| **Hashtag Battle** | #MoroccoChampions vs #StolenTitle — which narrative is winning. |
| **Geographic Split** | North Africa = positive. West Africa = negative. Global = mixed. |

---

## 🔑 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Health check + cache status |
| `/api/tweets/afcon` | GET | Full tweet list + metrics (5-min cache) |
| `/api/tweets/afcon?force_refresh=true` | GET | Bypass cache, fetch fresh |
| `/api/tweets/afcon/metrics` | GET | Aggregated metrics only (no tweets) |
| `/api/analyze/single` | POST | Analyze one tweet `{ "text": "..." }` |

---

## 📝 License

MIT — free to use and modify.

---

> // This app was built by CeeJay for Chinedum Aranotu – 2026
