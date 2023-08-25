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
SIGMA_N_2 = 3396.449
PRIOR_MU = np.array([0, 4.925, 0, 0, 82.209, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
SIGMA_BETA = 29.624
PRIOR_SIGMA = np.diag(np.array([29.090**2, 30.186**2, SIGMA_BETA**2, SIGMA_BETA**2, 46.240**2, \
                                    SIGMA_BETA**2, SIGMA_BETA**2, SIGMA_BETA**2, SIGMA_BETA**2, SIGMA_BETA**2,\
                                    SIGMA_BETA**2, SIGMA_BETA**2, SIGMA_BETA**2, SIGMA_BETA**2, SIGMA_BETA**2]))

""" STUDY """
## Schedule Size ##
SCHEDULE_LENGTH_IN_DAYS = 7
DECISION_TIMES_PER_DAY = 2

# ANNA TODO: need to change this to 35 for the pilot study
STUDY_DURATION = 70

""" DATABASE """
MEAN_COLS = ["posterior_mu_{}, ".format(i) for i in range(RL_ALG_FEATURE_DIM)]
POSTERIOR_COLS = ["posterior_var_{}_{}, ".format(i, j) for i in range(RL_ALG_FEATURE_DIM) for j in range(RL_ALG_FEATURE_DIM)]
POSTERIOR_TABLE_COLS = "policy_idx, " + "timestamp," + ''.join(MEAN_COLS) + ''.join(POSTERIOR_COLS)
POSTERIOR_TABLE_COLS = POSTERIOR_TABLE_COLS[:-2]
