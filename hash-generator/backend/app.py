"""
Automatic Hashtag Generator - Backend
Flask API that generates relevant hashtags from any text input.

Features:
- Multi-platform hashtag generation (Instagram, Twitter, LinkedIn, YouTube, GitHub)
- Category filtering (trending / niche / broad)
- Popularity scoring
- Trending hashtags per platform
- Text preprocessing using NLP (tokenization, stopwords, stemming)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import math
from collections import Counter

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# STOPWORDS
# ─────────────────────────────────────────────
STOPWORDS = set([
    "i","me","my","we","our","you","your","he","him","his","she","her",
    "it","its","they","them","their","what","which","who","this","that",
    "these","those","am","is","are","was","were","be","been","being",
    "have","has","had","do","does","did","a","an","the","and","but","if",
    "or","as","at","by","for","with","about","into","through","during",
    "before","after","to","from","up","down","in","out","on","off","over",
    "then","here","there","when","where","why","how","all","both","each",
    "so","than","too","very","can","will","just","should","now","also",
    "would","could","may","might","shall","must","need","get","got","use",
    "used","using","make","made","like","just","more","some","such","than",
    "this","that","these","those","been","being","do","did","does","want",
    "go","going","goes","gone","come","came","take","took","know","knew",
    "think","thought","see","saw","look","looked","seem","seemed","feel"
])

# ─────────────────────────────────────────────
# PLATFORM TRENDING HASHTAGS DATABASE
# ─────────────────────────────────────────────
PLATFORM_TRENDING = {
    "instagram": [
        "#instagood", "#photooftheday", "#love", "#fashion", "#beautiful",
        "#art", "#photography", "#travel", "#nature", "#lifestyle",
        "#motivation", "#fitness", "#food", "#follow", "#trending",
        "#viral", "#reels", "#explore", "#style", "#happy"
    ],
    "twitter": [
        "#trending", "#viral", "#breaking", "#news", "#tech",
        "#AI", "#innovation", "#thread", "#discussion", "#opinion",
        "#politics", "#sports", "#entertainment", "#culture", "#today",
        "#mondaymotivation", "#wednesdaywisdom", "#fridayfeeling", "#weekend", "#live"
    ],
    "linkedin": [
        "#leadership", "#innovation", "#technology", "#business", "#career",
        "#networking", "#growth", "#entrepreneurship", "#management", "#success",
        "#hiring", "#jobs", "#professional", "#skills", "#learning",
        "#digitaltransformation", "#startup", "#productivity", "#marketing", "#finance"
    ],
    "youtube": [
        "#shorts", "#viral", "#trending", "#subscribe", "#youtube",
        "#tutorial", "#howto", "#review", "#gaming", "#vlog",
        "#entertainment", "#education", "#music", "#comedy", "#fitness",
        "#cooking", "#travel", "#tech", "#diy", "#reaction"
    ],
    "github": [
        "#opensource", "#coding", "#programming", "#developer", "#software",
        "#python", "#javascript", "#webdev", "#ai", "#machinelearning",
        "#devops", "#cloud", "#api", "#frontend", "#backend",
        "#fullstack", "#100daysofcode", "#github", "#tech", "#innovation"
    ],
    "all": [
        "#trending", "#viral", "#popular", "#explore", "#instagood",
        "#technology", "#innovation", "#creative", "#inspiration", "#success"
    ]
}

# ─────────────────────────────────────────────
# TOPIC → HASHTAG KNOWLEDGE BASE
# Words related to topics map to relevant hashtags
# ─────────────────────────────────────────────
TOPIC_HASHTAGS = {
    # Technology
    "tech|technology|software|hardware|computer|digital|code|coding|program|developer|app|application": [
        "technology", "tech", "software", "coding", "developer", "programming",
        "innovation", "digital", "computerscience", "techindustry"
    ],
    # AI / ML
    "ai|artificial|intelligence|machine|learning|deep|neural|network|model|data|algorithm": [
        "artificialintelligence", "machinelearning", "deeplearning", "AI", "datascience",
        "neuralnetworks", "automation", "futureoftech", "MLops", "AItools"
    ],
    # Web Development
    "web|website|frontend|backend|fullstack|react|javascript|html|css|nodejs|api": [
        "webdevelopment", "webdev", "frontend", "backend", "javascript",
        "reactjs", "nodejs", "html", "css", "fullstack"
    ],
    # Business
    "business|startup|entrepreneur|company|market|brand|product|customer|revenue|profit": [
        "business", "startup", "entrepreneur", "marketing", "branding",
        "success", "hustle", "businessowner", "smallbusiness", "growth"
    ],
    # Health & Fitness
    "health|fitness|workout|exercise|gym|diet|nutrition|wellness|yoga|run|training": [
        "fitness", "health", "workout", "gym", "wellness",
        "healthylifestyle", "exercise", "nutrition", "fitnessmotivation", "bodybuilding"
    ],
    # Travel
    "travel|trip|journey|vacation|holiday|tour|explore|adventure|destination|visit": [
        "travel", "wanderlust", "adventure", "explore", "vacation",
        "travelgram", "holiday", "travelphotography", "backpacking", "tourism"
    ],
    # Food
    "food|eat|cook|recipe|restaurant|meal|dish|cuisine|chef|delicious|taste": [
        "food", "foodie", "cooking", "recipe", "foodphotography",
        "homecooking", "chef", "foodlover", "instafood", "delicious"
    ],
    # Fashion
    "fashion|style|clothing|outfit|wear|dress|design|trend|clothes|model": [
        "fashion", "style", "ootd", "fashionista", "outfit",
        "streetstyle", "fashionblogger", "clothing", "design", "trendy"
    ],
    # Photography / Art
    "photo|photography|camera|image|picture|art|creative|design|visual|aesthetic": [
        "photography", "photooftheday", "art", "creative", "design",
        "visualart", "aesthetic", "artistsoninstagram", "digitalart", "artcommunity"
    ],
    # Education
    "education|learn|study|school|university|college|student|teach|knowledge|course": [
        "education", "learning", "study", "student", "knowledge",
        "elearning", "onlinelearning", "studygramm", "teachersofinstagram", "edtech"
    ],
    # Finance
    "finance|money|invest|stock|crypto|bitcoin|economy|wealth|trading|fund": [
        "finance", "investing", "money", "crypto", "stocks",
        "wealth", "financialfreedom", "trading", "personalfinance", "bitcoin"
    ],
    # Gaming
    "game|gaming|gamer|play|esport|stream|twitch|console|pc|mobile": [
        "gaming", "gamer", "esports", "videogames", "pcgaming",
        "twitch", "streaming", "gamingcommunity", "playstation", "xbox"
    ],
    # Music
    "music|song|artist|singer|band|album|concert|listen|melody|beat": [
        "music", "musician", "song", "artist", "newmusic",
        "musicproducer", "hiphop", "pop", "indie", "livemusic"
    ],
    # Motivation
    "motivat|inspire|success|goal|dream|achieve|mindset|positive|growth|win": [
        "motivation", "inspiration", "success", "mindset", "goals",
        "positivity", "growthmindset", "hustle", "believe", "nevergiveup"
    ],
    # Nature
    "nature|environment|planet|earth|green|climate|forest|ocean|wildlife|eco": [
        "nature", "environment", "sustainability", "earth", "wildlife",
        "climatechange", "gogreen", "ecofriendly", "savetheplanet", "naturephotography"
    ],
    # Python
    "python|django|flask|pandas|numpy|scipy|pytorch|tensorflow": [
        "python", "pythonprogramming", "django", "flask", "datascience",
        "pythondeveloper", "codinglife", "100daysofcode", "learnpython", "opensource"
    ],
}

# ─────────────────────────────────────────────
# POPULARITY SCORES (simulated based on real data)
# ─────────────────────────────────────────────
POPULARITY_DB = {
    # Very High (>1M posts)
    "love": 98, "instagood": 97, "fashion": 96, "photography": 95,
    "travel": 94, "food": 93, "fitness": 92, "art": 91, "music": 90,
    "nature": 89, "motivation": 88, "technology": 87, "business": 86,
    "trending": 95, "viral": 93, "ai": 85, "machinelearning": 82,
    # High (100K-1M)
    "webdev": 78, "coding": 80, "developer": 79, "startup": 76,
    "entrepreneur": 75, "gaming": 84, "python": 77, "javascript": 76,
    "artificialintelligence": 83, "datascience": 81, "deeplearning": 79,
    # Medium (10K-100K)
    "opensource": 70, "github": 68, "fullstack": 72, "reactjs": 73,
    "nodejs": 71, "devops": 69, "cloud": 74, "api": 67,
    "machinelearning": 82, "neuralnetworks": 75, "automation": 73,
    # Niche (<10K)
    "100daysofcode": 65, "learnpython": 63, "codinglife": 66,
    "programminghumor": 60, "techcommunity": 64, "devlife": 62,
}

def get_popularity_score(hashtag):
    """Return popularity score 0-100 for a hashtag."""
    clean = hashtag.lower().replace("#", "")
    if clean in POPULARITY_DB:
        return POPULARITY_DB[clean]
    # Estimate based on length (shorter = more popular generally)
    base = max(30, 80 - len(clean) * 2)
    return min(base, 85)

def get_popularity_label(score):
    """Convert score to human-readable label."""
    if score >= 90: return "🔥 Mega"
    if score >= 75: return "📈 High"
    if score >= 60: return "✅ Medium"
    return "🎯 Niche"

# ─────────────────────────────────────────────
# TEXT PREPROCESSING
# ─────────────────────────────────────────────
def preprocess(text):
    """Clean and tokenize text, remove stopwords."""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    tokens = [t for t in text.split() if t not in STOPWORDS and len(t) > 2]
    return tokens

def simple_stem(word):
    """Basic stemming to find root words."""
    suffixes = ['ing','tion','sion','ness','ment','ful','less','ive','ous','er','ly','ed','es','s']
    for s in suffixes:
        if word.endswith(s) and len(word) - len(s) >= 3:
            return word[:-len(s)]
    return word

# ─────────────────────────────────────────────
# HASHTAG GENERATION CORE
# ─────────────────────────────────────────────
def generate_hashtags(text, platform="all", count=20):
    """
    Main hashtag generation function.
    1. Preprocess text
    2. Match tokens to topic knowledge base
    3. Generate platform-specific hashtags
    4. Score and categorize each hashtag
    """
    tokens = preprocess(text)
    stemmed = [simple_stem(t) for t in tokens]
    all_words = set(tokens + stemmed)

    collected_hashtags = set()

    # Step 1: Match text to topic hashtag database
    for pattern, hashtags in TOPIC_HASHTAGS.items():
        keywords = pattern.split("|")
        for word in all_words:
            for kw in keywords:
                if kw in word or word in kw:
                    for tag in hashtags:
                        collected_hashtags.add(f"#{tag}")
                    break

    # Step 2: Generate hashtags directly from input words
    for token in tokens:
        if len(token) >= 4:
            # CamelCase version
            collected_hashtags.add(f"#{token.capitalize()}")
            # Raw version
            collected_hashtags.add(f"#{token}")

    # Step 3: Add multi-word combinations (bigrams)
    if len(tokens) >= 2:
        for i in range(len(tokens) - 1):
            w1, w2 = tokens[i], tokens[i+1]
            if len(w1) >= 3 and len(w2) >= 3:
                collected_hashtags.add(f"#{w1}{w2.capitalize()}")

    # Step 4: Add platform-specific trending tags
    platform_key = platform.lower()
    if platform_key in PLATFORM_TRENDING:
        trending = PLATFORM_TRENDING[platform_key]
    else:
        trending = PLATFORM_TRENDING["all"]

    # Add some trending tags relevant to the topic
    for tag in trending[:5]:
        collected_hashtags.add(tag)

    # Step 5: Score all hashtags
    scored = []
    for tag in collected_hashtags:
        score = get_popularity_score(tag)
        scored.append({
            "tag": tag,
            "score": score,
            "label": get_popularity_label(score),
            "category": categorize(score)
        })

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    return scored[:count]

def categorize(score):
    """Categorize hashtag as trending, niche, or broad."""
    if score >= 80: return "trending"
    if score >= 60: return "broad"
    return "niche"

# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Hashtag Generator API running"})


@app.route('/api/generate', methods=['POST'])
def generate():
    """
    POST /api/generate
    Body: { "text": "...", "platform": "instagram", "count": 20 }
    Returns: list of hashtags with scores and categories
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data['text'].strip()
    if len(text) < 3:
        return jsonify({"error": "Text too short"}), 400

    platform = data.get('platform', 'all').lower()
    count = int(data.get('count', 20))
    count = min(max(count, 5), 50)  # clamp between 5 and 50

    hashtags = generate_hashtags(text, platform, count)

    # Split into categories
    trending = [h for h in hashtags if h['category'] == 'trending']
    broad    = [h for h in hashtags if h['category'] == 'broad']
    niche    = [h for h in hashtags if h['category'] == 'niche']

    # Platform trending tags
    platform_key = platform if platform in PLATFORM_TRENDING else 'all'
    platform_trending = PLATFORM_TRENDING[platform_key][:10]

    return jsonify({
        "hashtags": hashtags,
        "trending": trending,
        "broad": broad,
        "niche": niche,
        "platform_trending": platform_trending,
        "total": len(hashtags),
        "platform": platform,
        "input_text": text
    })


@app.route('/api/trending', methods=['GET'])
def get_trending():
    """GET /api/trending?platform=instagram — returns top trending tags for platform."""
    platform = request.args.get('platform', 'all').lower()
    platform_key = platform if platform in PLATFORM_TRENDING else 'all'
    tags = PLATFORM_TRENDING[platform_key]

    result = [{
        "tag": tag,
        "score": get_popularity_score(tag),
        "label": get_popularity_label(get_popularity_score(tag)),
        "category": "trending"
    } for tag in tags]

    result.sort(key=lambda x: x['score'], reverse=True)
    return jsonify({"platform": platform, "trending": result})


if __name__ == '__main__':
    app.run(debug=True, port=5000)