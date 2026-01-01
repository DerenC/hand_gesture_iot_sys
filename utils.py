import math

NUM_OF_DP = 6

def dist_between(x1, y1, x2, y2):
    return round(math.sqrt( (x1 - x2)**2 + (y1 - y2)**2), NUM_OF_DP)
