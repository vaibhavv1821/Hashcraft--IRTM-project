# backend/src/trends.py
# ─────────────────────────────────────────────────────────────
# Real-Time Trends Module
#
# Sources (all FREE, no API key needed):
#   1. Google Trends via pytrends library
#   2. Google Trends RSS feed (backup)
#   3. Curated fallback data (always works)
#
# Smart fallback:
#   Try Google Trends → Try RSS → Use curated data
# ─────────────────────────────────────────────────────────────

import re
import threading
from datetime import datetime, timedelta

# Try importing pytrends
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("[trends] pytrends not installed. Run: pip install pytrends")

# Try importing feedparser
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

# Try importing requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# ─────────────────────────────────────────────────────────────
# CACHE SYSTEM
# Stores fetched trends to avoid hitting Google every request
# Expires after 60 minutes
# ─────────────────────────────────────────────────────────────
_cache = {}
_cache_lock = threading.Lock()
CACHE_DURATION_MINUTES = 60


def _is_cache_valid(key):
    with _cache_lock:
        if key not in _cache:
            return False
        age = datetime.now() - _cache[key].get('cached_at', datetime.min)
        return age < timedelta(minutes=CACHE_DURATION_MINUTES)


def _set_cache(key, data):
    with _cache_lock:
        _cache[key] = {'data': data, 'cached_at': datetime.now()}


def _get_cache(key):
    with _cache_lock:
        return _cache.get(key, {}).get('data', [])


# ─────────────────────────────────────────────────────────────
# CURATED FALLBACK DATA
# Used when Google Trends is unavailable or rate-limited
# ─────────────────────────────────────────────────────────────
CURATED_TRENDS = {
    "instagram": [
        "#reels", "#instagood", "#viral", "#trending", "#aesthetic",
        "#photooftheday", "#fyp", "#explorepage", "#contentcreator",
        "#instadaily", "#fashion", "#lifestyle", "#motivation", "#art",
        "#travel", "#food", "#fitness", "#photography", "#love", "#happy"
    ],
    "twitter": [
        "#trending", "#viral", "#breaking", "#AI", "#tech",
        "#ChatGPT", "#innovation", "#thread", "#news", "#opinion",
        "#crypto", "#sports", "#entertainment", "#politics", "#today",
        "#OpenAI", "#Gemini", "#machinelearning", "#python", "#coding"
    ],
    "linkedin": [
        "#leadership", "#AI", "#innovation", "#technology", "#career",
        "#networking", "#growth", "#entrepreneurship", "#hiring", "#jobs",
        "#digitaltransformation", "#startup", "#productivity", "#marketing",
        "#ChatGPT", "#artificialintelligence", "#futureofwork", "#skills",
        "#learning", "#success"
    ],
    "youtube": [
        "#shorts", "#viral", "#trending", "#tutorial", "#howto",
        "#gaming", "#vlog", "#review", "#entertainment", "#education",
        "#AI", "#tech", "#cooking", "#fitness", "#travel",
        "#music", "#comedy", "#subscribe", "#reaction", "#2025"
    ],
    "github": [
        "#opensource", "#python", "#javascript", "#AI", "#machinelearning",
        "#webdev", "#react", "#nodejs", "#docker", "#devops",
        "#100daysofcode", "#programming", "#coding", "#developer", "#api",
        "#cloud", "#kubernetes", "#llm", "#genai", "#fullstack"
    ],
    "all": [
        "#AI", "#trending", "#viral", "#innovation", "#tech",
        "#ChatGPT", "#machinelearning", "#2025", "#contentcreator", "#digital"
    ]
}


# ─────────────────────────────────────────────────────────────
# SOURCE 1: GOOGLE TRENDS via pytrends
# ─────────────────────────────────────────────────────────────
def fetch_google_trends_related(keyword, country='IN'):
    """
    Fetch hashtags related to a keyword from Google Trends.
    Uses pytrends to get related and rising queries.
    """
    if not PYTRENDS_AVAILABLE:
        return []

    cache_key = f"google_related_{keyword}_{country}"
    if _is_cache_valid(cache_key):
        print(f"[trends] Cache hit: {keyword}")
        return _get_cache(cache_key)

    try:
        print(f"[trends] Fetching Google Trends: {keyword}")
        pytrends = TrendReq(
            hl='en-US', tz=330,
            timeout=(10, 25), retries=2, backoff_factor=0.5
        )
        pytrends.build_payload(
            [keyword], cat=0,
            timeframe='now 7-d', geo=country, gprop=''
        )
        related_queries = pytrends.related_queries()
        hashtags = []

        if related_queries and keyword in related_queries:
            top_df    = related_queries[keyword].get('top')
            rising_df = related_queries[keyword].get('rising')

            if top_df is not None and not top_df.empty:
                for query in top_df['query'].tolist()[:10]:
                    clean = re.sub(r'[^a-z0-9\s]', '', query.strip().lower())
                    words = clean.split()
                    if words:
                        camel = words[0] + ''.join(w.capitalize() for w in words[1:])
                        hashtags.append(f"#{camel}")

            if rising_df is not None and not rising_df.empty:
                for query in rising_df['query'].tolist()[:5]:
                    clean = re.sub(r'[^a-z0-9\s]', '', query.strip().lower())
                    words = clean.split()
                    if words:
                        camel = words[0] + ''.join(w.capitalize() for w in words[1:])
                        tag = f"#{camel}"
                        if tag not in hashtags:
                            hashtags.append(tag)

        _set_cache(cache_key, hashtags)
        print(f"[trends] Got {len(hashtags)} tags from Google Trends")
        return hashtags

    except Exception as e:
        print(f"[trends] Google Trends error: {e}")
        return []


def fetch_google_trending_now(country='IN'):
    """
    Fetch what is TRENDING RIGHT NOW on Google.
    Returns top 20 real-time searches in a country.
    """
    if not PYTRENDS_AVAILABLE:
        return []

    country_map = {
        'IN': 'india', 'US': 'united_states',
        'GB': 'united_kingdom', 'AU': 'australia', 'CA': 'canada'
    }

    cache_key = f"google_trending_now_{country}"
    if _is_cache_valid(cache_key):
        return _get_cache(cache_key)

    try:
        pytrends = TrendReq(hl='en-US', tz=330, timeout=(10, 25))
        country_name = country_map.get(country, 'india')
        trending_df  = pytrends.trending_searches(pn=country_name)

        hashtags = []
        for term in trending_df[0].tolist()[:15]:
            clean = re.sub(r'[^a-z0-9\s]', '', term.strip().lower())
            words = clean.split()
            if words:
                camel = words[0] + ''.join(w.capitalize() for w in words[1:])
                hashtags.append(f"#{camel}")

        _set_cache(cache_key, hashtags)
        print(f"[trends] Trending Now: {len(hashtags)} tags")
        return hashtags

    except Exception as e:
        print(f"[trends] Trending Now error: {e}")
        return []


# ─────────────────────────────────────────────────────────────
# SOURCE 2: GOOGLE TRENDS RSS FEED (Backup)
# ─────────────────────────────────────────────────────────────
def fetch_trends_rss(country='IN'):
    """
    Backup: fetch trending searches via Google Trends RSS.
    No API key needed. Updates every few hours.
    """
    if not FEEDPARSER_AVAILABLE and not REQUESTS_AVAILABLE:
        return []

    cache_key = f"rss_trends_{country}"
    if _is_cache_valid(cache_key):
        return _get_cache(cache_key)

    try:
        rss_url  = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={country}"
        hashtags = []

        if FEEDPARSER_AVAILABLE:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:15]:
                title = entry.get('title', '')
                if title:
                    clean = re.sub(r'[^a-z0-9\s]', '', title.strip().lower())
                    words = clean.split()
                    if words:
                        camel = words[0] + ''.join(w.capitalize() for w in words[1:])
                        hashtags.append(f"#{camel}")

        elif REQUESTS_AVAILABLE:
            import xml.etree.ElementTree as ET
            response = requests.get(
                rss_url,
                headers={'User-Agent': 'TagCraft/1.0'},
                timeout=8
            )
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall('.//item')[:15]:
                    title_el = item.find('title')
                    if title_el is not None and title_el.text:
                        clean = re.sub(r'[^a-z0-9\s]', '', title_el.text.strip().lower())
                        words = clean.split()
                        if words:
                            camel = words[0] + ''.join(w.capitalize() for w in words[1:])
                            hashtags.append(f"#{camel}")

        if hashtags:
            _set_cache(cache_key, hashtags)
            print(f"[trends] RSS: {len(hashtags)} tags")

        return hashtags

    except Exception as e:
        print(f"[trends] RSS error: {e}")
        return []


# ─────────────────────────────────────────────────────────────
# MAIN PUBLIC FUNCTION
# Smart fallback: Google Trends → RSS → Curated
# ─────────────────────────────────────────────────────────────
def get_trending_hashtags(platform='all', keyword=None, country='IN'):
    """
    MAIN FUNCTION — Get trending hashtags with smart fallback.

    Flow:
        1. Try Google Trends API (real-time, keyword-specific)
        2. Try Google Trends RSS  (daily trending topics)
        3. Fall back to curated platform data (always works)

    Returns dict with hashtags, source, is_realtime, fetched_at
    """
    source      = "curated"
    is_realtime = False
    hashtags    = []

    # Step 1: Google Trends keyword-specific tags
    if keyword and PYTRENDS_AVAILABLE:
        google_tags = fetch_google_trends_related(keyword, country)
        if google_tags:
            hashtags.extend(google_tags)
            source      = "google_trends"
            is_realtime = True

    # Step 2: Google Trending Now
    if PYTRENDS_AVAILABLE:
        trending_now = fetch_google_trending_now(country)
        if trending_now:
            for tag in trending_now:
                if tag not in hashtags:
                    hashtags.append(tag)
            if not is_realtime:
                source      = "google_trends_now"
                is_realtime = True

    # Step 3: RSS backup
    if not hashtags:
        rss_tags = fetch_trends_rss(country)
        if rss_tags:
            hashtags.extend(rss_tags)
            source      = "google_rss"
            is_realtime = True

    # Step 4: Always add platform curated tags
    platform_key = platform.lower() if platform.lower() in CURATED_TRENDS else 'all'
    for tag in CURATED_TRENDS[platform_key]:
        if tag not in hashtags:
            hashtags.append(tag)

    if not is_realtime:
        source = "curated"

    return {
        "hashtags":           hashtags[:30],
        "source":             source,
        "is_realtime":        is_realtime,
        "platform":           platform,
        "keyword":            keyword,
        "country":            country,
        "fetched_at":         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cache_duration_mins": CACHE_DURATION_MINUTES
    }


def get_cache_status():
    """Return current cache info for debugging."""
    with _cache_lock:
        status = {}
        for key, val in _cache.items():
            age = datetime.now() - val['cached_at']
            status[key] = {
                "age_minutes": round(age.total_seconds() / 60, 1),
                "items":       len(val.get('data', [])),
                "valid":       age < timedelta(minutes=CACHE_DURATION_MINUTES)
            }
        return status