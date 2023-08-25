import numpy as np
from rl_ohrs.reproducible_randomness import reproducible_bernoulli
import scipy.stats as stats

from rl_ohrs.reward_definition import *
from rl_ohrs.smoothing_function import genearlized_logistic_func
from rl_ohrs.database.data_tables_integration import get_posterior_values
from rl_ohrs.global_vars import (
            D_ADVANTAGE,
            D_BASELINE,
            SIGMA_N_2,
            PRIOR_MU,
            PRIOR_SIGMA
)

"""### Bayesian Linear Regression Thompson Sampler
---
RL Algorithm that uses a contextual bandit framework with Thompson sampling, full-pooling, and
a Bayesian Linear Regression reward approximating function with action centering.
"""

""" POSTERIOR HELPERS """
# create the feature vector given state, action, and action selection probability with action centering
def create_big_phi(advantage_states, baseline_states, actions, probs):
  big_phi = np.hstack((baseline_states, np.multiply(advantage_states.T, probs).T, \
                       np.multiply(advantage_states.T, (actions - probs)).T,))
  return big_phi

def compute_posterior_var(Phi):
  return np.linalg.inv(1/SIGMA_N_2 * Phi.T @ Phi + np.linalg.inv(PRIOR_SIGMA))

def compute_posterior_mean(Phi, R):
  return compute_posterior_var(Phi) \
   @ (1/SIGMA_N_2 * Phi.T @ R + np.linalg.inv(PRIOR_SIGMA) @ PRIOR_MU)

# update posterior distribution
def update_posterior_w(Phi, R):
  mean = compute_posterior_mean(Phi, R)
  var = compute_posterior_var(Phi)

  return mean, var

""" ACTION SELECTION """
# we calculate the posterior probability of P(R_1 > R_0) clipped
# we make a Bernoulli draw with prob. P(R_1 > R_0) of the action
def bayes_lr_action_selector(beta_post_mean, beta_post_var, advantage_state):
  # using the genearlized_logistic_func, probabilities are already clipped to asymptotes
  mu = advantage_state @ beta_post_mean
  std = np.sqrt(advantage_state @ beta_post_var @ advantage_state.T)
  posterior_prob = stats.norm.expect(func=genearlized_logistic_func, loc=mu, scale=std)
  action, seed = reproducible_bernoulli(posterior_prob)

  return action, posterior_prob, seed

# creating the BLR object will automatically grab the most recent parameters
class BayesianLinearRegression():
    def __init__(self):
        policy_idx, mean, var = get_posterior_values()
        self.posterior_mean = mean
        self.posterior_var = var

    def action_selection(self, advantage_state):
        return bayes_lr_action_selector(self.posterior_mean[-D_ADVANTAGE:], \
                                        self.posterior_var[-D_ADVANTAGE:,-D_ADVANTAGE:], \
                                        advantage_state)

""" UPDATE """

def update_posterior(alg_states, actions, pis, rewards):
    Phi = create_big_phi(alg_states, alg_states, actions, pis)
    posterior_mean, posterior_var = update_posterior_w(Phi, rewards)

    return posterior_mean, posterior_var
