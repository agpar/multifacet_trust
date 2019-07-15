"""
Trust indicators from (Mauro et al. 2019) and (Fang et al. 2015)
for which coefficients will eventually be learned.
"""
from collections import defaultdict

class YelpTrustIndicators:
    """Calculate global trust indicators for all users.

    Also implements methods for calculating local trust indicators
    """
    LAST_YEAR = 2019
    def __init__(self, yelp_data):
        self._yelp_data = yelp_data
        self._indicators = defaultdict(dict)
        self._compute_indicators()

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

    def _compute_indicators(self):
        self._compute_elite_years()
        self._compute_elite_per_year()
        self._compute_profile_up()
        self._compute_profile_up_per_year()

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
        max_elite_years = max(self._elite_year_count(u) for u in self._yelp_data.users())

        for u in self._yelp_data.users():
            elite_years = self._elite_year_count(u)
            self._indicators[u['user_id']]['elite_years'] = elite_years/max_elite_years

    def _compute_elite_per_year(self):
        """A new indicator, elite years w.r.t number of years on site"""
        for u in self._yelp_data.users():
            elite_years = self._elite_year_count(u)
            if elite_years == 0:
                self._indicators[u['user_id']]['elite_years_per_year'] = 0
                continue

            years_on_site = self._years_on_site(u)
            self._indicators[u['user_id']]['elite_years_per_year'] = elite_years / years_on_site

    def _profile_up_count(self, user):
        return user['compliment_hot'] + user['compliment_more'] + user['compliment_writer'] + user['compliment_profile']

    def _compute_profile_up(self):
        """Based on Muaro eq 14, but some changes because of yelp data"""
        max_ups = max(self._profile_up_count(u) for u in self._yelp_data.users())
        for u in self._yelp_data.users():
            self._indicators[u['user_id']]['profile_up'] = self._profile_up_count(u) / max_ups

    def _compute_profile_up_per_year(self):
        """Based on Muaro eq 14, but also dividing by years on site first"""
        max_ups_per_year = max(self._profile_up_count(u)/self._years_on_site(u) for u in self._yelp_data.users())
        for u in self._yelp_data.users():
            self._indicators[u['user_id']]['profile_up_per_year'] = (self._profile_up_count(u) / self._years_on_site(u)) / max_ups_per_year