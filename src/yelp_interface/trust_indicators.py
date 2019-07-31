"""
Trust indicators from (Mauro et al. 2019) and (Fang et al. 2015)
for which coefficients will eventually be learned.
"""
import numpy as np
from tqdm import tqdm
from yelp_interface.fang_trust import FangTrust
from yelp_interface.mauro_trust import MauroTrust


class YelpTrustIndicators:
    """Calculate global trust indicators for all users.

    Also implements methods for calculating local trust indicators
    """

    def __init__(self, yelp_data):
        self._yelp_data = yelp_data
        self.fang_trust = FangTrust(yelp_data.reviews_by_item)
        self.mauro_trust = MauroTrust(list(yelp_data.users()))

    def vector_labels(self):
        return (self.mauro_trust.vector_labels() +
                self.fang_trust.vector_labels())

    def to_dataset(self, start, stop):
        users = list(self._yelp_data.users())
        if stop > len(users):
            msg = "'size' out of bounds. "
            msg += f"Only have {len(users)} users in memory."
            raise Exception(msg)

        X = []
        for i1 in tqdm(range(start, stop)):
            trustee = users[i1]
            for i2 in range(i1 + 1, stop):
                if i1 == i2:
                    continue
                truster = users[i2]
                feats = self.mauro_trust.get_vector(truster, trustee)
                feats.extend(self.fang_trust.get_vector(truster, trustee))
                X.append(np.array(feats, dtype=np.dtype('float32')))

        return np.array(X, dtype=np.dtype('float32'))
