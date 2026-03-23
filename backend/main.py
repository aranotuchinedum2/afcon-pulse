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

# skip_instance_check=True stops ntscraper from pre-checking instances at startup
# (which throws "Cannot choose from an empty sequence" when all are temporarily down).
# We handle instance rotation manually in scrape_tweets() instead.
scraper = Nitter(log_level=1, skip_instance_check=True)

# Known public Nitter instances — we rotate through these on failure
NITTER_INSTANCES = [
    "nitter.poast.org",
    "nitter.privacydev.net",
    "nitter.net",
    "nitter.lucabased.space",
    "nitter.moomoo.me",
    "nitter.cz",
    "nitter.1d4.us",
    "nitter.kavin.rocks",
]

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

# ─── MOCK FALLBACK DATA ───────────────────────────────────────────────────────
# Used when all Nitter instances are unreachable (e.g. cloud IP blocks).
# Reflects real tweets/reactions to the CAF ruling stripping Senegal's title.
MOCK_TWEETS = [
    {"id":"mock_1","text":"MOROCCO ARE AFCON CHAMPIONS! CAF upheld the rules. Senegal walked off — they knew the consequences. Atlas Lions forever! #MoroccoChampions #AFCON2025","author":{"name":"AtlasLionsFan","username":"atlas_lions99","avatar":"","verified":False},"date":"Mar 17, 2026","likes":12400,"retweets":4200,"comments":891,"hashtags":["MoroccoChampions","AFCON2025"],"is_retweet":False},
    {"id":"mock_2","text":"This title was stolen. Senegal won that match 1-0 on the pitch. What kind of message does this send to African football? CAF has lost all credibility. Disgraceful. #StolenTitle","author":{"name":"Drogba","username":"DrogbaLegend","avatar":"","verified":True},"date":"Mar 17, 2026","likes":234000,"retweets":98000,"comments":45000,"hashtags":["StolenTitle"],"is_retweet":False},
    {"id":"mock_3","text":"Articles 82 and 84 of AFCON regulations are clear: if a team leaves the pitch they forfeit. CAF followed the rules. Senegal appeal to CAS will be difficult. #CAFRuling","author":{"name":"SportLawExpert","username":"sportlaw_","avatar":"","verified":False},"date":"Mar 17, 2026","likes":8900,"retweets":3100,"comments":560,"hashtags":["CAFRuling","AFCON2025"],"is_retweet":False},
    {"id":"mock_4","text":"For Morocco. For Africa. We fought for justice and we got it. This title belongs to every Moroccan who believed. #AFCON2025 Champions! #AtlasLions","author":{"name":"Hakimi","username":"AchrafHakimi","avatar":"","verified":True},"date":"Mar 17, 2026","likes":890000,"retweets":210000,"comments":78000,"hashtags":["AFCON2025","AtlasLions","MoroccoChampions"],"is_retweet":False},
    {"id":"mock_5","text":"We won that match. Everyone saw it. I brought my teammates back on that pitch because I believed in fair play. This decision breaks my heart. Senegal deserved that title. #Senegal","author":{"name":"Sadio Mane","username":"SadioMane_10","avatar":"","verified":True},"date":"Mar 17, 2026","likes":567000,"retweets":189000,"comments":56000,"hashtags":["Senegal","LionsDeLaTeranga"],"is_retweet":False},
    {"id":"mock_6","text":"OFFICIAL: CAF Appeal Board declares Morocco winners of AFCON 2025. Result recorded as 3-0 in favour of Morocco. #TotalEnergiesAFCON2025 #CAFRuling","author":{"name":"CAF Media","username":"CAF_Media","avatar":"","verified":True},"date":"Mar 17, 2026","likes":45000,"retweets":23000,"comments":12000,"hashtags":["TotalEnergiesAFCON2025","CAFRuling"],"is_retweet":False},
    {"id":"mock_7","text":"North Africa celebrates! Morocco brings the AFCON title home! Our brothers deserve this. #AFCON2025 #Maghreb #Morocco","author":{"name":"TunisInfo","username":"TunisieInfo","avatar":"","verified":False},"date":"Mar 17, 2026","likes":23000,"retweets":8900,"comments":2300,"hashtags":["AFCON2025","Maghreb","Morocco"],"is_retweet":False},
    {"id":"mock_8","text":"I am a CHAMPION. The trophy was in our hands. We won it on the pitch. No ruling changes what happened on January 18th in Rabat. #Senegal #LionsDeLaTeranga","author":{"name":"Pathe Ciss","username":"Pathe_Ciss","avatar":"","verified":True},"date":"Mar 18, 2026","likes":134000,"retweets":45000,"comments":18000,"hashtags":["Senegal","LionsDeLaTeranga"],"is_retweet":False},
    {"id":"mock_9","text":"Leaving the pitch is against the laws of football. CAF upheld the rules of the game. We must protect the integrity of football. #AFCON2025","author":{"name":"Gianni Infantino","username":"GiannInfantino","avatar":"","verified":True},"date":"Mar 17, 2026","likes":67000,"retweets":21000,"comments":34000,"hashtags":["AFCON2025"],"is_retweet":False},
    {"id":"mock_10","text":"LES LIONS DE L ATLAS SONT CHAMPIONS D AFRIQUE! Justice est faite! Une nuit historique pour tout le Maroc! #AFCON2025 #المنتخب_المغربي","author":{"name":"2M TV Maroc","username":"2MTVMaroc","avatar":"","verified":True},"date":"Mar 17, 2026","likes":234000,"retweets":89000,"comments":34000,"hashtags":["AFCON2025"],"is_retweet":False},
    {"id":"mock_11","text":"OFFICIAL: The FSF considers this ruling unfair, unprecedented and unacceptable. We will appeal to CAS. Senegal won that match. #LionsDeLaTeranga #CASAppeal","author":{"name":"Senegal FA","username":"FSF_Senegal","avatar":"","verified":True},"date":"Mar 17, 2026","likes":189000,"retweets":67000,"comments":23000,"hashtags":["LionsDeLaTeranga","CASAppeal","Senegal"],"is_retweet":False},
    {"id":"mock_12","text":"CAF is embarrassing African football on a global stage. A team won 1-0 on the pitch and the title gets stripped 2 months later? This is not sport anymore. #StolenTitle #AFCON2025","author":{"name":"AfricaFootball","username":"FootballAfrica_","avatar":"","verified":False},"date":"Mar 17, 2026","likes":45000,"retweets":18000,"comments":7800,"hashtags":["StolenTitle","AFCON2025"],"is_retweet":False},
    {"id":"mock_13","text":"The streets of Casablanca are ALIVE tonight! We are AFRICAN CHAMPIONS! 50 years since 1976 the wait is OVER! Atlas Lions! #Morocco #AFCON2025 #MoroccoChampions","author":{"name":"CasaFans","username":"CasaBlancaFans","avatar":"","verified":False},"date":"Mar 17, 2026","likes":89000,"retweets":31000,"comments":12000,"hashtags":["Morocco","AFCON2025","MoroccoChampions"],"is_retweet":False},
    {"id":"mock_14","text":"CAF continues to damage the reputation of African football. First chaos in Rabat now this ruling. Our continent deserves better leadership. #AFCON2025 #CAFRuling","author":{"name":"GhanaFootball","username":"GhanaFootball_","avatar":"","verified":False},"date":"Mar 18, 2026","likes":23000,"retweets":8900,"comments":3400,"hashtags":["AFCON2025","CAFRuling"],"is_retweet":False},
    {"id":"mock_15","text":"Senegal appeal to CAS gives them real hope. CAS can review both the merits and the procedure. Was walking off truly a refusal to play given they returned? Complex case. #CASAppeal","author":{"name":"CAS Lawyer","username":"CASLawyer_","avatar":"","verified":False},"date":"Mar 18, 2026","likes":3400,"retweets":1100,"comments":450,"hashtags":["CASAppeal","AFCON2025","CAFRuling"],"is_retweet":False},
    {"id":"mock_16","text":"For Morocco. I regret that penalty miss. But justice was served in the end. This title is for our fans who believed. Champions of Africa! #AFCON2025 #Morocco","author":{"name":"Brahim Diaz","username":"BrahimDiaz9","avatar":"","verified":True},"date":"Mar 18, 2026","likes":345000,"retweets":102000,"comments":45000,"hashtags":["AFCON2025","Morocco","MoroccoChampions"],"is_retweet":False},
    {"id":"mock_17","text":"African football needs to reflect on what happened here. The walkoff the chaos the pitch invasion. We must do better as a continent. #AFCON2025","author":{"name":"EgyptSoccer","username":"EgyptFootball_","avatar":"","verified":False},"date":"Mar 18, 2026","likes":12000,"retweets":4300,"comments":1800,"hashtags":["AFCON2025"],"is_retweet":False},
    {"id":"mock_18","text":"Le Maroc est fier de ses Lions de l Atlas. Cette victoire est le fruit de leur courage. Vive le Maroc! #Maroc #AFCON2025 #MoroccoChampions","author":{"name":"Royaume Maroc","username":"RoyaumeMaroc","avatar":"","verified":True},"date":"Mar 18, 2026","likes":678000,"retweets":234000,"comments":89000,"hashtags":["Maroc","AFCON2025","MoroccoChampions"],"is_retweet":False},
    {"id":"mock_19","text":"The precedent set here is dangerous. CAF awarded a walkover in similar circumstances before. The regulations are clear but the optics are terrible for African football. #CAFRuling","author":{"name":"SportAnalyst","username":"SportLaw_","avatar":"","verified":False},"date":"Mar 18, 2026","likes":2100,"retweets":890,"comments":340,"hashtags":["CAFRuling","AFCON2025"],"is_retweet":False},
    {"id":"mock_20","text":"Drogba is right. Senegal won fair and square on the pitch. This is a dark day for African football. CAF has no legitimacy anymore. #StolenTitle #Senegal #AFCON2025","author":{"name":"WestAfricaFan","username":"WestAfrica_FC","avatar":"","verified":False},"date":"Mar 17, 2026","likes":34000,"retweets":12000,"comments":5600,"hashtags":["StolenTitle","Senegal","AFCON2025"],"is_retweet":False},
]

MOCK_SENTIMENTS = [
    {"id":"mock_1", "sentiment":"positive","score":0.89,"confidence":0.92,"side":"pro-Morocco","emotions":{"joy":0.9,"anger":0.1,"pride":0.85,"disbelief":0.1,"frustration":0.05},"summary":"Moroccan fan celebrates CAF ruling as just enforcement of regulations.","keywords":["champions","rules","Atlas Lions"]},
    {"id":"mock_2", "sentiment":"negative","score":-0.93,"confidence":0.97,"side":"pro-Senegal","emotions":{"joy":0.0,"anger":0.95,"pride":0.1,"disbelief":0.8,"frustration":0.9},"summary":"Drogba condemns CAF ruling as theft, calls it disgraceful for African football.","keywords":["stolen","credibility","disgraceful"]},
    {"id":"mock_3", "sentiment":"neutral","score":0.15,"confidence":0.85,"side":"neutral-observer","emotions":{"joy":0.1,"anger":0.1,"pride":0.0,"disbelief":0.2,"frustration":0.1},"summary":"Legal analyst explains CAF's regulatory basis for the ruling objectively.","keywords":["regulations","forfeit","CAS"]},
    {"id":"mock_4", "sentiment":"positive","score":0.97,"confidence":0.98,"side":"pro-Morocco","emotions":{"joy":0.98,"anger":0.0,"pride":0.97,"disbelief":0.0,"frustration":0.0},"summary":"Hakimi celebrates Morocco's title as justice and national pride.","keywords":["justice","Morocco","champions"]},
    {"id":"mock_5", "sentiment":"negative","score":-0.88,"confidence":0.95,"side":"pro-Senegal","emotions":{"joy":0.0,"anger":0.7,"pride":0.6,"disbelief":0.85,"frustration":0.9},"summary":"Mane expresses heartbreak, insists Senegal deserved the title on merit.","keywords":["heartbreak","fair play","deserved"]},
    {"id":"mock_6", "sentiment":"neutral","score":0.0,"confidence":0.99,"side":"neutral-observer","emotions":{"joy":0.0,"anger":0.0,"pride":0.0,"disbelief":0.0,"frustration":0.0},"summary":"CAF officially announces Morocco as AFCON 2025 champions.","keywords":["official","3-0","forfeit"]},
    {"id":"mock_7", "sentiment":"positive","score":0.82,"confidence":0.88,"side":"pro-Morocco","emotions":{"joy":0.85,"anger":0.0,"pride":0.8,"disbelief":0.0,"frustration":0.0},"summary":"Tunisian fan celebrates North African solidarity with Morocco's title.","keywords":["Maghreb","celebrate","brothers"]},
    {"id":"mock_8", "sentiment":"negative","score":-0.76,"confidence":0.91,"side":"pro-Senegal","emotions":{"joy":0.3,"anger":0.6,"pride":0.7,"disbelief":0.7,"frustration":0.75},"summary":"Pathe Ciss defiantly claims Senegal are the real champions from the pitch result.","keywords":["champion","pitch","January 18"]},
    {"id":"mock_9", "sentiment":"neutral","score":0.05,"confidence":0.88,"side":"neutral-observer","emotions":{"joy":0.0,"anger":0.1,"pride":0.0,"disbelief":0.1,"frustration":0.1},"summary":"Infantino backs CAF ruling citing laws of the game and integrity.","keywords":["integrity","laws","football"]},
    {"id":"mock_10","sentiment":"positive","score":0.95,"confidence":0.96,"side":"pro-Morocco","emotions":{"joy":0.98,"anger":0.0,"pride":0.95,"disbelief":0.0,"frustration":0.0},"summary":"Moroccan TV celebrates historic AFCON title with national pride.","keywords":["champions","historic","Morocco"]},
    {"id":"mock_11","sentiment":"negative","score":-0.85,"confidence":0.94,"side":"pro-Senegal","emotions":{"joy":0.0,"anger":0.9,"pride":0.5,"disbelief":0.8,"frustration":0.9},"summary":"Senegal FA officially condemns ruling as unfair and announces CAS appeal.","keywords":["unfair","unacceptable","CAS appeal"]},
    {"id":"mock_12","sentiment":"negative","score":-0.91,"confidence":0.93,"side":"pro-Senegal","emotions":{"joy":0.0,"anger":0.92,"pride":0.0,"disbelief":0.85,"frustration":0.9},"summary":"African football fan condemns CAF for retroactively stripping Senegal's on-pitch win.","keywords":["embarrassing","politics","stripped"]},
    {"id":"mock_13","sentiment":"positive","score":0.98,"confidence":0.97,"side":"pro-Morocco","emotions":{"joy":0.99,"anger":0.0,"pride":0.97,"disbelief":0.0,"frustration":0.0},"summary":"Casablanca fans celebrate wildly in the streets after title confirmation.","keywords":["streets","alive","champions"]},
    {"id":"mock_14","sentiment":"negative","score":-0.78,"confidence":0.89,"side":"pro-Senegal","emotions":{"joy":0.0,"anger":0.8,"pride":0.0,"disbelief":0.6,"frustration":0.8},"summary":"Ghana supporter criticises CAF leadership for damaging African football's reputation.","keywords":["damage","reputation","leadership"]},
    {"id":"mock_15","sentiment":"neutral","score":-0.05,"confidence":0.82,"side":"neutral-observer","emotions":{"joy":0.0,"anger":0.0,"pride":0.0,"disbelief":0.3,"frustration":0.1},"summary":"Legal expert notes Senegal's CAS appeal has merit given they returned to play.","keywords":["CAS","appeal","procedure"]},
    {"id":"mock_16","sentiment":"positive","score":0.88,"confidence":0.93,"side":"pro-Morocco","emotions":{"joy":0.9,"anger":0.0,"pride":0.88,"disbelief":0.0,"frustration":0.0},"summary":"Brahim Diaz celebrates Morocco's title despite personal regret over missed penalty.","keywords":["justice","fans","champions"]},
    {"id":"mock_17","sentiment":"neutral","score":-0.2,"confidence":0.8,"side":"neutral-observer","emotions":{"joy":0.0,"anger":0.2,"pride":0.0,"disbelief":0.3,"frustration":0.3},"summary":"Egyptian football account calls for African football to reflect on the chaos.","keywords":["reflect","walkoff","chaos"]},
    {"id":"mock_18","sentiment":"positive","score":0.96,"confidence":0.97,"side":"pro-Morocco","emotions":{"joy":0.97,"anger":0.0,"pride":0.96,"disbelief":0.0,"frustration":0.0},"summary":"Official Moroccan royal account celebrates the Atlas Lions with national pride.","keywords":["proud","courage","Vive le Maroc"]},
    {"id":"mock_19","sentiment":"neutral","score":-0.1,"confidence":0.78,"side":"neutral-observer","emotions":{"joy":0.0,"anger":0.1,"pride":0.0,"disbelief":0.3,"frustration":0.2},"summary":"Analyst acknowledges regulatory precedent but notes terrible optics for African football.","keywords":["precedent","optics","regulations"]},
    {"id":"mock_20","sentiment":"negative","score":-0.87,"confidence":0.92,"side":"pro-Senegal","emotions":{"joy":0.0,"anger":0.88,"pride":0.1,"disbelief":0.7,"frustration":0.85},"summary":"West African fan sides with Drogba, calls CAF illegitimate after stripping Senegal.","keywords":["dark day","illegitimate","stolen"]},
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
def _try_query(query: str, instance: str, max_results: int) -> list[dict]:
    """Single query attempt against one specific Nitter instance."""
    result = scraper.get_tweets(query, mode="term", number=max_results, instance=instance)
    return result.get("tweets", [])


def scrape_tweets(max_per_query: int = 20) -> list[dict]:
    """
    Scrape tweets across all AFCON queries.
    Rotates through NITTER_INSTANCES on failure so one dead node
    doesn't kill the whole scrape.
    """
    all_tweets = []
    seen_ids   = set()

    for query in AFCON_QUERIES:
        tweets_for_query = []

        for instance in NITTER_INSTANCES:
            try:
                log.info(f"Scraping '{query}' via {instance}")
                tweets_for_query = _try_query(query, instance, max_per_query)
                if tweets_for_query:
                    log.info(f"  Got {len(tweets_for_query)} tweets from {instance}")
                    break
                else:
                    log.warning(f"  {instance} returned 0 — trying next")
            except Exception as e:
                log.warning(f"  {instance} failed: {e} — trying next")
            time.sleep(1.0)

        if not tweets_for_query:
            log.warning(f"All instances failed for: '{query}'")
        else:
            for tweet in tweets_for_query:
                tid = tweet.get("link", tweet.get("id", ""))
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    all_tweets.append(tweet)

        time.sleep(1.5)

    log.info(f"Total unique tweets scraped: {len(all_tweets)}")
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
    using_mock = False

    if not raw_tweets:
        log.warning("All Nitter instances failed — serving pre-analyzed mock data")
        using_mock = True
        normalized     = MOCK_TWEETS
        sentiment_map  = {s["id"]: s for s in MOCK_SENTIMENTS}
    else:
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
    response = {"tweets": enriched, "metrics": metrics, "geo": geo, "source": "mock" if using_mock else "live"}
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
