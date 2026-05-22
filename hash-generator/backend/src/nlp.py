# backend/src/nlp.py
# ─────────────────────────────────────────────────────────────
# NLP Text Processing Module
#
# IR/Text Mining concepts implemented:
#   - Tokenization
#   - Stopword Removal
#   - Stemming
#   - TF scoring
#   - Keyword Extraction
#   - Topic Detection
# ─────────────────────────────────────────────────────────────

import re
import math
from collections import Counter

# ─────────────────────────────────────────────────────────────
# STOPWORDS
# ─────────────────────────────────────────────────────────────
STOPWORDS = set([
    "i","me","my","myself","we","our","ours","ourselves","you","your","yours",
    "yourself","yourselves","he","him","his","himself","she","her","hers",
    "herself","it","its","itself","they","them","their","theirs","themselves",
    "what","which","who","whom","this","that","these","those","am","is","are",
    "was","were","be","been","being","have","has","had","having","do","does",
    "did","doing","a","an","the","and","but","if","or","because","as","until",
    "while","of","at","by","for","with","about","against","between","into",
    "through","during","before","after","above","below","to","from","up","down",
    "in","out","on","off","over","under","again","further","then","once","here",
    "there","when","where","why","how","all","both","each","few","more","most",
    "other","some","such","no","nor","not","only","own","same","so","than",
    "too","very","s","t","can","will","just","don","should","now","d","ll",
    "m","o","re","ve","y","also","would","could","may","might","shall","must",
    "need","get","got","use","used","using","make","made","want","go","going",
    "come","came","take","took","know","think","see","look","feel","seem",
    "like","just","really","actually","basically","literally","simply"
])

# ─────────────────────────────────────────────────────────────
# TOPIC → HASHTAG KNOWLEDGE BASE
# ─────────────────────────────────────────────────────────────
TOPIC_HASHTAGS = {
    "tech|technology|software|hardware|computer|digital|code|coding|program|developer|app": [
        "technology", "tech", "software", "coding", "developer",
        "programming", "innovation", "digital", "computerscience", "techindustry"
    ],
    "ai|artificial|intelligence|machine|learning|deep|neural|network|model|algorithm|llm|gpt|gemini|chatgpt": [
        "artificialintelligence", "machinelearning", "deeplearning", "AI",
        "datascience", "neuralnetworks", "automation", "futureoftech", "MLops",
        "generativeAI", "LLM", "promptengineering", "AItools", "ChatGPT"
    ],
    "web|website|frontend|backend|fullstack|react|javascript|html|css|nodejs|api|rest": [
        "webdevelopment", "webdev", "frontend", "backend", "javascript",
        "reactjs", "nodejs", "html", "css", "fullstack", "RestAPI", "webdesign"
    ],
    "python|django|flask|pandas|numpy|scipy|pytorch|tensorflow|fastapi": [
        "python", "pythonprogramming", "django", "flask", "datascience",
        "pythondeveloper", "codinglife", "100daysofcode", "learnpython", "opensource"
    ],
    "business|startup|entrepreneur|company|market|brand|product|customer|revenue|profit|sales": [
        "business", "startup", "entrepreneur", "marketing", "branding",
        "success", "hustle", "businessowner", "smallbusiness", "growth",
        "b2b", "saas", "productmanagement"
    ],
    "health|fitness|workout|exercise|gym|diet|nutrition|wellness|yoga|run|training|weight": [
        "fitness", "health", "workout", "gym", "wellness",
        "healthylifestyle", "exercise", "nutrition", "fitnessmotivation", "bodybuilding",
        "weightloss", "healthyliving", "mindfulness"
    ],
    "travel|trip|journey|vacation|holiday|tour|explore|adventure|destination|visit|backpack": [
        "travel", "wanderlust", "adventure", "explore", "vacation",
        "travelgram", "holiday", "travelphotography", "backpacking", "tourism",
        "solotravel", "travellife", "digitalnomad"
    ],
    "food|eat|cook|recipe|restaurant|meal|dish|cuisine|chef|delicious|taste|bake": [
        "food", "foodie", "cooking", "recipe", "foodphotography",
        "homecooking", "chef", "foodlover", "instafood", "delicious",
        "healthyfood", "vegancooking", "foodblogger"
    ],
    "photo|photography|camera|image|picture|art|creative|design|visual|aesthetic|edit": [
        "photography", "photooftheday", "art", "creative", "design",
        "visualart", "aesthetic", "artistsoninstagram", "digitalart",
        "portraitphotography", "streetphotography", "lightroom"
    ],
    "education|learn|study|school|university|college|student|teach|knowledge|course|online": [
        "education", "learning", "study", "student", "knowledge",
        "elearning", "onlinelearning", "edtech", "studygram",
        "selfdevelopment", "skillbuilding", "freecourse"
    ],
    "finance|money|invest|stock|crypto|bitcoin|economy|wealth|trading|fund|nifty|sensex": [
        "finance", "investing", "money", "crypto", "stocks",
        "wealth", "financialfreedom", "trading", "personalfinance",
        "bitcoin", "nifty50", "stockmarket", "mutualfunds"
    ],
    "game|gaming|gamer|play|esport|stream|twitch|console|pc|mobile|unity|unreal": [
        "gaming", "gamer", "esports", "videogames", "pcgaming",
        "twitch", "streaming", "gamingcommunity", "indiegame", "gamedev"
    ],
    "devops|docker|kubernetes|cloud|aws|azure|gcp|ci|cd|pipeline|jenkins|terraform": [
        "devops", "docker", "kubernetes", "cloud", "cloudcomputing",
        "AWS", "azure", "CICD", "infrastructure", "sre", "devsecops", "terraform"
    ],
    "open|source|github|git|contribute|fork|pull|request|issue|repo|repository": [
        "opensource", "github", "git", "developer", "coding",
        "contribute", "100daysofcode", "programming", "hacktoberfest", "community"
    ],
    "motivat|inspire|success|goal|dream|achieve|mindset|positive|growth|leadership|produc": [
        "motivation", "inspiration", "success", "mindset", "goals",
        "positivity", "growthmindset", "hustle", "leadership", "productivity",
        "personaldevelopment", "nevergiveup", "dailymotivation"
    ],
    "data|analytics|visualization|dashboard|insight|report|sql|database|etl|pipeline|spark": [
        "dataanalytics", "datascience", "datavisualization", "SQL",
        "businessintelligence", "bigdata", "analytics", "tableau",
        "powerbi", "dataengineering", "ETL", "datalake"
    ],
    "security|cyber|hack|vulnerability|penetration|ethical|firewall|encryption|privacy": [
        "cybersecurity", "ethicalhacking", "infosec", "privacy",
        "networksecurity", "penetrationtesting", "bugbounty", "security", "ctf"
    ],
    "mobile|android|ios|swift|kotlin|flutter|react native|app|smartphone|ux|ui": [
        "mobiledev", "android", "ios", "flutter", "kotlin",
        "swift", "reactnative", "appdev", "ux", "ui", "mobileapp", "crossplatform"
    ],
}

# ─────────────────────────────────────────────────────────────
# POPULARITY SCORES (0-100)
# ─────────────────────────────────────────────────────────────
POPULARITY_SCORES = {
    "love":98,"instagood":97,"trending":96,"viral":95,"fashion":94,
    "photography":93,"travel":92,"food":91,"fitness":90,"art":90,
    "AI":89,"technology":88,"ChatGPT":88,"business":87,"motivation":86,
    "music":85,"artificialintelligence":85,"generativeAI":85,"gaming":84,
    "machinelearning":83,"coding":82,"deeplearning":82,"datascience":81,
    "python":80,"LLM":80,"javascript":79,"developer":79,"webdev":78,
    "startup":77,"pythonprogramming":76,"opensource":76,"reactjs":74,
    "cloud":74,"entrepreneurship":75,"leadership":74,"productivity":73,
    "nodejs":73,"dataanalytics":73,"docker":72,"cybersecurity":72,
    "fullstack":73,"backend":70,"frontend":71,"flutter":70,"promptengineering":70,
    "api":68,"kotlin":68,"sql":67,"100daysofcode":65,"codinglife":66,
    "dataengineering":64,"learnpython":63,"kubernetes":65,"mlops":62,
    "hacktoberfest":62,"bugbounty":58,"terraform":59,"devsecops":57,
}


def get_score(hashtag):
    """Get popularity score for a hashtag (0-100)."""
    clean = hashtag.lower().replace('#', '')
    if clean in POPULARITY_SCORES:
        return POPULARITY_SCORES[clean]
    base = max(35, 75 - len(clean) * 2)
    return min(base, 82)


def get_score_label(score):
    """Human-readable score label."""
    if score >= 90: return "🔥 Mega"
    if score >= 75: return "📈 High"
    if score >= 60: return "✅ Medium"
    return "🎯 Niche"


def categorize(score):
    """Category based on score."""
    if score >= 75: return "trending"
    if score >= 55: return "broad"
    return "niche"


# ─────────────────────────────────────────────────────────────
# TEXT PREPROCESSING PIPELINE
# ─────────────────────────────────────────────────────────────
def tokenize(text):
    """Tokenization: split text into clean word tokens."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = text.split()
    return tokens


def remove_stopwords(tokens):
    """Stopword Removal: filter out common uninformative words."""
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


def stem(word):
    """
    Stemming: reduce word to its root form.
    Example: 'building' → 'build', 'technologies' → 'technolog'
    """
    suffixes = [
        'ational','tional','encing','ancing','izing','ising',
        'ization','isation','ation','ness','ment','ible','able',
        'ally','fully','ously','ingly','edly','less','ing',
        'tion','sion','ous','ive','ize','ise','ful','est',
        'er','ly','ed','es','s'
    ]
    w = word.lower()
    for s in suffixes:
        if w.endswith(s) and len(w) - len(s) >= 3:
            return w[:-len(s)]
    return w


def preprocess(text):
    """
    Full NLP Preprocessing Pipeline:
    1. Tokenize
    2. Remove stopwords
    3. Stem
    Returns both original tokens and stemmed tokens.
    """
    tokens = tokenize(text)
    tokens = remove_stopwords(tokens)
    stemmed = [stem(t) for t in tokens]
    return tokens, stemmed


def term_frequency(tokens):
    """
    TF (Term Frequency): count how often each term appears.
    IR Concept: foundation of TF-IDF weighting.
    """
    total = len(tokens)
    if total == 0:
        return {}
    counts = Counter(tokens)
    return {word: count / total for word, count in counts.items()}


def extract_keywords(text, top_n=10):
    """
    Keyword Extraction using TF scoring.
    Returns top N most important keywords from text.
    """
    tokens, stemmed = preprocess(text)
    tf = term_frequency(tokens)
    keywords = sorted(
        [(w, s) for w, s in tf.items() if len(w) >= 4],
        key=lambda x: x[1],
        reverse=True
    )
    return [w for w, _ in keywords[:top_n]]


def detect_topics(text):
    """
    Topic Detection: match text tokens against
    topic knowledge base patterns.
    IR Concept: Query-to-Index matching.
    """
    tokens, stemmed = preprocess(text)
    all_words = set(tokens + stemmed)
    detected = []

    for pattern in TOPIC_HASHTAGS.keys():
        keywords = pattern.split('|')
        for word in all_words:
            for kw in keywords:
                if kw in word or word in kw:
                    if pattern not in detected:
                        detected.append(pattern)
                    break

    return detected


def generate_from_text(text, count=20):
    """
    Core Hashtag Generation from text input.

    Steps:
    1. Extract keywords (Text Mining)
    2. Match topics to knowledge base (IR)
    3. Generate bigram combinations
    4. Score and rank all hashtags
    """
    tokens, stemmed = preprocess(text)
    all_words = set(tokens + stemmed)
    collected = set()

    # Step 1: Topic-based hashtags
    for pattern, hashtags in TOPIC_HASHTAGS.items():
        keywords = pattern.split('|')
        matched = False
        for word in all_words:
            for kw in keywords:
                if kw in word or word in kw:
                    matched = True
                    break
            if matched:
                break
        if matched:
            for tag in hashtags:
                collected.add(f"#{tag}")

    # Step 2: Direct keyword hashtags
    for token in tokens:
        if len(token) >= 4:
            collected.add(f"#{token.capitalize()}")
            collected.add(f"#{token}")

    # Step 3: Bigram combinations
    for i in range(len(tokens) - 1):
        w1, w2 = tokens[i], tokens[i + 1]
        if len(w1) >= 3 and len(w2) >= 3:
            collected.add(f"#{w1}{w2.capitalize()}")

    # Step 4: Score and rank
    scored = []
    for tag in collected:
        score = get_score(tag)
        scored.append({
            "tag": tag,
            "score": score,
            "label": get_score_label(score),
            "category": categorize(score),
            "source": "text_analysis"
        })

    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:count]