# backend/src/predictor.py
# ─────────────────────────────────────────────────────────────
# Performance Predictor — estimates hashtag reach & engagement
#
# Predicts for each hashtag:
#   - Estimated reach (views)
#   - Engagement rate
#   - Competition level
#   - Best time to post
#   - Platform fit score
#   - Overall grade (A+ to D)
# ─────────────────────────────────────────────────────────────

import math
import re
from datetime import datetime


# ─────────────────────────────────────────────────────────────
# PLATFORM RULES
# ─────────────────────────────────────────────────────────────
PLATFORM_RULES = {
    'instagram': {
        'optimal_count':  25,
        'max_count':      30,
        'optimal_length': (5, 20),
        'reach_multiplier': 1.4,
        'best_times': ['6:00 AM', '12:00 PM', '7:00 PM', '9:00 PM'],
        'best_days':  ['Monday', 'Wednesday', 'Friday'],
    },
    'twitter': {
        'optimal_count':  2,
        'max_count':      3,
        'optimal_length': (4, 15),
        'reach_multiplier': 1.2,
        'best_times': ['8:00 AM', '12:00 PM', '5:00 PM'],
        'best_days':  ['Tuesday', 'Wednesday', 'Thursday'],
    },
    'linkedin': {
        'optimal_count':  5,
        'max_count':      10,
        'optimal_length': (5, 25),
        'reach_multiplier': 1.3,
        'best_times': ['7:00 AM', '10:00 AM', '12:00 PM'],
        'best_days':  ['Tuesday', 'Wednesday', 'Thursday'],
    },
    'youtube': {
        'optimal_count':  8,
        'max_count':      15,
        'optimal_length': (4, 20),
        'reach_multiplier': 1.1,
        'best_times': ['2:00 PM', '4:00 PM', '9:00 PM'],
        'best_days':  ['Friday', 'Saturday', 'Sunday'],
    },
    'github': {
        'optimal_count':  10,
        'max_count':      20,
        'optimal_length': (3, 20),
        'reach_multiplier': 0.9,
        'best_times': ['10:00 AM', '2:00 PM'],
        'best_days':  ['Monday', 'Tuesday', 'Wednesday'],
    },
    'all': {
        'optimal_count':  15,
        'max_count':      25,
        'optimal_length': (4, 20),
        'reach_multiplier': 1.0,
        'best_times': ['9:00 AM', '12:00 PM', '6:00 PM'],
        'best_days':  ['Tuesday', 'Wednesday', 'Thursday'],
    },
}

# ─────────────────────────────────────────────────────────────
# REACH ESTIMATES by popularity score band
# ─────────────────────────────────────────────────────────────
REACH_BANDS = [
    (90, 100, '🚀 Viral',    800_000,  5_000_000, 'Very High'),
    (80,  90, '🔥 Mega',     200_000,    800_000, 'High'),
    (70,  80, '📈 High',      50_000,    200_000, 'Medium-High'),
    (60,  70, '✅ Good',      10_000,     50_000, 'Medium'),
    (50,  60, '📊 Moderate',   2_000,     10_000, 'Low-Medium'),
    (40,  50, '🎯 Niche',       500,       2_000, 'Low'),
    ( 0,  40, '💤 Low',         100,         500, 'Very Low'),
]

# ─────────────────────────────────────────────────────────────
# ENGAGEMENT RATE by platform
# ─────────────────────────────────────────────────────────────
ENGAGEMENT_BASE = {
    'instagram': 0.058,
    'twitter':   0.025,
    'linkedin':  0.035,
    'youtube':   0.042,
    'github':    0.018,
    'all':       0.040,
}

# ─────────────────────────────────────────────────────────────
# GRADE HELPERS
# ─────────────────────────────────────────────────────────────
def score_to_grade(score):
    if score >= 88: return 'A+'
    if score >= 80: return 'A'
    if score >= 72: return 'B+'
    if score >= 64: return 'B'
    if score >= 55: return 'C+'
    if score >= 45: return 'C'
    return 'D'

def grade_color(grade):
    colors = {
        'A+': '#34d399', 'A':  '#4ade80',
        'B+': '#a3e635', 'B':  '#facc15',
        'C+': '#fb923c', 'C':  '#f87171',
        'D':  '#94a3b8',
    }
    return colors.get(grade, '#94a3b8')


# ─────────────────────────────────────────────────────────────
# PREDICT SINGLE HASHTAG
# ─────────────────────────────────────────────────────────────
def predict_hashtag(tag, score, platform='all', category='broad'):
    platform_key = platform if platform in PLATFORM_RULES else 'all'
    rules        = PLATFORM_RULES[platform_key]
    clean        = tag.replace('#', '')
    tag_len      = len(clean)

    # Reach estimate
    reach_label, reach_min, reach_max, competition = '', 0, 0, 'Medium'
    for band in REACH_BANDS:
        if band[0] <= score <= band[1]:
            reach_label = band[2]
            reach_min   = band[3]
            reach_max   = band[4]
            competition = band[5]
            break

    multiplier = rules['reach_multiplier']
    reach_min  = int(reach_min * multiplier)
    reach_max  = int(reach_max * multiplier)

    def fmt(n):
        if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
        if n >= 1_000:     return f"{n/1_000:.0f}K"
        return str(n)

    reach_str = f"{fmt(reach_min)} – {fmt(reach_max)}"

    # Engagement
    base_rate    = ENGAGEMENT_BASE.get(platform_key, 0.04)
    score_factor = score / 100
    niche_bonus  = 0.02 if category == 'niche' else 0
    engagement   = round((base_rate * (0.5 + score_factor * 0.5) + niche_bonus) * 100, 1)

    # Length score
    opt_min, opt_max = rules['optimal_length']
    if opt_min <= tag_len <= opt_max:
        length_score = 100
        length_note  = 'Optimal length'
    elif tag_len < opt_min:
        length_score = 70
        length_note  = 'Too short'
    elif tag_len <= opt_max + 5:
        length_score = 80
        length_note  = 'Slightly long'
    else:
        length_score = 50
        length_note  = 'Too long — harder to read'

    # Platform fit
    platform_fit = min(100, int(score * 0.6 + length_score * 0.4))

    # Overall
    overall    = int(score * 0.45 + platform_fit * 0.30 + length_score * 0.25)
    grade      = score_to_grade(overall)
    grade_col  = grade_color(grade)

    # Tips
    tips = []
    if tag_len > opt_max:
        tips.append(f"Shorten to under {opt_max} chars for {platform_key}")
    if category == 'niche':
        tips.append("Niche tag → higher engagement, lower reach")
    if category == 'trending':
        tips.append("Trending tag → high competition, post at peak time")
    if score >= 80:
        tips.append("High competition — pair with niche tags")
    if score < 50:
        tips.append("Low volume — great for targeted audience")
    if not tips:
        tips.append(f"Well-optimised for {platform_key}")

    return {
        'tag':             tag,
        'score':           score,
        'category':        category,
        'grade':           grade,
        'grade_color':     grade_col,
        'overall':         overall,
        'reach_label':     reach_label,
        'reach_range':     reach_str,
        'reach_min':       reach_min,
        'reach_max':       reach_max,
        'engagement_rate': f"{engagement}%",
        'engagement_val':  engagement,
        'competition':     competition,
        'length_score':    length_score,
        'length_note':     length_note,
        'tag_length':      tag_len,
        'platform_fit':    platform_fit,
        'best_time':       rules['best_times'][0],
        'best_days':       rules['best_days'],
        'tips':            tips,
    }


# ─────────────────────────────────────────────────────────────
# PREDICT ALL HASHTAGS
# ─────────────────────────────────────────────────────────────
def predict_all(hashtags, platform='all', top_n=10):
    predictions = []
    for h in hashtags[:top_n]:
        pred = predict_hashtag(
            tag      = h['tag'],
            score    = h.get('score', 50),
            platform = platform,
            category = h.get('category', 'broad'),
        )
        predictions.append(pred)

    if not predictions:
        return {'predictions': [], 'summary': {}}

    grades      = [p['grade'] for p in predictions]
    avg_overall = round(sum(p['overall'] for p in predictions) / len(predictions))
    avg_engage  = round(sum(p['engagement_val'] for p in predictions) / len(predictions), 1)
    top_pred    = max(predictions, key=lambda p: p['overall'])
    rules       = PLATFORM_RULES.get(platform, PLATFORM_RULES['all'])

    trending_count = sum(1 for p in predictions if p['category'] == 'trending')
    niche_count    = sum(1 for p in predictions if p['category'] == 'niche')
    broad_count    = sum(1 for p in predictions if p['category'] == 'broad')

    if trending_count > niche_count + broad_count:
        mix_tip = "Add more niche tags to balance high competition trending tags"
    elif niche_count > trending_count + broad_count:
        mix_tip = "Add some trending tags to increase overall reach"
    else:
        mix_tip = "Good mix of trending, broad and niche tags!"

    return {
        'predictions': predictions,
        'summary': {
            'avg_overall':      avg_overall,
            'avg_grade':        score_to_grade(avg_overall),
            'avg_grade_color':  grade_color(score_to_grade(avg_overall)),
            'avg_engagement':   f"{avg_engage}%",
            'top_tag':          top_pred['tag'],
            'top_grade':        top_pred['grade'],
            'best_time':        rules['best_times'][0],
            'best_days':        rules['best_days'],
            'mix_tip':          mix_tip,
            'total_predicted':  len(predictions),
            'grade_counts': {
                'A': sum(1 for g in grades if g in ['A+', 'A']),
                'B': sum(1 for g in grades if g in ['B+', 'B']),
                'C': sum(1 for g in grades if g in ['C+', 'C']),
                'D': sum(1 for g in grades if g == 'D'),
            }
        }
    }