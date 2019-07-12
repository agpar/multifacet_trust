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
import json

NUM_USERS = 10000
DATA_DIR = '/home/alex/Documents/datasets/yelp'
READ_SAMPLE = True

if not READ_SAMPLE:
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
reviewed_business_ids = dict({r['business_id']: r['review_id'] for rlist in reviews.values() for r in rlist})


# Indexed by review_id
businesses = {}
with open(BUSINESS_FILE) as f:
    for line in f:
        business = json.loads(line)
        if business['business_id'] in reviewed_business_ids.keys():
            businesses[reviewed_business_ids[business['business_id']]] = business


def save_sample():
    """Write out the NUM_USERS samples so they can be used again later."""
    USER_SAMPLE_PATH = path.join(DATA_DIR, 'user_sample.json')
    BUSINESS_SAMPLE_PATH = path.join(DATA_DIR, 'business_sample.json')
    REVIEW_SAMPLE_PATH = path.join(DATA_DIR, 'review_sample.json')

    with open(USER_SAMPLE_PATH, 'w') as f:
        for user in users.values():
            f.write(json.dumps(user)+"\n")

    with open(BUSINESS_SAMPLE_PATH, 'w') as f:
        for business in businesses.values():
            f.write(json.dumps(business)+"\n")

    with open(REVIEW_SAMPLE_PATH, 'w') as f:
        for user_reviews in reviews.values():
            for review in user_reviews:
                f.write(json.dumps(review)+"\n")