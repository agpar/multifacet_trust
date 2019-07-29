"""
Standard methods for calculating review similarity.
"""

import math
import numpy as np
from tools.user_reviews import UserReviews


def review_pcc(user1_reviews: UserReviews,
               user2_reviews: UserReviews,
               avg_mode='OVERALL'):
    shared = user1_reviews.mutually_reviewed_items(user2_reviews)
    user1_tups = user1_reviews.get_pcc_tuples(shared, avg_mode)
    user2_tups = user2_reviews.get_pcc_tuples(shared, avg_mode)
    assert(len(user1_tups) == len(user2_tups))

    numer = 0
    denom1 = 0
    denom2 = 0
    for user1_tup, user2_tup in zip(user1_tups, user2_tups):
        item1_id, score1, avg1 = user1_tup
        item2_id, score2, avg2 = user2_tup
        assert(item1_id == item2_id)

        numer += (score1 - avg1) * (score2 - avg2)
        denom1 += pow(score1 - avg1, 2)
        denom2 += pow(score2 - avg2, 2)
    denom = math.sqrt(denom1 * denom2)

    if denom == 0:
        # Is this the best return option here?
        return 0
    else:
        return numer / denom


def review_cos(user1_reviews: UserReviews,
               user2_reviews: UserReviews):
    shared = user1_reviews.mutually_reviewed_items(user2_reviews)
    user1_tups = user1_reviews.get_pcc_tuples(shared)
    user2_tups = user2_reviews.get_pcc_tuples(shared)
    assert(len(user1_tups) == len(user2_tups))

    # Naive loop so that I can fit in an assertion.
    review_scores1 = []
    review_scores2 = []
    for user1_tup, user2_tup in zip(user1_tups, user2_tups):
        item1_id, score1, _ = user1_tup
        item2_id, score2, _ = user2_tup
        assert(item1_id == item2_id)
        review_scores1.append(score1)
        review_scores2.append(score2)

    numer = np.dot(review_scores1, review_scores2)
    denom = np.linalg.norm(review_scores1) * np.linalg.norm(review_scores2)
    return numer / denom






