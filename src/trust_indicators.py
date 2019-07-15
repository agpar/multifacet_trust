"""
Trust indicators from (Mauro et al. 2019) and (Fang et al. 2015)
for which coefficients will eventually be learned.
"""
from collections import defaultdict

class YelpTrustIndicators:
    """Calculate global trust indicators for all users.

    Also implements methods for calculating local trust indicators
    """
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
            raise KeyError(f'{key}')
        return indicators

    def _compute_indicators(self):
        self._compute_elite_years()
        self._compute_elite_since_joining()

    def _elite_year_count(self, user):
        if not user['elite']:
            return 0
        else:
            return len(u['elite'].split(','))

    def _compute_elite_years(self):
        """Based on Mauro eq 13"""
        max_elite_years = max(self._elite_year_count(u) for u in self._yelp_data.users())

        for u in self._yelp_data.users():
            elite_years = self._elite_year_count(u)
            self._indicators[u['user_id']]['elite_years'] = elite_years/max_elite_years

    def _compute_elite_since_joining(self):
        """A new indicator, elite years w.r.t number of years on site"""
        for u in self._yelp_data.users():
            elite_years = self._elite_year_count(u)
            if elite_years == 0:
                self._indicators[u['user_id']]['elite_years_since_join'] = 0
                continue

            join_date = u['yelping_since']
            join_year = int(join_date.split('-')[0])
            years_since_join = 2019 - join_year
            elite_years = self._elite_year_count(u)

            # Note, we already handled the case where user was never elite.
            if years_since_join == 0:
                self._indicators[u['user_id']]['elite_years_since_join'] = 1
            else:
                self._indicators[u['user_id']]['elite_years_since_join'] = elite_years / years_since_join

