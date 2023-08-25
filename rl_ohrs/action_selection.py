import numpy as np
from datetime import datetime, timedelta
import traceback

from rl_ohrs.process_state import process_alg_state, get_a_bar, get_most_recent_data, get_and_process_states
from rl_ohrs.database.data_tables_integration import push_tuple_data_for_users, get_morning_decision_t, get_evening_decision_t, get_study_description
from rl_ohrs.day_in_study import get_study_level_day_in_study, get_user_day_in_study
from rl_ohrs.schedule import construct_schedule_id
from rl_ohrs.dependencies.dependency_integration import get_user_dt_for_date
from rl_ohrs.reproducible_randomness import reproducible_bernoulli
from rl_ohrs.global_vars import SCHEDULE_LENGTH_IN_DAYS, DECISION_TIMES_PER_DAY
from rl_ohrs.rl_email import exception_handler

FIXED_RANDOMIZATION_PROB = 0.5

def state_evolution(current_states, user_actions):
    # b_bar is the same for morning and evening decision times
    normalized_b_bar = current_states[0][1]
    # when calculating a_bar we only have access to the most recent morning dt
    # so we don't include the action for the evening dt, even if we know it
    a_bar = get_a_bar(user_actions[:-1])
    # app_engagement = 0 because this schedule will only get executed if the user
    # does not open the app
    next_morning_state = process_alg_state(0, normalized_b_bar, a_bar, 0)
    next_evening_state = process_alg_state(1, normalized_b_bar, a_bar, 0)

    return next_morning_state, next_evening_state

def impute_rest_of_schedule(user_id, schedule_id, schedule, user_day_in_study, \
                            current_alg, current_states, user_actions):
    day_in_study = get_study_level_day_in_study()
    current_policy_idx = get_study_description("policy_idx")
    for i in range(1, SCHEDULE_LENGTH_IN_DAYS):
        # if within a week, use state imputation procedure
        if i < 7:
            policy_idx = current_policy_idx
            current_states = state_evolution(current_states, user_actions)
            next_morning_state, next_evening_state = current_states
            morning_action, morning_prob, morning_seed = current_alg.action_selection(next_morning_state)
            evening_action, evening_prob, evening_seed = current_alg.action_selection(next_evening_state)
            user_actions = np.append(user_actions, [morning_action, evening_action])
        # if past a week, then select action with probability 0.5
        else:
            # indicates fixed probability randomization
            policy_idx = -1
            morning_prob, evening_prob = FIXED_RANDOMIZATION_PROB, FIXED_RANDOMIZATION_PROB
            morning_action, morning_seed = reproducible_bernoulli(morning_prob)
            evening_action, evening_seed = reproducible_bernoulli(evening_prob)
            # no state was used for action-selection
            next_morning_state = np.zeros(5)
            next_evening_state = np.zeros(5)

        schedule[i, 0] = morning_action
        schedule[i, 1] = evening_action
        # record in database
        push_tuple_data_for_users(user_id, schedule_id, (2 * (user_day_in_study + i)) - 2, \
        get_user_dt_for_date(datetime.now().date() + timedelta(days=i), "morning", user_id), \
        day_in_study + i, policy_idx, next_morning_state, morning_seed, morning_action, morning_prob)
        push_tuple_data_for_users(user_id, schedule_id, (2 * (user_day_in_study + i)) - 1, \
        get_user_dt_for_date(datetime.now().date() + timedelta(days=i), "evening", user_id), \
        day_in_study + i, policy_idx, next_evening_state, evening_seed, evening_action, evening_prob)

    return schedule


def action_selection(current_alg, user_id):
    try:
        user_qualities, user_actions = get_most_recent_data(user_id)
        current_states = get_and_process_states(user_id, user_qualities, user_actions)
        user_day_in_study = get_user_day_in_study(user_id)
        schedule_id = construct_schedule_id(user_id, user_day_in_study)
        schedule = np.full((SCHEDULE_LENGTH_IN_DAYS, DECISION_TIMES_PER_DAY), np.nan)
        # first day in schedule has fresh data
        morning_adv_state, evening_adv_state = current_states
        morning_action, morning_prob, morning_seed = current_alg.action_selection(morning_adv_state)
        evening_action, evening_prob, evening_seed = current_alg.action_selection(evening_adv_state)
        schedule[0, 0] = morning_action
        schedule[0, 1] = evening_action
        # record in database
        day_in_study = get_study_level_day_in_study()
        policy_idx = get_study_description("policy_idx")
        push_tuple_data_for_users(user_id, schedule_id, get_morning_decision_t(user_day_in_study), \
        get_user_dt_for_date(datetime.now().date(), "morning", user_id), day_in_study, policy_idx, \
        morning_adv_state, morning_seed, morning_action, morning_prob)
        push_tuple_data_for_users(user_id, schedule_id, get_evening_decision_t(user_day_in_study), \
        get_user_dt_for_date(datetime.now().date(), "evening", user_id), day_in_study, policy_idx, \
        evening_adv_state, evening_seed, evening_action, evening_prob)
        # the rest of the schedule is imputed
        user_actions = np.append(user_actions, [morning_action, evening_action])
        schedule = impute_rest_of_schedule(user_id, schedule_id, schedule, user_day_in_study, \
        current_alg, current_states, user_actions)

        return schedule, schedule_id

    except Exception as e:
        print("Action-Selection Error: ", str(e))
        exception_handler([user_id], "fallback", traceback.format_exc())
        schedule = np.zeros(shape=(SCHEDULE_LENGTH_IN_DAYS, DECISION_TIMES_PER_DAY))
        schedule_id = "fallback_method"
        # record in database
        for i in range(SCHEDULE_LENGTH_IN_DAYS):
            morning_action, morning_seed = reproducible_bernoulli(FIXED_RANDOMIZATION_PROB)
            evening_action, evening_seed = reproducible_bernoulli(FIXED_RANDOMIZATION_PROB)
            schedule[i, 0] = morning_action
            schedule[i, 1] = evening_action
            push_tuple_data_for_users(user_id, schedule_id, None, None, None, "fallback_method", np.zeros(5), morning_seed, morning_action, FIXED_RANDOMIZATION_PROB)
            push_tuple_data_for_users(user_id, schedule_id, None, None, None, "fallback_method", np.zeros(5), evening_seed, evening_action, FIXED_RANDOMIZATION_PROB)

        return schedule, schedule_id
