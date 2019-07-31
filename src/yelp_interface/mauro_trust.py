from collections import defaultdict, Counter, OrderedDict


class MauroTrust():
    """Trust indicators from Mauro et al"""
    LAST_YEAR = 2019

    def __init__(self, users):
        self._users = users
        self._indicators = defaultdict(OrderedDict)
        self.compute_indicators()

    def get_vector(self, truster, trustee):
        truster_indicators = list(self.get_indicators(truster).values())
        trustee_indicators = list(self.get_indicators(trustee).values())
        values = truster_indicators + trustee_indicators
        values.append(self.social_relation(truster, trustee))
        values.append(self.is_friend(truster, trustee))
        return values

    def vector_labels(self):
        rand_key = next(iter(self._indicators.keys()))
        indi_labels = list(self._indicators[rand_key].keys())
        labels = []
        for prefix in ('truster_', 'trustee_'):
            for label in indi_labels:
                labels.append(f'{prefix}{label}')
        labels.append('social_jac')
        labels.append('are_friends')
        return labels

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

    def compute_indicators(self):
        self.compute_elite_years()
        self.compute_elite_per_year()
        self.compute_profile_up()
        self.compute_profile_up_per_year()
        self.compute_fans()
        self.compute_fans_per_year()
        self.compute_visibility()
        self.compute_global_feedback()
        self.compute_global_norm_feedback()

    def _addi(self, user, indicator_title, indicator_value):
        """Add an indicator with given title for given user"""
        self._indicators[user['user_id']][indicator_title] = indicator_value

    @staticmethod
    def social_relation(truster, trustee):
        numer = len(truster['friends'].intersection(trustee['friends']))
        denom = len(truster['friends'].union(trustee['friends']))
        if numer == 0:
            return 0
        return numer / denom

    @staticmethod
    def is_friend(truster, trustee):
        return trustee['user_id'] in truster['friends']

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

    def compute_elite_years(self):
        """Based on Mauro eq 13"""
        max_elite_years = max(self._elite_year_count(u)
                              for u in self._users)

        for u in self._users:
            elite_years = self._elite_year_count(u)
            self._addi(u, 'elite_years', elite_years / max_elite_years)

    def compute_elite_per_year(self):
        """A new indicator, elite years w.r.t number of years on site"""
        for u in self._users:
            elite_years = self._elite_year_count(u)
            if elite_years == 0:
                self._addi(u, 'elite_years_per_year', 0)
                continue

            years_on_site = self._years_on_site(u)
            self._addi(u, 'elite_years_per_year', elite_years / years_on_site)

    def _profile_up_count(self, user):
        return (user['compliment_hot'] + user['compliment_more'] +
                user['compliment_writer'] + user['compliment_profile'])

    def compute_profile_up(self):
        """Based on Mauro eq 14, but some changes because of yelp data"""
        max_ups = max(self._profile_up_count(u)
                      for u in self._users)
        for u in self._users:
            self._addi(u, 'profile_up', self._profile_up_count(u) / max_ups)

    def compute_profile_up_per_year(self):
        """Based on Mauro eq 14, normalized for years on site."""
        max_ups_per_year = max(self._profile_up_count(u) /
                               self._years_on_site(u)
                               for u in self._users)
        for u in self._users:
            indi = (self._profile_up_count(u) /
                    (self._years_on_site(u) * max_ups_per_year))
            self._addi(u, 'profile_up_per_year', indi)

    def compute_fans(self):
        """Based on Mauro eq 15"""
        max_fans = max(u['fans'] for u in self._users)
        for u in self._users:
            self._addi(u, 'fans', u['fans'] / max_fans)

    def compute_fans_per_year(self):
        """Based on Mauro eq 15, normalized for years on site"""
        max_fans_per_year = max(u['fans'] / self._years_on_site(u)
                                for u in self._users)
        for u in self._users:
            indi = u['fans'] / (self._years_on_site(u) * max_fans_per_year)
            self._addi(u, 'fans_per_year', indi)

    def compute_visibility(self):
        """Based on Mauro eq 16."""
        max_ups = max(self._profile_up_count(u)
                      for u in self._users)
        for u in self._users:
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

    def compute_global_feedback(self):
        """Based on Mauro eq 17"""
        max_feedback = max(self._count_global_feedback(u)
                           for u in self._users)
        for u in self._users:
            indi = self._count_global_feedback(u) / max_feedback
            self._addi(u, 'global_feedback', indi)

    def compute_global_norm_feedback(self):
        """Based on Mauro eq 17, normalized for number of contributions"""
        max_feedback = max((self._count_global_feedback(u) /
                            self._count_contributions(u))
                           for u in self._users)
        for u in self._users:
            indi = (self._count_global_feedback(u) /
                    (self._count_contributions(u) * max_feedback))
            self._addi(u, 'global_feedback_norm', indi)

    def global_feedback(self, user, item):
        """Based on Mauro eq 18: feedback relative to an item"""
        # TODO do I ever call this???
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
