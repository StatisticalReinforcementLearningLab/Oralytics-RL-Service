import numpy as np

def reproducible_bernoulli(prob):
    seed = np.random.randint(1000)
    rng = np.random.default_rng(seed)
    outcome = rng.binomial(n=1, p=prob)

    return outcome, seed
