# This app was built by CeeJay for Chinedum Aranotu – 2026
# AfconPulse — Python Backend: ntscraper + Claude AI + Geographic Breakdown

import os
import json
import time
import logging
import re
from datetime import datetime
from collections import Counter, defaultdict

import anthropic
from ntscraper import Nitter
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="AfconPulse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", os.getenv("FRONTEND_URL", "*")],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── CLIENTS ──────────────────────────────────────────────────────────────────
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
scraper = Nitter(log_level=1)

# ─── SEARCH TERMS ─────────────────────────────────────────────────────────────
AFCON_QUERIES = [
    "#AFCON2025",
    "#MoroccoChampions",
    "#StolenTitle",
    "#CAFRuling",
    "Morocco AFCON Senegal",
    "#CASAppeal AFCON",
    "Senegal AFCON forfeit",
]

# ─── GEOGRAPHIC SIGNAL RULES ──────────────────────────────────────────────────
# ntscraper doesn't return geo coords, so we infer region from tweet text + hashtags.
# Each tuple: (regex_pattern, region_label, country_code)

GEO_SIGNALS: list[tuple[str, str, str]] = [
    # ── North Africa ───────────────────────────────────────────────────────────
    (r"\b(maroc|morocco|moroccan|rabat|casablanca|atlas lion|hakimi|brahim)\b",   "North Africa", "MA"),
    (r"\b(algérie|algeria|algerian|alger)\b",                                     "North Africa", "DZ"),
    (r"\b(tunisie|tunisia|tunisian|tunis)\b",                                     "North Africa", "TN"),
    (r"\b(égypte|egypt|egyptian|cairo|salah|al-ahly)\b",                          "North Africa", "EG"),
    (r"\b(libye|libya|libyan|tripoli)\b",                                         "North Africa", "LY"),
    # Arabic script (high confidence MENA/North Africa)
    (r"[\u0600-\u06FF]{5,}",                                                      "North Africa", "AR"),

    # ── West Africa ────────────────────────────────────────────────────────────
    (r"\b(senegal|sénégal|senegalese|dakar|teranga|sadio|mane|gueye|koulibaly)\b","West Africa",  "SN"),
    (r"\b(nigeria|nigerian|lagos|abuja|super eagle)\b",                           "West Africa",  "NG"),
    (r"\b(ghana|ghanaian|accra|black star)\b",                                    "West Africa",  "GH"),
    (r"\b(ivory coast|côte d.ivoire|ivorian|abidjan|drogba)\b",                   "West Africa",  "CI"),
    (r"\b(mali|malian|bamako)\b",                                                 "West Africa",  "ML"),
    (r"\b(cameroon|cameroonian|yaoundé|lion indomptable)\b",                      "West Africa",  "CM"),
    (r"\b(guinea|guinean|conakry)\b",                                             "West Africa",  "GN"),
    (r"\b(burkina|burkinabe|ouagadougou)\b",                                      "West Africa",  "BF"),
    # Wolof keywords (strongly Senegal)
    (r"\b(xam|baye|ndank|yow|nekk|dafa|waaw)\b",                                  "West Africa",  "SN"),

    # ── East Africa ────────────────────────────────────────────────────────────
    (r"\b(ethiopia|ethiopian|addis ababa)\b",                                     "East Africa",  "ET"),
    (r"\b(kenya|kenyan|nairobi|harambee)\b",                                      "East Africa",  "KE"),
    (r"\b(tanzania|tanzanian|dar es salaam)\b",                                   "East Africa",  "TZ"),
    (r"\b(uganda|ugandan|kampala)\b",                                             "East Africa",  "UG"),

    # ── Central Africa ─────────────────────────────────────────────────────────
    (r"\b(dr congo|drc|congolese|kinshasa|leopards)\b",                           "Central Africa","CD"),
    (r"\b(gabon|gabonese|libreville)\b",                                          "Central Africa","GA"),

    # ── Southern Africa ────────────────────────────────────────────────────────
    (r"\b(south africa|south african|johannesburg|cape town|bafana)\b",           "Southern Africa","ZA"),
    (r"\b(zimbabwe|zimbabwean|harare|warriors)\b",                                "Southern Africa","ZW"),
    (r"\b(zambia|zambian|lusaka|chipolopolo)\b",                                  "Southern Africa","ZM"),

    # ── Europe ─────────────────────────────────────────────────────────────────
    (r"\b(france|french|paris|psg|ligue 1|stade de france)\b",                    "Europe",       "FR"),
    (r"\b(spain|spanish|madrid|barcelona|laliga|real madrid|atletico)\b",         "Europe",       "ES"),
    (r"\b(england|english|london|premier league|arsenal|chelsea|liverpool)\b",    "Europe",       "GB"),
    (r"\b(germany|german|bundesliga|berlin|münchen|munich)\b",                    "Europe",       "DE"),
    (r"\b(italy|italian|serie a|juventus|milan|roma)\b",                          "Europe",       "IT"),
    (r"\b(portugal|portuguese|porto|benfica|sporting)\b",                         "Europe",       "PT"),
    # French West African diaspora signal
    (r"\b(voler|volé|honte|bravo|champion|injuste|arbitre|scandale|inacceptable)\b","Europe",     "FR"),

    # ── Middle East ────────────────────────────────────────────────────────────
    (r"\b(saudi|riyadh|jeddah|ksa|saudi arabia)\b",                               "Middle East",  "SA"),
    (r"\b(qatar|doha|al-kass)\b",                                                 "Middle East",  "QA"),
    (r"\b(emirates|dubai|abu dhabi|uae)\b",                                       "Middle East",  "AE"),

    # ── Americas ───────────────────────────────────────────────────────────────
    (r"\b(usa|united states|american|new york|los angeles|mls|usmnt)\b",          "Americas",     "US"),
    (r"\b(brazil|brasil|brazilian|são paulo|rio)\b",                              "Americas",     "BR"),
    (r"\b(canada|canadian|toronto|cf montréal)\b",                                "Americas",     "CA"),
]

REGION_CONTEXT = {
    "North Africa":    "Morocco home region + Arab world — strongly pro-Morocco",
    "West Africa":     "Senegal's backyard + rivals — deeply divided, high anger",
    "East Africa":     "Neutral observers — skeptical of CAF governance",
    "Central Africa":  "Mixed — some suspicion of host-nation bias",
    "Southern Africa": "Neutral — concern about African football integrity",
    "Europe":          "Large Moroccan + Senegalese diaspora (esp. France) — polarised",
    "Middle East":     "Pan-Arab solidarity with Morocco — likely positive",
    "Americas":        "Neutral diaspora — academic interest + fairness debate",
    "Unknown":         "No region signal detected in tweet",
}


def detect_region(tweet: dict) -> tuple[str, str]:
    """
    Returns (region_label, country_code).
    Scans tweet text + hashtags for geographic signals.
    """
    text = (
        tweet.get("text", "") + " " + " ".join(tweet.get("hashtags", []))
    ).lower()

    for pattern, region, code in GEO_SIGNALS:
        if re.search(pattern, text, re.IGNORECASE):
            return region, code

    return "Unknown", "??"


def compute_geo_breakdown(enriched_tweets: list[dict]) -> dict:
    """
    Groups tweets by region, returns per-region sentiment metrics.
    """
    region_buckets: dict[str, dict] = defaultdict(lambda: {
        "tweet_count": 0,
        "sentiment_counts": {"positive": 0, "neutral": 0, "negative": 0},
        "scores": [],
        "country_tally": Counter(),
        "hashtag_tally": Counter(),
    })

    for tweet in enriched_tweets:
        region = tweet.get("region", "Unknown")
        code   = tweet.get("country_code", "??")
        rb     = region_buckets[region]

        rb["tweet_count"] += 1
        rb["sentiment_counts"][tweet.get("sentiment", "neutral")] += 1
        rb["scores"].append(tweet.get("score", 0.0))
        rb["country_tally"][code] += 1
        for tag in tweet.get("hashtags", []):
            rb["hashtag_tally"][tag.lower()] += 1

    result = []
    for region, rb in sorted(region_buckets.items(), key=lambda x: -x[1]["tweet_count"]):
        scores  = rb["scores"]
        total   = rb["tweet_count"] or 1
        counts  = rb["sentiment_counts"]
        avg_scr = round(sum(scores) / len(scores), 3) if scores else 0.0
        dominant = max(counts, key=counts.get)

        result.append({
            "region":        region,
            "tweet_count":   rb["tweet_count"],
            "avg_score":     avg_scr,
            "dominant":      dominant,
            "pct_positive":  round(counts["positive"] / total * 100, 1),
            "pct_neutral":   round(counts["neutral"]  / total * 100, 1),
            "pct_negative":  round(counts["negative"] / total * 100, 1),
            "top_countries": rb["country_tally"].most_common(3),
            "top_hashtags":  rb["hashtag_tally"].most_common(5),
            "context":       REGION_CONTEXT.get(region, ""),
        })

    geotagged = sum(r["tweet_count"] for r in result if r["region"] != "Unknown")
    unknown   = region_buckets.get("Unknown", {}).get("tweet_count", 0)

    return {
        "by_region":       result,
        "total_geotagged": geotagged,
        "total_unknown":   unknown,
        "geo_coverage_pct": round(geotagged / (geotagged + unknown) * 100, 1) if (geotagged + unknown) > 0 else 0,
    }

# ─── SCRAPER ──────────────────────────────────────────────────────────────────
def scrape_tweets(max_per_query: int = 20) -> list[dict]:
    all_tweets = []
    seen_ids   = set()

    for query in AFCON_QUERIES:
        try:
            log.info(f"Scraping: {query}")
            result = scraper.get_tweets(query, mode="term", number=max_per_query)
            for tweet in result.get("tweets", []):
                tid = tweet.get("link", tweet.get("id", ""))
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    all_tweets.append(tweet)
            time.sleep(1.5)
        except Exception as e:
            log.warning(f"Failed query '{query}': {e}")

    log.info(f"Scraped {len(all_tweets)} unique tweets")
    return all_tweets


def normalize_tweet(raw: dict) -> dict:
    stats = raw.get("stats", {})
    user  = raw.get("user",  {})
    return {
        "id":        raw.get("link", ""),
        "text":      raw.get("text", ""),
        "author": {
            "name":     user.get("name",     "Unknown"),
            "username": user.get("username", ""),
            "avatar":   user.get("avatar",   ""),
            "verified": user.get("verified", False),
        },
        "date":      raw.get("date", ""),
        "likes":     _parse_stat(stats.get("likes",    0)),
        "retweets":  _parse_stat(stats.get("retweets", 0)),
        "comments":  _parse_stat(stats.get("comments", 0)),
        "hashtags":  raw.get("hashtags", []),
        "is_retweet": raw.get("retweet", False),
    }


def _parse_stat(val) -> int:
    if isinstance(val, int): return val
    if isinstance(val, str):
        val = val.strip().replace(",", "")
        if val.endswith("K"): return int(float(val[:-1]) * 1_000)
        if val.endswith("M"): return int(float(val[:-1]) * 1_000_000)
        try: return int(val)
        except ValueError: return 0
    return 0

# ─── SENTIMENT ENGINE ─────────────────────────────────────────────────────────
CONTEXT = (
    "Morocco was awarded the 2025 AFCON title by the CAF Appeal Board on March 17, 2026. "
    "Senegal had won the final 1-0 on the pitch but briefly walked off in protest of a penalty "
    "awarded to Morocco in stoppage time. CAF declared Senegal forfeited (3-0 Morocco). "
    "Senegal is appealing to CAS. Drogba called it 'stolen'. Morocco last won AFCON in 1976."
)

def analyze_sentiment_batch(tweets: list[dict]) -> list[dict]:
    results    = []
    BATCH_SIZE = 15

    for i in range(0, len(tweets), BATCH_SIZE):
        batch    = tweets[i:i + BATCH_SIZE]
        numbered = "\n".join(
            f'[{j}] ID:{t["id"]} — "{t["text"][:280]}"'
            for j, t in enumerate(batch)
        )
        prompt = f"""Context: {CONTEXT}

Analyze the sentiment of each tweet. Return ONLY a valid JSON array — no markdown.

Each element:
{{
  "index": <int>,
  "id": "<tweet id>",
  "sentiment": "positive"|"neutral"|"negative",
  "score": <float -1.0 to 1.0>,
  "confidence": <float 0–1>,
  "side": "pro-Morocco"|"pro-Senegal"|"neutral-observer",
  "emotions": {{"joy":<0-1>,"anger":<0-1>,"pride":<0-1>,"disbelief":<0-1>,"frustration":<0-1>}},
  "summary": "<one sentence>",
  "keywords": ["word1","word2","word3"]
}}

Tweets:
{numbered}"""

        try:
            msg = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            raw    = msg.content[0].text.replace("```json","").replace("```","").strip()
            parsed = json.loads(raw)
            results.extend(parsed)
            time.sleep(0.5)
        except Exception as e:
            log.error(f"Batch {i // BATCH_SIZE} failed: {e}")
            for j, t in enumerate(batch):
                results.append({
                    "index": j, "id": t["id"],
                    "sentiment": "neutral", "score": 0.0, "confidence": 0.5,
                    "side": "neutral-observer",
                    "emotions": {"joy":0,"anger":0,"pride":0,"disbelief":0,"frustration":0},
                    "summary": "Analysis unavailable.", "keywords": []
                })

    return results


def compute_aggregate_metrics(enriched: list[dict]) -> dict:
    if not enriched: return {}

    sentiments = [t["sentiment"] for t in enriched if t.get("sentiment")]
    scores     = [t["score"]     for t in enriched if t.get("score") is not None]
    pos, neu, neg = (sentiments.count(s) for s in ("positive","neutral","negative"))
    total = len(sentiments) or 1

    total_eng   = sum((t.get("likes",0) + t.get("retweets",0)*2) for t in enriched) or 1
    w_score     = sum(t.get("score",0) * (t.get("likes",0) + t.get("retweets",0)*2) for t in enriched) / total_eng
    sides       = [t.get("side","neutral-observer") for t in enriched]
    all_tags    = [h.lower() for t in enriched for h in t.get("hashtags",[])]
    top_tags    = Counter(all_tags).most_common(10)
    balance     = 1 - abs(pos - neg) / total
    controversy = round((balance * 0.6 + (neg / total) * 0.4) * 100, 1)

    return {
        "total_tweets":        len(enriched),
        "sentiment_breakdown": {"positive": pos, "neutral": neu, "negative": neg},
        "sentiment_pct":       {
            "positive": round(pos / total * 100, 1),
            "neutral":  round(neu / total * 100, 1),
            "negative": round(neg / total * 100, 1),
        },
        "avg_score":           round(sum(scores) / len(scores), 3) if scores else 0,
        "weighted_score":      round(w_score, 3),
        "controversy_index":   controversy,
        "stance_breakdown":    {
            "pro_morocco": sides.count("pro-Morocco"),
            "pro_senegal": sides.count("pro-Senegal"),
            "neutral":     sides.count("neutral-observer"),
        },
        "top_hashtags": [{"tag": f"#{t}", "count": c} for t, c in top_tags],
        "fetched_at":   datetime.utcnow().isoformat() + "Z",
    }

# ─── CACHE ────────────────────────────────────────────────────────────────────
class Cache:
    def __init__(self, ttl=300):
        self.data, self.fetched_at, self.ttl = None, 0, ttl
    def is_fresh(self):
        return self.data is not None and (time.time() - self.fetched_at) < self.ttl
    def set(self, data):
        self.data, self.fetched_at = data, time.time()

tweet_cache = Cache(ttl=300)

# ─── ROUTES ───────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "AfconPulse API online", "version": "1.0.0"}

@app.get("/api/health")
def health():
    return {"ok": True, "cache_fresh": tweet_cache.is_fresh()}

@app.get("/api/tweets/afcon")
def get_afcon_tweets(force_refresh: bool = False):
    if not force_refresh and tweet_cache.is_fresh():
        log.info("Serving from cache")
        return tweet_cache.data

    raw_tweets = scrape_tweets(max_per_query=20)
    if not raw_tweets:
        raise HTTPException(503, "No tweets scraped — Nitter instances may be down")

    normalized        = [normalize_tweet(t) for t in raw_tweets if not t.get("retweet", False)]
    sentiment_results = analyze_sentiment_batch(normalized)
    sentiment_map     = {s["id"]: s for s in sentiment_results}

    enriched = []
    for tweet in normalized:
        s              = sentiment_map.get(tweet["id"], {})
        region, code   = detect_region(tweet)
        enriched.append({
            **tweet,
            "sentiment":    s.get("sentiment",  "neutral"),
            "score":        s.get("score",       0.0),
            "confidence":   s.get("confidence",  0.5),
            "side":         s.get("side",        "neutral-observer"),
            "emotions":     s.get("emotions",    {}),
            "summary":      s.get("summary",     ""),
            "keywords":     s.get("keywords",    []),
            "region":       region,
            "country_code": code,
        })

    metrics  = compute_aggregate_metrics(enriched)
    geo      = compute_geo_breakdown(enriched)
    response = {"tweets": enriched, "metrics": metrics, "geo": geo}
    tweet_cache.set(response)
    return response

@app.get("/api/tweets/afcon/metrics")
def get_metrics_only():
    if not tweet_cache.is_fresh():
        raise HTTPException(503, "No cached data — call /api/tweets/afcon first")
    return tweet_cache.data.get("metrics", {})

@app.get("/api/tweets/afcon/geo")
def get_geo_only():
    """Geographic breakdown only — lightweight polling endpoint."""
    if not tweet_cache.is_fresh():
        raise HTTPException(503, "No cached data — call /api/tweets/afcon first")
    return tweet_cache.data.get("geo", {})

class SingleTweetRequest(BaseModel):
    text: str

@app.post("/api/analyze/single")
def analyze_single_tweet(body: SingleTweetRequest):
    if not body.text.strip():
        raise HTTPException(400, "Tweet text cannot be empty")

    mock     = {"text": body.text, "hashtags": []}
    region, code = detect_region(mock)

    prompt = f"""Context: {CONTEXT}

Analyze this tweet. Return ONLY valid JSON — no markdown.

{{
  "sentiment": "positive"|"neutral"|"negative",
  "score": <float -1.0 to 1.0>,
  "confidence": <float 0–1>,
  "side": "pro-Morocco"|"pro-Senegal"|"neutral-observer",
  "emotions": {{"joy":<0-1>,"anger":<0-1>,"pride":<0-1>,"disbelief":<0-1>,"frustration":<0-1>}},
  "summary": "<one sentence>",
  "keywords": ["word1","word2","word3"]
}}

Tweet: "{body.text}" """

    try:
        msg = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw    = msg.content[0].text.replace("```json","").replace("```","").strip()
        result = json.loads(raw)
        result["region"]       = region
        result["country_code"] = code
        result["region_context"] = REGION_CONTEXT.get(region, "")
        return result
    except json.JSONDecodeError as e:
        raise HTTPException(500, f"Parse error: {e}")
    except anthropic.APIError as e:
        raise HTTPException(502, f"Anthropic API error: {e}")
