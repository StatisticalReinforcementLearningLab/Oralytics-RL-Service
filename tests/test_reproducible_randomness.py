import unittest
from rl_ohrs.reproducible_randomness import *

class ReproducibleRandomness(unittest.TestCase):

    def test_randomness_is_reproducible(self):
        prob = 0.5
        for _ in range(100):
            outcome, seed = reproducible_bernoulli(prob)
            test_rng = np.random.default_rng(seed)
            outcome2 = test_rng.binomial(n=1, p=prob)
            self.assertEqual(outcome, outcome2)

if __name__ == "__main__":
    unittest.main()
