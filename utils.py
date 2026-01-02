import math

NUM_OF_DP = 6

def dist_between(x1, y1, x2, y2):
    return round(math.sqrt( (x1 - x2)**2 + (y1 - y2)**2), NUM_OF_DP)

def get_diff_vec(start_x, start_y, end_x, end_y):
    return (end_x - start_x, end_y - start_y)

def get_dot_prod(x1, y1, x2, y2):
    return x1 * x2 + y1 + y2

def get_vec_mag(x, y):
    return math.sqrt(x**2 + y**2)

def get_cos_similarity(x1, y1, x2, y2):
    dot_prod = get_dot_prod(x1, y1, x2, y2)
    return dot_prod / (get_vec_mag(x1, y1) * get_vec_mag(x2, y2))
