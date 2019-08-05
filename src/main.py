from yelp_interface.data_interface import read_data
from yelp_interface.trust_indicators import YelpTrustIndicators
from small_experiments import friend_pcc_corr as fpcc
from small_experiments.friend_pcc_corr import gen_vectors
from regression import *
import time

yd = read_data()
yti = YelpTrustIndicators(yd)
# users, reviews_by_business = fpcc.load_data()


def gen_data(yti, start, stop):
    start_time = time.time()
    X = yti.to_dataset(start, stop)
    stop_time = time.time()
    print(f"Generation took {stop_time-start_time} seconds.")
    return X
