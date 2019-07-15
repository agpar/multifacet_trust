"""
Methods for pulling data out of YELP dataset.

To reduce the amount of data pulled into memory, the current
plan is to specify some number of users (NUM_USERS) then only
pull in the reviews/businesses/tips that are relevant to those
users. In the case of a user having a friend that is not in
the selected set, that data will be retained but the system
will not recurse into importing that user.

Since these sets are so large, it might be good to write out
a subset before doing all the dev work.
"""
from os import path
from collections import defaultdict
from collections import namedtuple
import json
import copy


NUM_USERS = 10000
DATA_DIR = '/home/alex/Documents/datasets/yelp'
READ_SAMPLE = True

RatingTuple = namedtuple('Rating', 'user_id item_id score')

class YelpData:
    def __init__(self, users, reviews, tips, businesses):
        self._users = users
        self._reviews = reviews
        self._tips = tips
        self._businesses = businesses
        self._rating_tuples = []

    def get_user(self, user_id):
        user = self._users[user_id]
        if user.get('reviews'):
            return user
        reviews = self._reviews.get(user_id, [])
        tips = self._tips.get(user_id, [])
        user['reviews'], user['tips'] = [], []
        for review in reviews:
            business = self._businesses[review['business_id']]
            review['business'] = business
            user['reviews'].append(review)
        for tip in tips:
            business = self._businesses[tip['business_id']]
            tip['business'] = business
            user['tips'].append(tip)

        return user

    def users(self):
        for user in self._users.values():
            yield self.get_user(user['user_id'])

    def rating_tuples(self):
        if self._rating_tuples:
            return self.self._rating_tuples

        rating_tuples = []
        for user in self._users.values():
            for review in self._reviews[user['user_id']]:
                user_id = user['user_id']
                item_id = review['business_id']
                score = review['stars']
                rating_tuples.append(RatingTuple(user_id, item_id, score))
        self._rating_tuples = rating_tuples
        return rating_tuples


def read_data(read_sample=READ_SAMPLE):
    if not read_sample:
        USERS_FILE = path.join(DATA_DIR, 'user.json')
        BUSINESS_FILE = path.join(DATA_DIR, 'business.json')
        REVIEW_FILE = path.join(DATA_DIR, 'review.json')
        TIP_FILE = path.join(DATA_DIR, 'tip.json')
    else:
        USERS_FILE = path.join(DATA_DIR, 'user_sample.json')
        BUSINESS_FILE = path.join(DATA_DIR, 'business_sample.json')
        REVIEW_FILE = path.join(DATA_DIR, 'review_sample.json')
        TIP_FILE = path.join(DATA_DIR, 'tip_sample.json')

    # Indexed by user_id.
    users = {}
    with open(USERS_FILE, 'r') as f:
        num_read = 0
        for line in f:
            user = json.loads(line)
            users[user['user_id']] = user
            num_read += 1
            if num_read == NUM_USERS:
                break
    user_ids = set(users.keys())

    # Indexed by user_id
    reviews = defaultdict(list)
    with open(REVIEW_FILE, 'r') as f:
        for line in f:
            review = json.loads(line)
            if review['user_id'] in user_ids:
                review['text'] = ''
                reviews[review['user_id']].append(review)
    reviewed_business_ids = set([r['business_id'] for rlist in reviews.values() for r in rlist])


    # Indexed by user_id
    tips = defaultdict(list)
    with open(TIP_FILE, 'r') as f:
        for line in f:
            tip = json.loads(line)
            if tip['user_id'] in user_ids:
                tip['text'] = ''
                tips[tip['user_id']].append(tip)
    tipped_business_ids = set([t['business_id'] for tlist in tips.values() for t in tlist])


    # Indexed by review_id and tip id
    businesses = {}
    with open(BUSINESS_FILE) as f:
        for line in f:
            business = json.loads(line)
            if business['business_id'] in reviewed_business_ids or business['business_id'] in tipped_business_ids:
                businesses[business['business_id']] = business

    return YelpData(users, reviews, tips, businesses)


def save_sample(users, reviews, tips, businesses):
    """Write out the NUM_USERS samples so they can be used again later."""
    USER_SAMPLE_PATH = path.join(DATA_DIR, 'user_sample.json')
    REVIEW_SAMPLE_PATH = path.join(DATA_DIR, 'review_sample.json')
    TIP_SAMPLE_PATH = path.join(DATA_DIR, 'tip_sample.json')
    BUSINESS_SAMPLE_PATH = path.join(DATA_DIR, 'business_sample.json')

    with open(USER_SAMPLE_PATH, 'w') as f:
        for user in users.values():
            if user.get('reviews'):
                del user['reviews']
            f.write(json.dumps(user)+"\n")

    with open(REVIEW_SAMPLE_PATH, 'w') as f:
        for user_reviews in reviews.values():
            for review in user_reviews:
                if review.get('business'):
                    del review['business']
                f.write(json.dumps(review)+"\n")

    with open(TIP_SAMPLE_PATH, 'w') as f:
        for user_tips in tips.values():
            for tip in user_tips:
                if tip.get('business'):
                    del tip['business']
                f.write(json.dumps(tip)+"\n")

    with open(BUSINESS_SAMPLE_PATH, 'w') as f:
        for business in businesses.values():
            f.write(json.dumps(business)+"\n")