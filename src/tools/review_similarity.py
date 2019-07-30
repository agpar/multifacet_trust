"""
Standard methods for calculating review similarity.
"""

import math
import numpy as np
from tools.user_reviews import UserReviews


def pcc(scores1, avgs1, scores2, avgs2):
    assert(len(scores1) == len(avgs1))
    assert(len(avgs1) == len(scores2))
    assert(len(scores2) == len(avgs2))
    if len(scores1) == 0:
        return 0
    numer = 0
    denom1 = 0
    denom2 = 0
    for s1, a1, s2, a2 in zip(scores1, avgs1, scores2, avgs2):
        numer += (s1 - a1) * (s2 - a2)
        denom1 += pow(s1 - a1, 2)
        denom2 += pow(s2 - a2, 2)
    denom = math.sqrt(denom1 * denom2)

    if denom == 0:
        # Is this the best return option here?
        return 0
    else:
        return numer / denom
    pass


def cos(scores1, scores2):
    assert(len(scores1) == len(scores2))
    if len(scores1) == 0:
        return 0
    numer = np.dot(scores1, scores2)
    denom = np.linalg.norm(scores1) * np.linalg.norm(scores2)
    return numer / denom


def review_pcc(user1_reviews: UserReviews,
               user2_reviews: UserReviews,
               avg_mode='OVERALL'):
    shared = user1_reviews.mutually_reviewed_items(user2_reviews)
    user1_tups = user1_reviews.get_pcc_tuples(shared, avg_mode)
    user2_tups = user2_reviews.get_pcc_tuples(shared, avg_mode)
    assert(len(user1_tups) == len(user2_tups))
    s1, a1, s2, a2 = _pcc_setup(user1_tups, user2_tups)
    return pcc(s1, a1, s2, a2)


def review_cos(user1_reviews: UserReviews,
               user2_reviews: UserReviews):
    shared = user1_reviews.mutually_reviewed_items(user2_reviews)
    user1_tups = user1_reviews.get_pcc_tuples(shared)
    user2_tups = user2_reviews.get_pcc_tuples(shared)
    assert(len(user1_tups) == len(user2_tups))

    scores1, _, scores2, _ = _pcc_setup(user1_tups, user2_tups)
    return cos(scores1, scores2)


def _pcc_setup(user1_tups, user2_tups):
    # Naive loop so that I can fit in an assertion.
    scores1 = []
    avgs1 = []
    scores2 = []
    avgs2 = []
    for user1_tup, user2_tup in zip(user1_tups, user2_tups):
        item1_id, score1, avg1 = user1_tup
        item2_id, score2, avg2 = user2_tup
        assert(item1_id == item2_id)
        scores1.append(score1)
        avgs1.append(avg1)
        scores2.append(score2)
        avgs2.append(avg2)
    return scores1, avgs1, scores2, avgs2
