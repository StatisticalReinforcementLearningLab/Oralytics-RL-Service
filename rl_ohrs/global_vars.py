import numpy as np

"""
GLOBAL VALUES
"""

""" ALGORITHM """
# Advantage Time Feature Dimensions
D_ADVANTAGE = 5
# Baseline Time Feature Dimensions
D_BASELINE = 5
# Total Feature Dimension
RL_ALG_FEATURE_DIM = D_BASELINE + D_ADVANTAGE + D_ADVANTAGE
### PRIOR VALUES ###
SIGMA_N_2 = 3878
ALPHA_0_MU = [18, 0, 30, 0, 73]
BETA_MU = [0, 0, 0, 53, 0]
PRIOR_MU = np.array(ALPHA_0_MU + BETA_MU + BETA_MU)
ALPHA_0_SIGMA = [73**2, 25**2, 95**2, 27**2, 83**2]
BETA_SIGMA = [12**2, 33**2, 35**2, 56**2, 17**2]
PRIOR_SIGMA = np.diag(np.array(ALPHA_0_SIGMA + BETA_SIGMA + BETA_SIGMA))


""" STUDY """
## Schedule Size ##
SCHEDULE_LENGTH_IN_DAYS = 70
DECISION_TIMES_PER_DAY = 2
STUDY_DURATION = 70
STUDY_START_DATE = ""

""" DATABASE """
MEAN_COLS = ["posterior_mu_{}, ".format(i) for i in range(RL_ALG_FEATURE_DIM)]
POSTERIOR_COLS = ["posterior_var_{}_{}, ".format(i, j) for i in range(RL_ALG_FEATURE_DIM) for j in range(RL_ALG_FEATURE_DIM)]
POSTERIOR_TABLE_COLS = "policy_idx, " + "timestamp," + ''.join(MEAN_COLS) + ''.join(POSTERIOR_COLS)
POSTERIOR_TABLE_COLS = POSTERIOR_TABLE_COLS[:-2]
