"""
Trust indicators from (Mauro et al. 2019) and (Fang et al. 2015)
for which coefficients will eventually be learned.
"""
from collections import defaultdict, Counter
import numpy as np
from tqdm import tqdm
from tools.review_similarity import review_pcc, review_cos, pcc, cos
from tools.user_reviews import avg_user_score, avg_item_score


class YelpTrustIndicators:
    """Calculate global trust indicators for all users.

    Also implements methods for calculating local trust indicators
    """
    LAST_YEAR = 2019

    def __init__(self, yelp_data):
        self._yelp_data = yelp_data
        self._indicators = defaultdict(dict)
        self._compute_indicators()
        self._cache = defaultdict(dict)

    def get_indicators(self, user):
        indicators = None
        if isinstance(user, str):
            key = user
        elif isinstance(user, dict):
            key = user['user_id']
        else:
            raise Exception("'user' is not string or a dict")

        indicators = self._indicators.get(key)
        if indicators is None:
            raise KeyError(f"'{key}'")
        return indicators

    def _addi(self, user, indicator_title, indicator_value):
        """Add an indicator with given title for given user"""
        self._indicators[user['user_id']][indicator_title] = indicator_value

    def _put_cachei(self, user, indicator_title, indicator_value):
        self._cache[user['user_id']][indicator_title] = indicator_value

    def _get_cachei(self, user, indicator_title):
        return self._cache[user['user_id']].get(indicator_title, None)

    def _compute_indicators(self):
        self._compute_elite_years()
        self._compute_elite_per_year()
        self._compute_profile_up()
        self._compute_profile_up_per_year()
        self._compute_fans()
        self._compute_fans_per_year()
        self._compute_visibility()
        self._compute_global_feedback()
        self._compute_global_norm_feedback()

    def _elite_year_count(self, user):
        if not user['elite']:
            return 0
        else:
            return len(user['elite'].split(','))

    def _years_on_site(self, user):
        join_date = user['yelping_since']
        join_year = int(join_date.split('-')[0])
        if join_year == self.LAST_YEAR:
            raise Exception(f"Unexpectedly fresh account: {user['user_id']}")
        years_since_join = self.LAST_YEAR - join_year
        return years_since_join

    def _compute_elite_years(self):
        """Based on Mauro eq 13"""
        max_elite_years = max(self._elite_year_count(u)
                              for u in self._yelp_data.users())

        for u in self._yelp_data.users():
            elite_years = self._elite_year_count(u)
            self._addi(u, 'elite_years', elite_years / max_elite_years)

    def _compute_elite_per_year(self):
        """A new indicator, elite years w.r.t number of years on site"""
        for u in self._yelp_data.users():
            elite_years = self._elite_year_count(u)
            if elite_years == 0:
                self._indicators[u['user_id']]['elite_years_per_year'] = 0
                continue

            years_on_site = self._years_on_site(u)
            self._addi(u, 'elite_years_per_year', elite_years / years_on_site)

    def _profile_up_count(self, user):
        return (user['compliment_hot'] + user['compliment_more'] +
                user['compliment_writer'] + user['compliment_profile'])

    def _compute_profile_up(self):
        """Based on Mauro eq 14, but some changes because of yelp data"""
        max_ups = max(self._profile_up_count(u)
                      for u in self._yelp_data.users())
        for u in self._yelp_data.users():
            self._addi(u, 'profile_up', self._profile_up_count(u) / max_ups)

    def _compute_profile_up_per_year(self):
        """Based on Mauro eq 14, normalized for years on site."""
        max_ups_per_year = max(self._profile_up_count(u) /
                               self._years_on_site(u)
                               for u in self._yelp_data.users())
        for u in self._yelp_data.users():
            indi = (self._profile_up_count(u) /
                    (self._years_on_site(u) * max_ups_per_year))
            self._addi(u, 'profile_up_per_year', indi)

    def _compute_fans(self):
        """Based on Mauro eq 15"""
        max_fans = max(u['fans'] for u in self._yelp_data.users())
        for u in self._yelp_data.users():
            self._addi(u, 'fans', u['fans'] / max_fans)

    def _compute_fans_per_year(self):
        """Based on Mauro eq 15, normalized for years on site"""
        max_fans_per_year = max(u['fans'] / self._years_on_site(u)
                                for u in self._yelp_data.users())
        for u in self._yelp_data.users():
            indi = u['fans'] / (self._years_on_site(u) * max_fans_per_year)
            self._addi(u, 'fans_per_year', indi)

    def _compute_visibility(self):
        """Based on Mauro eq 16."""
        max_ups = max(self._profile_up_count(u)
                      for u in self._yelp_data.users())
        for u in self._yelp_data.users():
            activity_level = self._count_contributions(u)
            indi = self._profile_up_count(u) / (max_ups * activity_level)
            self._addi(u, 'visibility', indi)

    def _count_global_feedback(self, user):
        up_count = 0
        for review in user['reviews']:
            up_count += review['useful']
            up_count += review['funny']
            up_count += review['cool']
        for tip in user['tips']:
            up_count += tip['compliment_count']
        return up_count

    def _count_contributions(self, user):
        return len(user['reviews']) + len(user['tips'])

    def _compute_global_feedback(self):
        """Based on Mauro eq 17"""
        max_feedback = max(self._count_global_feedback(u)
                           for u in self._yelp_data.users())
        for u in self._yelp_data.users():
            indi = self._count_global_feedback(u) / max_feedback
            self._addi(u, 'global_feedback', indi)

    def _compute_global_norm_feedback(self):
        """Based on Mauro eq 17, normalized for number of contributions"""
        max_feedback = max((self._count_global_feedback(u) /
                            self._count_contributions(u))
                           for u in self._yelp_data.users())
        for u in self._yelp_data.users():
            indi = (self._count_global_feedback(u) /
                    (self._count_contributions(u) * max_feedback))
            self._addi(u, 'global_feedback_norm', indi)

    def global_feedback(self, user, item):
        """Based on Mauro eq 18: feedback relative to an item"""
        reviews = self._yelp_data.get_reviews_for_item(item)
        tips = self._yelp_data.get_tips_for_item(item)
        counter = Counter()

        for review in reviews:
            user_id = review['user_id']
            counter[user_id] += review['useful']
            counter[user_id] += review['funny']
            counter[user_id] += review['cool']
        for tip in tips:
            user_id = tip['user_id']
            counter[user_id] += tip['compliment_count']

        most_common = counter.most_common()
        if not most_common:
            raise Exception(f"No one has ever reviewed {item}")
        _, max_ups = most_common[0]
        if max_ups == 0:
            raise Exception(f"No one has ever been complimented for reviewing {item}")
        return counter[user['user_id']] / max_ups

    @staticmethod
    def social_relation(truster, trustee):
        numer = len(truster['friends'].intersection(trustee['friends']))
        denom = len(truster['friends'].union(trustee['friends']))
        if numer == 0:
            return 0
        return numer / denom

    def benevolence_pcc(self, truster, trustee):
        reviews1 = truster['reviews']
        reviews2 = trustee['reviews']
        return review_pcc(reviews1, reviews2, avg_mode='OVERALL')

    def benevolence_cos(self, truster, trustee):
        reviews1 = truster['reviews']
        reviews2 = trustee['reviews']
        return review_cos(reviews1, reviews2)

    def integrity_pcc(self, user):
        cached_val = self._get_cachei(user, 'integrity_pcc')
        if cached_val:
            return cached_val

        reviews = user['reviews']
        avg_reviews = []
        for r in reviews:
            revs = self._yelp_data.get_reviews_for_item(r['business_id'])
            avg = avg_item_score(r['business_id'], revs)
            avg_reviews.append(avg)

        user_scores = [r['stars'] for r in reviews]
        user_avg = avg_user_score(user['user_id'], reviews)
        user_avgs = [user_avg for i in range(len(reviews))]
        global_avgs = [self._yelp_data.review_avg for i in range(len(reviews))]
        val = pcc(user_scores, user_avgs, avg_reviews, global_avgs)
        self._put_cachei(user, 'integrity_pcc', val)
        return val

    def integrity_cos(self, user):
        cached_val = self._get_cachei(user, 'integrity_cos')
        if cached_val:
            return cached_val

        reviews = user['reviews']
        avg_reviews = []
        for r in reviews:
            revs = self._yelp_data.get_reviews_for_item(r['business_id'])
            avg = avg_item_score(r['business_id'], revs)
            avg_reviews.append(avg)

        user_scores = [r['stars'] for r in reviews]
        val = cos(user_scores, avg_reviews)
        self._put_cachei(user, 'integrity_cos', val)
        return val

    def competence(self, user):
        cached_val = self._get_cachei(user, 'competence')
        if cached_val:
            return cached_val

        e = 0.5
        numer = 0
        denom = 0
        for review in user['reviews']:
            other_reviews = self._yelp_data.get_reviews_for_item(review['business_id'])
            numer += len([r for r in other_reviews if abs(r['stars'] - review['stars']) < e])
            denom += len(other_reviews)
        val = numer / denom

        self._put_cachei(user, 'competence', val)
        return val

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
                     sorted(self.get_indicators(trustee).items())]
            for i2 in range(start, stop):
                if i1 == i2:
                    continue
                truster = users[i2]
                x = [i for i in trustee_feats]

                # Add individual relationships
                x.append(self.social_relation(truster, trustee))
                x.append(self.benevolence_pcc(truster, trustee))
                x.append(self.benevolence_cos(truster, trustee))
                x.append(self.integrity_pcc(trustee))
                x.append(self.integrity_cos(trustee))
                x.append(self.competence(trustee))

                y = 1 if self.is_friend(truster, trustee) else 0
                X.append(np.array(x))
                Y.append(y)

        return np.array(X), np.array(Y)
