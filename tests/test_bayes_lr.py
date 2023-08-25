import unittest
from unittest.mock import patch
import numpy as np

from rl_ohrs.smoothing_function import genearlized_logistic_func
from rl_ohrs.global_vars import (
            D_ADVANTAGE,
            D_BASELINE
)
from rl_ohrs.bayes_lr import *

THETA_DIM = D_BASELINE + 2 * D_ADVANTAGE
GENERALIZED_LOGISTIC_FUNC = lambda x: np.apply_along_axis(genearlized_logistic_func, 0, x)
NUM_POSTERIOR_SAMPLES = 5000

def get_beta_posterior_draws(posterior_mean, posterior_var):
  # grab last D_ADVANTAGE of mean vector
  beta_post_mean = posterior_mean[-D_ADVANTAGE:]
  # grab right bottom corner D_ADVANTAGE x D_ADVANTAGE submatrix
  beta_post_var = posterior_var[-D_ADVANTAGE:,-D_ADVANTAGE:]

  return np.random.multivariate_normal(beta_post_mean, beta_post_var, NUM_POSTERIOR_SAMPLES)

class BayesianLinearRegressionTest(unittest.TestCase):

    def test_closed_form_prob_calculation(self):
        advantage_state = np.array([1, 1.2, 0.8, 0, 1])
        beta_post_mean = np.ones(D_ADVANTAGE)
        beta_post_var = 2 * np.diag(np.ones(D_ADVANTAGE))
        # closed form prob
        _, posterior_prob, _ = bayes_lr_action_selector(beta_post_mean, beta_post_var, advantage_state)

        # sampled prob
        beta_posterior_draws = get_beta_posterior_draws(beta_post_mean, beta_post_var)
        sampled_prob = np.mean(GENERALIZED_LOGISTIC_FUNC(beta_posterior_draws @ advantage_state))

        print("POSTERIOR PROB", posterior_prob)
        print("SAMPLED PROB:", sampled_prob)
        np.testing.assert_almost_equal(posterior_prob, sampled_prob, decimal=2)

    @patch("rl_ohrs.bayes_lr.get_posterior_values", return_value = (0, np.zeros(THETA_DIM), np.diag(np.ones(THETA_DIM))))
    def test_instantiation_and_action_selection(self, get_posterior_values):
        blr = BayesianLinearRegression()
        advantage_state = np.array([1, 1.2, 0.8, 0, 1])
        for _ in range(100):
            action, prob, seed = blr.action_selection(advantage_state)
            test_rng = np.random.default_rng(seed)
            outcome = test_rng.binomial(n=1, p=prob)
            self.assertEqual(action, outcome)

    def test_update_posterior_w(self):
        # ground truth values
        np.random.seed(1)
        N = 2
        true_alpha_0 = np.array([0.1, 0.1, 0.1, 0.1, 100])
        # alpha_1 and beta should be the same value
        true_alpha_1 = np.array([0.2, 0.2, 0.2, 0.2, 20])
        true_beta = np.copy(true_alpha_1)
        true_theta = np.concatenate([true_alpha_0, true_alpha_1, true_beta])
        baseline_states = np.hstack((np.array([np.random.randn(4) for _ in range(N)]), np.ones(N).reshape(-1, 1)))
        baseline_states = np.vstack((baseline_states, baseline_states))
        advantage_states = np.hstack((np.array([np.random.randn(4) for _ in range(N)]), np.ones(N).reshape(-1, 1)))
        advantage_states = np.vstack((advantage_states, advantage_states))
        actions = np.hstack((np.zeros(N), np.ones(N)))
        true_phi = create_big_phi(advantage_states, baseline_states, actions, 1.0 * np.ones(2 * N))
        # print("TRUE PHI", true_phi)
        true_rewards = (baseline_states @ true_alpha_0) + actions * (advantage_states @ true_beta) #+ np.random.randn(2 * N)

        posterior_mean, posterior_var = update_posterior_w(true_phi, true_rewards)
        # np.testing.assert_almost_equal(posterior_mean, true_theta, decimal=2)

if __name__ == "__main__":
    unittest.main()
