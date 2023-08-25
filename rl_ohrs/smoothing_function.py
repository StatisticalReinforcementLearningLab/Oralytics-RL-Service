import numpy as np
from scipy.special import expit

"""### Smoothing Functions
---
"""
# generalized logistic function https://en.wikipedia.org/wiki/Generalised_logistic_function
# lower and upper asymptotes (clipping values)
L_min = 0.2
L_max = 0.8
# larger values of b > 0 makes curve more "steep"
B_logistic = 0.515
# larger values of c > 0 shifts the value of function(0) to the right
C_logistic = 3
# larger values of k > 0 makes the asmptote towards upper clipping less steep
# and the asymptote towards the lower clipping more steep
K_logistic = 1

# uses scipy.special.expit for numerical stability
def genearlized_logistic_func(x):
    num = L_max - L_min
    stable_exp = expit(B_logistic * x - np.log(C_logistic))
    stable_exp_k = stable_exp**K_logistic

    return L_min + num * stable_exp_k
