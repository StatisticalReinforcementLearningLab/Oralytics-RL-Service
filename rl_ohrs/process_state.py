import numpy as np
from rl_ohrs.reward_definition import calculate_b_bar, calculate_a_bar, normalize_b_bar, normalize_a_bar
from rl_ohrs.database.data_tables_integration import get_user_info, get_user_data

""" PROCESS STATE """
## baseline: ##
# 0 - time of day
# 1 - b bar
# 2 - a bar
# 3 - app engagement
# 4 - bias
## advantage: ##
# 0 - time of day
# 1 - b bar
# 2 - a bar
# 3 - app engagement
# 4 - bias
def process_alg_state(time_of_day, normalized_b_bar, a_bar, app_engagement):
    state = np.array([time_of_day, \
                    normalized_b_bar, \
                    a_bar, \
                    app_engagement, 1])

    return state

def get_most_recent_qualities(user_id):
    return get_user_data("quality", user_id)

def get_most_recent_actions(user_id):
    return get_user_data("action", user_id)

def get_b_bar(user_qualities):
    j = len(user_qualities)
    if j < 14:
        b_bar = 0 if len(user_qualities) == 0 else np.mean(user_qualities)
    else:
        b_bar = calculate_b_bar(user_qualities[-14:])

    return b_bar

def get_a_bar(user_actions):
    j = len(user_actions)
    if j < 14:
        a_bar = 0 if len(user_actions) == 0 else np.mean(user_actions)
    else:
        a_bar = calculate_a_bar(user_actions[-14:])

    return a_bar

# j is user-specific decision time
# user_qualities and user_actions should be numpy arrays of the same size
def get_b_bar_a_bar(user_qualities, user_actions):
    # if first week for user, we impute A bar and B bar
    b_bar = get_b_bar(user_qualities)
    a_bar = get_a_bar(user_actions)

    return b_bar, a_bar

def get_most_recent_data(user_id):
    return get_most_recent_qualities(user_id), get_most_recent_actions(user_id)

# gets the current morning and evening state for today
def get_and_process_states(user_id, user_qualities, user_actions):
    # calculate current state
    b_bar, a_bar = get_b_bar_a_bar(user_qualities, \
                                    user_actions)
    app_engagement = get_user_info("user_opened_app", user_id)
    morning_state = process_alg_state(0, normalize_b_bar(b_bar), normalize_a_bar(a_bar), app_engagement)
    evening_state = process_alg_state(1, normalize_b_bar(b_bar), normalize_a_bar(a_bar), app_engagement)

    return morning_state, evening_state
