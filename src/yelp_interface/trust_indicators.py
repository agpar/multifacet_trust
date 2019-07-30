"""
Trust indicators from (Mauro et al. 2019) and (Fang et al. 2015)
for which coefficients will eventually be learned.
"""
from collections import defaultdict, Counter
import numpy as np
from tqdm import tqdm
from tools.review_similarity import review_pcc, review_cos, pcc, cos
from tools.user_reviews import avg_user_score, avg_item_score
from yelp_interface.fang_trust import FangTrust
from yelp_interface.mauro_trust import MauroTrust


class YelpTrustIndicators:
    """Calculate global trust indicators for all users.

    Also implements methods for calculating local trust indicators
    """
    LAST_YEAR = 2019

    def __init__(self, yelp_data):
        self._yelp_data = yelp_data
        self._indicators = defaultdict(dict)
        self.fang_trust = FangTrust(yelp_data.reviews_by_item)
        self.mauro_trust = MauroTrust(list(yelp_data.users()))

    @staticmethod
    def is_friend(truster, trustee):
        return trustee['user_id'] in truster['friends']

    def to_dataset(self, start, stop):
        X, Y = [], []
        users = list(self._yelp_data.users())
        if stop > len(users):
            raise Exception(f"'size' out of bounds. Only have {len(users)} users in memory.")

        for i1 in tqdm(range(start, stop)):
            trustee = users[i1]
            trustee_feats = [val for (key, val) in
                     sorted(self.mauro_trust.get_indicators(trustee).items())]
            for i2 in range(start, stop):
                if i1 == i2:
                    continue
                truster = users[i2]
                x = [i for i in trustee_feats]

                # Add individual relationships
                x.append(self.mauro_trust.social_relation(truster, trustee))
                x.append(self.fang_trust.benevolence_pcc(truster, trustee))
                x.append(self.fang_trust.benevolence_cos(truster, trustee))
                x.append(self.fang_trust.integrity_pcc(trustee))
                x.append(self.fang_trust.integrity_cos(trustee))
                x.append(self.fang_trust.competence(trustee))

                y = 1 if self.is_friend(truster, trustee) else 0
                X.append(np.array(x))
                Y.append(y)

        return np.array(X), np.array(Y)
