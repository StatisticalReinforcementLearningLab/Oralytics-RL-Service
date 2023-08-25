import numpy as np

"""### Reward Definition For RL Algorithm
---
"""

def get_brushing_quality(brushing_duration, brushing_pressure):
    return brushing_duration - brushing_pressure

def process_brushing_quality(brushing_quality):
    return min(brushing_quality, 180)

# b bar is designed to be in [0, 180]
def normalize_b_bar(b_bar):
    return (b_bar - (181 / 2)) / (179 / 2)

# we need a_bar to be between -1 and 1 because for behavioral scientists to interpret
# the intercept term, all state features need to have meaning at value 0.
# unnormalized a_bar is between [0, 1]
def normalize_a_bar(a_bar):
  return 2 * (a_bar - 0.5)

""" GLOBAL VALUES """
GAMMA = 13/14
B = normalize_b_bar(111)
A_1 = normalize_a_bar(0.5)
A_2 = normalize_a_bar(0.8)
DISCOUNTED_GAMMA_ARRAY = GAMMA ** np.flip(np.arange(14))
CONSTANT = (1 - GAMMA) / (1 - GAMMA**14)
XI_1 = 100
XI_2 = 100

# brushing duration is of length 14 where the first element is the brushing duration
# at time t - 14 and the last element the brushing duration at time t - 1
def calculate_b_bar(brushing_durations):
    sum_term = DISCOUNTED_GAMMA_ARRAY * brushing_durations

    return CONSTANT * np.sum(sum_term)

def calculate_a_bar(past_actions):
    sum_term = DISCOUNTED_GAMMA_ARRAY * past_actions

    return CONSTANT * np.sum(sum_term)

def calculate_b_condition(b_bar):
    return b_bar > B

def calculate_a1_condition(a_bar):
    return a_bar > A_1

def calculate_a2_condition(a_bar):
    return a_bar > A_2

def cost_definition(xi_1, xi_2, action, B_condition, A1_condition, A2_condition):
    return action * (xi_1 * B_condition * A1_condition + xi_2 * A2_condition)

# returns the reward where the cost term is parameterized by xi_1, xi_2
def reward_definition(quality, cost):
    return quality - cost

def get_reward_components(brushing_duration, brushing_pressure, current_action, b_bar, a_bar):
    raw_quality = get_brushing_quality(brushing_duration, brushing_pressure)
    quality = process_brushing_quality(raw_quality)
    B_condition = calculate_b_condition(b_bar)
    A1_condition = calculate_a1_condition(a_bar)
    A2_condition = calculate_a2_condition(a_bar)
    cost = cost_definition(XI_1, XI_2, current_action, B_condition, A1_condition, A2_condition)
    reward_comps = {
    "brushing_duration" : brushing_duration,
    "pressure_duration" : brushing_pressure,
    "raw_quality": raw_quality,
    "quality": quality,
    "B_condition" : B_condition,
    "A1_condition" : A1_condition,
    "A2_condition" : A2_condition,
    "cost_term" : cost,
    "reward" : reward_definition(quality, cost),
    "actual_b_bar" : b_bar
    }

    return reward_comps
