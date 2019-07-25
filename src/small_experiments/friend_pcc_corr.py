"""
A file to test whether or not friendship actually correlates
with similarity in terms of rating. Can you trust a friend more
than a non friend to give advise on the yelp data set?
"""

from os import path
import json
import math
from collections import defaultdict
from tqdm import tqdm
from yelp_interface.data_interface import YelpData as YD
from yelp_interface.trust_indicators import YelpTrustIndicators as YTI
from small_experiments.avg_review_score import AVG_REVIEW_SCORE


"""
EXP 1:
Compared to overall average review score
Using 20_000 users
    Avg non-friend pcc: 0.0147
    Avg frinds pcc: 0.0199

EXP 2:
Compared to overall average review score
Using 50_000 users


"""
DATA_DIR = '/home/alex/Documents/datasets/yelp'
USER_PATH = path.join(DATA_DIR, "user.json")
REVIEW_PATH = path.join(DATA_DIR, 'review.json')

SAMPLE_SIZE = 50_000
SHARE_CUTOFF = 3


def avg(lst):
    return sum(lst) / len(lst)


def are_friends(u1, u2):
    return 1 if u2['user_id'] in u1['friends'] else 0


def avg_review(review_list):
    return sum(r['stars'] for r in review_list) / len(review_list)


def cache_func(fn):
    """Cache a func where the first arg is an id"""
    cache = {}
    def wrapped(*args):
        key = args[0]
        if key in cache:
            return cache[key]
        val = fn(*args)
        cache[key] = val
        return val
    return wrapped


@cache_func
def avg_user_score(user_id, review_list):
    return avg_review(review_list)


@cache_func
def avg_item_score(item_id, review_list):
    return avg_review(review_list)


def pcc_useravg(review_scores1, avg1, review_scores2, avg2):
    # Now calculate PCC
    numer = 0
    denom1 = 0
    denom2 = 0
    for (item_id1, score1), (item_id2, score2) in zip(review_scores1, review_scores2):
        assert(item_id1 == item_id2)
        numer += (score1-avg1)*(score2-avg2)
        denom1 += pow(score1-avg1, 2)
        denom2 += pow(score2-avg2, 2)
    denom = math.sqrt(denom1 * denom2)

    if denom == 0:
        return 0
    else:
        return numer / denom


def pcc_itemavg(review_scores1, review_scores2, reviews_by_business):
    # Now calculate PCC
    numer = 0
    denom1 = 0
    denom2 = 0
    for (item_id1, score1), (item_id2, score2) in zip(review_scores1, review_scores2):
        assert(item_id1 == item_id2)
        item_avg = avg_item_score(item_id1, reviews_by_business[item_id1])
        numer += (score1 - item_avg) * (score2 - item_avg)
        denom1 += pow(score1 - item_avg, 2)
        denom2 += pow(score2 - item_avg, 2)
    denom = math.sqrt(denom1 * denom2)

    if denom == 0:
        return 0
    else:
        return numer / denom


def load_vectors():
    users = {}
    read_count = 0
    print("Loading USERS")
    with open(USER_PATH, 'r') as f:
        for line in f:
            full_user = json.loads(line)
            friends = YD.parse_friends(full_user)
            light_user = {
                'user_id': full_user['user_id'],
                'friends': friends
            }
            users[light_user['user_id']] = light_user
            read_count += 1
            if read_count >= SAMPLE_SIZE:
                break

    print("Loading REVIEWS")
    read_users = set(users.keys())
    reviews_by_user = defaultdict(list)
    with open(REVIEW_PATH, 'r') as f:
        for line in f:
            full_review = json.loads(line)
            if full_review['user_id'] not in read_users:
                continue
            light_review = {
                'user_id' : full_review['user_id'],
                'business_id': full_review['business_id'],
                'stars': full_review['stars']
            }
            reviews_by_user[light_review['user_id']].append(light_review)

    reviews_by_business = defaultdict(list)
    reviewed_by_user = defaultdict(set)
    for reviewlist in reviews_by_user.values():
        reviewlist.sort(key=lambda x: x['business_id'])
        for review in reviewlist:
            reviews_by_business[review['business_id']].append(review)
            reviewed_by_user[review['user_id']].add(review['business_id'])

    print("Generating VECTORS")
    user_list = list(users.values())
    vectors = []
    for i1 in tqdm(range(len(user_list))):
        u1 = user_list[i1]
        u1_reviews = reviews_by_user[u1['user_id']]
        u1_avg = avg_user_score(u1['user_id'], u1_reviews)
        u1_scores = [(r['business_id'], r['stars']) for r in u1_reviews]
        for i2 in range(i1 + 1, len(user_list)):
            u2 = user_list[i2]
            shared_items = reviewed_by_user[u1['user_id']].intersection(reviewed_by_user[u2['user_id']])
            if len(shared_items) < SHARE_CUTOFF:
                continue
            u2_reviews = reviews_by_user[u2['user_id']]
            u2_avg = avg_user_score(u2['user_id'], u2_reviews)
            u2_scores = [(r['business_id'], r['stars']) for r in u2_reviews]
            pcc = pcc_useravg(u1_scores, AVG_REVIEW_SCORE, u2_scores, AVG_REVIEW_SCORE)
            #pcc = pcc_itemavg(u1_scores, u2_scores, reviews_by_business)
            vectors.append([are_friends(u1, u2), pcc])

    return vectors

