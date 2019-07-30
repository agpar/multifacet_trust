def cache_func(fn):
    """Cache a func where the first arg is an id"""
    cache = {}

    def wrapped(*args):
        key = args[0]
        if key in cache:
            return cache[key]
        val = fn(*args)
        cache[key] = val
        return val
    return wrapped


def avg_review(review_list):
    return sum(r['stars'] for r in review_list) / len(review_list)


@cache_func
def avg_user_score(user_id, review_list):
    return avg_review(review_list)


@cache_func
def avg_item_score(item_id, review_list):
    return avg_review(review_list)


class UserReviews:
    """A collection of user reviews.

    Offers methods for working with these collections.
    """
    AVG_MODES = set(["ITEM", "USER", "OVERALL"])
    AVG_REVIEW_SCORE = 3.7161

    def __init__(self, review_list, reviews_by_items):
        self.reviewed_items = set(r['business_id'] for r in review_list)
        sorted_reviews = sorted(review_list, key=lambda r: r['business_id'])
        self.review_list = self._remove_dupes(
            sorted_reviews,
            self.reviewed_items)
        self.review_list.sort(key=lambda r: r['business_id'])
        self.reviews_by_items = reviews_by_items

    def get_pcc_tuples(self, item_ids, avg_mode='OVERALL'):
        review_tuples = []
        relevant_reviews = [r for r in self.review_list
                            if r['business_id'] in item_ids]
        review_avgs = self.get_avgs(relevant_reviews, avg_mode)
        for review, avg in zip(relevant_reviews, review_avgs):
            item_id = review['business_id']
            score = review['stars']
            review_tuples.append((item_id, score, avg))
        return review_tuples

    def mutually_reviewed_items(self, other_reviews):
        """Compute the set of items both users have reviewed"""
        shared = self.reviewed_items.intersection(other_reviews.reviewed_items)
        return shared

    def get_avgs(self, review_list, avg_mode):
        """Computes a list of average reviews for each review.

        Averages can be:
            ITEM: the average review score for that item
            USER: the average reveiw score for the user
            OVERALL: the overall average review score.
        """
        if avg_mode == "ITEM":
            return self._item_review_avg(review_list)
        elif avg_mode == "USER":
            return self._user_review_avg(review_list)
        elif avg_mode == "OVERALL":
            return self._overall_review_avg(review_list)
        else:
            modes = ", ".join(self.AVG_MODES)
            msg = f"'avg_mode' must be in {modes}"
            raise Exception(msg)

    def _item_review_avg(self, review_list):
        for review in review_list:
            item_id = review['business_id']
            avg = avg_item_score(item_id, self._reviews_by_items[item_id])
            yield avg

    def _user_review_avg(self, review_list):
        user_id = self.review_list[0]['user_id']
        avg = avg_user_score(user_id, self.review_list)
        return (avg for i in range(len(review_list)))

    def _overall_review_avg(self, review_list):
        return (self.AVG_REVIEW_SCORE for i in range(len(review_list)))

    def _remove_dupes(self, reviews, reviewed_items):
        """Only retain the latest review for each item.

        Assumes reviews is sorted by business id.
        """
        if not self._has_dupes(reviews, reviewed_items):
            return reviews
        else:
            deduped_reviews = self._linear_dupe_removal(reviews)
            assert(len(deduped_reviews) == len(reviewed_items))
            return deduped_reviews

    def _has_dupes(self, reviews, reviewed_items):
        return len(reviews) != len(reviewed_items)

    def _linear_dupe_removal(self, reviews):
        """Return only the latest review for each item

        I tried to make this fast, but in retrospect it probably
        doesn't matter since the average user probably has <100
        reviews
        """
        i = 0
        deduped_reviews = []
        current_item = reviews[0]['business_id']
        latest_review_for_item = reviews[0]
        while i < len(reviews) - 1:
            next_review = reviews[i + 1]
            if (next_review['business_id'] < current_item):
                raise Exception("Reviews must be sorted by business_id")

            if next_review['business_id'] == current_item:
                if next_review['date'] > latest_review_for_item['date']:
                    latest_review_for_item = next_review
            else:
                deduped_reviews.append(latest_review_for_item)
                current_item = next_review['business_id']
                latest_review_for_item = next_review
            i += 1
        deduped_reviews.append(latest_review_for_item)
        return deduped_reviews

    def __iter__(self):
        return self.review_list.__iter__()

    def __getitem__(self, key):
        return self.review_list[key]

    def __len__(self):
        return len(self.review_list)
