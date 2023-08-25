import numpy as np
from scipy.stats import bernoulli
from datetime import datetime, timedelta
from process_state import process_alg_state, get_a_bar, get_most_recent_data, get_and_process_states
from database.data_tables_integration import get_user_info, push_tuple_data_for_users, set_user_info, get_morning_decision_t, get_evening_decision_t, get_study_description
from schedule import construct_schedule_id
from dependencies.dependency_integration import get_user_dt_for_date
from global_vars import SCHEDULE_LENGTH_IN_DAYS, DECISION_TIMES_PER_DAY

def state_evolution(current_states, user_actions):
    # b_bar is the same for morning and evening decision times
    normalized_b_bar = current_states[0][1]
    a_bar = get_a_bar(user_actions)
    # app_engagement = 0 because this schedule will only get executed if the user
    # does not open the app
    next_morning_state = process_alg_state(0, normalized_b_bar, a_bar, 0)
    next_evening_state = process_alg_state(1, normalized_b_bar, a_bar, 0)

    return next_morning_state, next_evening_state

def impute_rest_of_schedule(user_id, schedule_id, schedule, user_day_in_study, \
                            current_alg, current_states, user_actions):
    day_in_study = int(get_study_description("day_in_study"))
    policy_idx = get_study_description("policy_idx")
    for i in range(1, SCHEDULE_LENGTH_IN_DAYS):
        current_states = state_evolution(current_states, user_actions)
        next_morning_state, next_evening_state = current_states
        morning_action, morning_prob = current_alg.action_selection(next_morning_state)
        evening_action, evening_prob = current_alg.action_selection(next_evening_state)
        schedule[i, 0] = morning_action
        schedule[i, 1] = evening_action
        user_actions = np.append(user_actions, [morning_action, evening_action])
        # record in database
        push_tuple_data_for_users(user_id, schedule_id, (2 * (user_day_in_study + i)) - 2, \
        get_user_dt_for_date(datetime.now().date() + timedelta(days=i), "morning", user_id), \
        day_in_study + i, policy_idx, next_morning_state, morning_action, morning_prob)
        push_tuple_data_for_users(user_id, schedule_id, (2 * (user_day_in_study + i)) - 1, \
        get_user_dt_for_date(datetime.now().date() + timedelta(days=i), "evening", user_id), \
        day_in_study + i, policy_idx, next_evening_state, evening_action, evening_prob)

    return schedule


def action_selection(current_alg, user_id):
    try:
        user_qualities, user_actions = get_most_recent_data(user_id)
        current_states = get_and_process_states(user_id, user_qualities, user_actions)
        user_day_in_study = get_user_info("user_day_in_study", user_id)
        schedule_id = construct_schedule_id(user_id, user_day_in_study)
        schedule = np.full((SCHEDULE_LENGTH_IN_DAYS, DECISION_TIMES_PER_DAY), np.nan)
        # first day in schedule has fresh data
        morning_adv_state, evening_adv_state = current_states
        morning_action, morning_prob = current_alg.action_selection(morning_adv_state)
        evening_action, evening_prob = current_alg.action_selection(evening_adv_state)
        schedule[0, 0] = morning_action
        schedule[0, 1] = evening_action
        # record in database
        day_in_study = get_study_description("day_in_study")
        policy_idx = get_study_description("policy_idx")
        push_tuple_data_for_users(user_id, schedule_id, get_morning_decision_t(user_day_in_study), \
        get_user_dt_for_date(datetime.now().date(), "morning", user_id), day_in_study, policy_idx, \
        morning_adv_state, morning_action, morning_prob)
        push_tuple_data_for_users(user_id, schedule_id, get_evening_decision_t(user_day_in_study), \
        get_user_dt_for_date(datetime.now().date(), "evening", user_id), day_in_study, policy_idx, \
        evening_adv_state, evening_action, evening_prob)
        # the rest of the schedule is imputed
        user_actions = np.append(user_actions, [morning_action, evening_action])
        schedule = impute_rest_of_schedule(user_id, schedule_id, schedule, user_day_in_study, \
        current_alg, current_states, user_actions)

        return schedule, schedule_id

    # ANNA TODO: need to update this after confirming with Susan!
    # should we still update batch data with fallback method data?
    except Exception as e:
        print("Action-Selection Error: ", str(e))
        print("Action-Selection Fallback Method")
        # ANNA TODO: needs logger
        fixed_prob = 0.5
        schedule = np.array([bernoulli.rvs(fixed_prob) for _ in range(14)]).reshape((SCHEDULE_LENGTH_IN_DAYS, DECISION_TIMES_PER_DAY))
        schedule_id = "fallback_method"
        # schedule_id = construct_schedule_id(user_id, user_day_in_study)
        # record in database
        for i in range(SCHEDULE_LENGTH_IN_DAYS):
            push_tuple_data_for_users(user_id, schedule_id, None, None, None, "fallback_method", np.zeros(5), schedule[i, 0], fixed_prob)
            push_tuple_data_for_users(user_id, schedule_id, None, None, None, "fallback_method", np.zeros(5), schedule[i, 1], fixed_prob)

        return schedule, schedule_id
