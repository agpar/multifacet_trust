from os import path
import json
import settings

DATA_DIR = settings.DATA_DIR
REVIEW_PATH = path.join(DATA_DIR, 'review.json')

# Based on running avg_review_score() - just saving data here.
AVG_REVIEW_SCORE = 3.7161

def avg_review_score():
    stars = 0
    review_count = 0
    with open(REVIEW_PATH, 'r') as f:
        for line in f:
            full_review = json.loads(line)
            stars += full_review['stars']
            review_count += 1
    return stars / review_count
