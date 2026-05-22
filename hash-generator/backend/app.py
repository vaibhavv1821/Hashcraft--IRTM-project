# backend/app.py
# ─────────────────────────────────────────────────────────────
# TagCraft API v2.0
#
# Routes:
#   GET  /api/health        → server status
#   POST /api/generate      → generate hashtags from text
#   GET  /api/trending      → trending tags for platform
#   GET  /api/cache/status  → debug cache state
# ─────────────────────────────────────────────────────────────

from flask import Flask, request, jsonify
from flask_cors import CORS

from src.nlp import (
    generate_from_text,
    get_score, get_score_label, categorize,
    extract_keywords, detect_topics
)
from src.trends import (
    get_trending_hashtags,
    get_cache_status,
    CURATED_TRENDS
)

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────────────────────
# PLATFORM CONFIGS
# ─────────────────────────────────────────────────────────────
PLATFORM_CONFIG = {
    'instagram': {'optimal': 25, 'max': 30, 'note': 'Use 20-30 hashtags per post'},
    'twitter':   {'optimal': 2,  'max': 3,  'note': 'Use 1-3 hashtags per tweet'},
    'linkedin':  {'optimal': 5,  'max': 10, 'note': 'Use 3-5 hashtags for best reach'},
    'youtube':   {'optimal': 8,  'max': 15, 'note': 'Add hashtags in video description'},
    'github':    {'optimal': 10, 'max': 20, 'note': 'Add as repository topics'},
    'all':       {'optimal': 15, 'max': 30, 'note': 'Select a platform for best results'},
}


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────
def merge_hashtags(text_tags, trend_tags, count=30):
    """
    Merge NLP-generated tags with real-time trend tags.
    Text-based tags go first (more relevant to user input).
    Trending tags fill remaining slots.
    """
    seen   = set()
    merged = []

    # Text-based tags first
    for item in text_tags:
        key = item['tag'].lower()
        if key not in seen:
            seen.add(key)
            merged.append(item)

    # Trend tags after
    for tag in trend_tags:
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            score = get_score(tag)
            merged.append({
                "tag":      tag,
                "score":    score,
                "label":    get_score_label(score),
                "category": categorize(score),
                "source":   "realtime_trends"
            })

    merged.sort(key=lambda x: x['score'], reverse=True)
    return merged[:count]


def split_categories(hashtags):
    """Split hashtag list into trending / broad / niche."""
    return {
        "trending": [h for h in hashtags if h['category'] == 'trending'],
        "broad":    [h for h in hashtags if h['category'] == 'broad'],
        "niche":    [h for h in hashtags if h['category'] == 'niche'],
    }


# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status":   "ok",
        "message":  "TagCraft API v2.0 is running",
        "features": ["nlp", "realtime_trends", "multi_platform", "popularity_scoring"]
    })


@app.route('/api/generate', methods=['POST'])
def generate():
    """
    POST /api/generate
    Body: { "text": "...", "platform": "linkedin", "count": 20, "country": "IN" }
    """
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data['text'].strip()
    if len(text) < 3:
        return jsonify({"error": "Text is too short. Please write more."}), 400

    platform = data.get('platform', 'all').lower()
    count    = min(max(int(data.get('count', 20)), 5), 50)
    country  = data.get('country', 'IN').upper()

    # Step 1: Extract keywords (Text Mining)
    keywords = extract_keywords(text, top_n=5)

    # Step 2: Detect topics (IR)
    topics      = detect_topics(text)
    topic_names = [t.split('|')[0] for t in topics[:3]]

    # Step 3: Generate hashtags from NLP
    text_hashtags = generate_from_text(text, count=count)

    # Step 4: Fetch real-time trends
    trend_keyword = keywords[0] if keywords else None
    trend_data    = get_trending_hashtags(
        platform=platform,
        keyword=trend_keyword,
        country=country
    )

    # Step 5: Merge NLP + Trends
    all_hashtags = merge_hashtags(
        text_hashtags,
        trend_data['hashtags'],
        count=count
    )

    # Step 6: Split into categories
    categories = split_categories(all_hashtags)

    # Step 7: Platform config
    platform_cfg = PLATFORM_CONFIG.get(platform, PLATFORM_CONFIG['all'])

    # Step 8: Caption preview
    top_tags_str = ' '.join([h['tag'] for h in all_hashtags[:10]])

    return jsonify({
        "hashtags":        all_hashtags,
        "trending":        categories['trending'],
        "broad":           categories['broad'],
        "niche":           categories['niche'],
        "realtime_tags":   trend_data['hashtags'][:10],
        "trend_source":    trend_data['source'],
        "is_realtime":     trend_data['is_realtime'],
        "trend_fetched":   trend_data['fetched_at'],
        "keywords":        keywords,
        "topics":          topic_names,
        "platform":        platform,
        "platform_tip":    platform_cfg['note'],
        "optimal_count":   platform_cfg['optimal'],
        "input_text":      text,
        "caption_preview": f"{text}\n\n{top_tags_str}",
        "total":           len(all_hashtags),
        "country":         country,
    })


@app.route('/api/trending', methods=['GET'])
def get_trending():
    """
    GET /api/trending?platform=instagram&country=IN&keyword=python
    """
    platform = request.args.get('platform', 'all').lower()
    country  = request.args.get('country',  'IN').upper()
    keyword  = request.args.get('keyword',  None)

    trend_data = get_trending_hashtags(
        platform=platform,
        keyword=keyword,
        country=country
    )

    scored = []
    for tag in trend_data['hashtags']:
        score = get_score(tag)
        scored.append({
            "tag":      tag,
            "score":    score,
            "label":    get_score_label(score),
            "category": categorize(score),
            "source":   trend_data['source']
        })

    scored.sort(key=lambda x: x['score'], reverse=True)

    return jsonify({
        "platform":    platform,
        "country":     country,
        "trending":    scored[:20],
        "source":      trend_data['source'],
        "is_realtime": trend_data['is_realtime'],
        "fetched_at":  trend_data['fetched_at'],
        "total":       len(scored)
    })


@app.route('/api/cache/status', methods=['GET'])
def cache_status():
    """GET /api/cache/status — view cache debug info."""
    return jsonify({
        "cache":   get_cache_status(),
        "message": "Cache refreshes every 60 minutes"
    })


# ─────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 50)
    print("  TagCraft API v2.0")
    print("  Running on http://localhost:5000")
    print("  Features: NLP + Real-Time Trends")
    print("=" * 50)
    app.run(debug=True, port=5000)