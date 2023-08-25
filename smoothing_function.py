import numpy as np

"""### Smoothing Functions
---
"""
# traditional Thompson Sampling
BASIC_THOMPSON_SAMPLING_FUNC = lambda x: x > 0

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

def genearlized_logistic_func(x):
    num = L_max - L_min
    denom = (1 + C_logistic * np.exp(-B_logistic * x))**K_logistic

    return L_min + (num / denom)
