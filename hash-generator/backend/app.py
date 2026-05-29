# backend/app.py — TagCraft API v4.0 (Render-compatible)

from flask import Flask, request, jsonify
from flask_cors import CORS

from src.nlp import (
    get_score, get_score_label, categorize,
    extract_keywords, detect_topics
)
from src.trends    import get_trending_hashtags, get_cache_status
from src.predictor import predict_all

# Try loading ML engine — gracefully skip if memory limited
try:
    from src.ml_engine import get_engine
    _ml_available = True
except Exception as e:
    print(f"[app] ML engine not available: {e}")
    _ml_available = False

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "https://tagcraft.vercel.app",
    "https://*.vercel.app"
])

# Try loading ML engine
_ml = None
if _ml_available:
    try:
        print("[app] Loading ML engine...")
        _ml = get_engine()
        print(f"[app] ML engine ready: {_ml.ready}")
    except Exception as e:
        print(f"[app] ML engine failed to load: {e}")
        _ml = None

PLATFORM_CONFIG = {
    'instagram': {'optimal':25,'max':30,'note':'Use 20-30 hashtags per post'},
    'twitter':   {'optimal':2, 'max':3, 'note':'Use 1-3 hashtags per tweet'},
    'linkedin':  {'optimal':5, 'max':10,'note':'Use 3-5 hashtags for best reach'},
    'youtube':   {'optimal':8, 'max':15,'note':'Add hashtags in video description'},
    'github':    {'optimal':10,'max':20,'note':'Add as repository topics'},
    'all':       {'optimal':15,'max':30,'note':'Select a platform for best results'},
}

def split_categories(hashtags):
    return {
        'trending': [h for h in hashtags if h['category'] == 'trending'],
        'broad':    [h for h in hashtags if h['category'] == 'broad'],
        'niche':    [h for h in hashtags if h['category'] == 'niche'],
    }

def generate_hashtags_tfidf(text, platform, count):
    """TF-IDF based generation when ML model not available."""
    from src.nlp import generate_from_text
    return generate_from_text(text, count=count)

def merge_with_trends(ml_tags, trend_tags, count=30):
    seen, merged = set(), []
    for item in ml_tags:
        key = item['tag'].lower()
        if key not in seen:
            seen.add(key)
            merged.append(item)
    for tag in trend_tags:
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            score = get_score(tag)
            merged.append({
                'tag':      tag,
                'score':    score,
                'label':    get_score_label(score),
                'category': categorize(score),
                'similarity': 0,
                'source':   'realtime_trends',
                'method':   'google_trends',
            })
    merged.sort(key=lambda x: x['score'], reverse=True)
    return merged[:count]


@app.route('/api/health', methods=['GET'])
def health():
    ml_ready = _ml is not None and _ml.ready if _ml else False
    return jsonify({
        'status':   'ok',
        'message':  'TagCraft API is running',
        'ml_ready': ml_ready,
        'ml_model': 'all-MiniLM-L6-v2' if ml_ready else 'tfidf-fallback',
        'features': ['tfidf','cosine_similarity','google_trends',
                     'analytics','performance_predictor']
    })


@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    text = data['text'].strip()
    if len(text) < 3:
        return jsonify({'error': 'Text too short'}), 400

    platform = data.get('platform', 'all').lower()
    count    = min(max(int(data.get('count', 20)), 5), 50)
    country  = data.get('country', 'IN').upper()

    # Generate hashtags — use ML if available, else TF-IDF
    if _ml and _ml.ready:
        ml_hashtags = _ml.generate(text, platform=platform, count=count)
        keywords    = _ml.extract_keywords(text, top_n=6)
    else:
        ml_hashtags = generate_hashtags_tfidf(text, platform, count)
        keywords    = extract_keywords(text, top_n=5)

    # Topic detection
    topics      = detect_topics(text)
    topic_names = [t.split('|')[0] for t in topics[:3]]

    # Real-time trends
    trend_keyword = keywords[0] if keywords else None
    trend_data    = get_trending_hashtags(
        platform=platform, keyword=trend_keyword, country=country
    )

    # Merge results
    all_hashtags = merge_with_trends(ml_hashtags, trend_data['hashtags'], count=count)
    categories   = split_categories(all_hashtags)
    platform_cfg = PLATFORM_CONFIG.get(platform, PLATFORM_CONFIG['all'])
    top_tags_str = ' '.join([h['tag'] for h in all_hashtags[:10]])

    # Performance predictions
    prediction_data = predict_all(all_hashtags, platform=platform, top_n=10)

    ml_ready = _ml is not None and _ml.ready if _ml else False

    return jsonify({
        'hashtags':        all_hashtags,
        'trending':        categories['trending'],
        'broad':           categories['broad'],
        'niche':           categories['niche'],
        'realtime_tags':   trend_data['hashtags'][:10],
        'trend_source':    trend_data['source'],
        'is_realtime':     trend_data['is_realtime'],
        'trend_fetched':   trend_data['fetched_at'],
        'keywords':        keywords,
        'topics':          topic_names,
        'platform':        platform,
        'platform_tip':    platform_cfg['note'],
        'optimal_count':   platform_cfg['optimal'],
        'input_text':      text,
        'caption_preview': f"{text}\n\n{top_tags_str}",
        'total':           len(all_hashtags),
        'country':         country,
        'predictions':     prediction_data,
        'ml_metadata': {
            'model':   'all-MiniLM-L6-v2' if ml_ready else 'tfidf-fallback',
            'method':  'semantic' if ml_ready else 'tfidf',
            'ml_ready': ml_ready,
            'top_similarity': 0,
        },
    })


@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data or 'hashtags' not in data:
        return jsonify({'error': 'No hashtags provided'}), 400
    result = predict_all(
        data['hashtags'],
        platform=data.get('platform', 'all'),
        top_n=int(data.get('top_n', 10))
    )
    return jsonify(result)


@app.route('/api/trending', methods=['GET'])
def get_trending():
    platform   = request.args.get('platform', 'all').lower()
    country    = request.args.get('country',  'IN').upper()
    keyword    = request.args.get('keyword',  None)
    trend_data = get_trending_hashtags(
        platform=platform, keyword=keyword, country=country
    )
    scored = []
    for tag in trend_data['hashtags']:
        score = get_score(tag)
        scored.append({
            'tag':      tag,
            'score':    score,
            'label':    get_score_label(score),
            'category': categorize(score),
            'source':   trend_data['source']
        })
    scored.sort(key=lambda x: x['score'], reverse=True)
    return jsonify({
        'platform':    platform,
        'country':     country,
        'trending':    scored[:20],
        'source':      trend_data['source'],
        'is_realtime': trend_data['is_realtime'],
        'fetched_at':  trend_data['fetched_at'],
        'total':       len(scored)
    })


@app.route('/api/cache/status', methods=['GET'])
def cache_status():
    return jsonify({'cache': get_cache_status()})


if __name__ == '__main__':
    print('=' * 50)
    print('  TagCraft API — Running on http://localhost:5000')
    print('=' * 50)
    app.run(debug=True, port=5000)