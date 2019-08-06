"""
A file to test whether or not friendship actually correlates
with similarity in terms of rating. Can you trust a friend more
than a non friend to give advise on the yelp data set?
"""

from os import path
import json
from collections import defaultdict
from yelp_interface.data_interface import YelpData as YD
from tools.user_reviews import UserReviews
from tools.review_similarity import review_pcc
import settings
"""
EXP 1:
Compared to overall average review score
Using 20_000 users
Minimum 3 ratings in common
    Avg frinds pcc: 0.2293
    Avg non-friend pcc: 0.1843

Compared to overall average review score
Using 50_000 users
Minimum 3 ratings in common
    Avg frinds pcc: 0.2307
    Avg non-friend pcc: 0.1791

EXP 3:
Compared to item average review score
Using 20_000 users
Minimum 3 ratings in common
    Avg frinds pcc: 0.007
    Avg non-friend pcc: -0.011
"""


DATA_DIR = settings.DATA_DIR
USER_PATH = path.join(DATA_DIR, "user.json")
REVIEW_PATH = path.join(DATA_DIR, 'review.json')

SAMPLE_SIZE = 2000
SHARE_CUTOFF = 3


def are_friends(u1, u2):
    return 1 if u2['user_id'] in u1['friends'] else 0


def load_data():
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
                'user_id': full_review['user_id'],
                'date': full_review['date'],
                'business_id': full_review['business_id'],
                'stars': full_review['stars']
            }
            reviews_by_user[light_review['user_id']].append(light_review)

    reviews_by_business = defaultdict(list)
    for reviewlist in reviews_by_user.values():
        for review in reviewlist:
            reviews_by_business[review['business_id']].append(review)

    for user in users.values():
        user['reviews'] = UserReviews(
            reviews_by_user[user['user_id']],
            reviews_by_business)

    return users, reviews_by_business


def gen_vectors(users, reviews_by_business, PARALLEL=True):
    print("Generating function calls")
    user_list = list(users.values())
    vectors = []

    for i1 in range(len(user_list)):
        u1 = user_list[i1]
        for i2 in range(i1 + 1, len(user_list)):
            u2 = user_list[i2]
            shared_items = u1['reviews'].mutually_reviewed_items(u2['reviews'])
            if len(shared_items) < SHARE_CUTOFF:
                continue

            u1u2_pcc = review_pcc(u1['reviews'], u2['reviews'], "OVERALL")
            vectors.append([are_friends(u1, u2), u1u2_pcc])
    return vectors
