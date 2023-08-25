import numpy as np
from datetime import datetime
from database.data_tables_integration import (
            set_user_info,
            get_user_info,
            get_tuple_data_for_users,
            push_update_data_for_user,
            get_update_data,
            push_updated_posterior_values,
            get_current_study_users,
            get_study_description,
            push_study_description,
            get_morning_decision_t,
            get_evening_decision_t,
            get_actual_tuple_data_for_users,
            push_actual_tuple_data_for_users,
            get_tuple_data_col_val,
            push_actual_reward_data_for_users
)
from dependencies.dependency_integration import get_recent_user_data
from reward_definition import get_reward_components
from bayes_lr import update_posterior
from schedule import construct_schedule_id

def get_schedule_id(user_id):
    return get_user_info("most_recent_schedule_id", user_id)

def resolve_and_update_schedule_id(user_id, recent_data_dict):
    app_engagement_indict = recent_data_dict['app_engagement']
    previous_schedule_id = get_schedule_id(user_id)
    # if user did not open app so both morning and evening
    # then default to last saved schedule_id
    morning_schedule_id = previous_schedule_id
    evening_schedule_id = previous_schedule_id
    if app_engagement_indict:
        user_day_in_study = get_user_info("user_day_in_study", user_id)
        most_recent_schedule_id = construct_schedule_id(user_id, user_day_in_study)
        set_user_info(user_id, "most_recent_schedule_id", most_recent_schedule_id)
        if recent_data_dict["morning_used_recent_schedule"]:
            morning_schedule_id = most_recent_schedule_id
        if recent_data_dict["evening_used_recent_schedule"]:
            evening_schedule_id = most_recent_schedule_id

    return morning_schedule_id, evening_schedule_id

# gets the correct row given the schedule_id
# saves the correct row to the action selection data table
def get_and_push_actual_row(user_id, schedule_id, decision_t):
    vals = get_tuple_data_for_users(user_id, schedule_id, decision_t)
    push_actual_tuple_data_for_users(vals)

# get row from action selection table
# then impute values to prepare for pushing to update data table
# return row of the form:
# [0] action [1] prob [2] reward [3] brushing quality
# [4] state_tod [5] state_b_bar [6] state_a_bar [7] state_app_engage
# [8] state_bias
def get_row_for_batch_data_update(user_id, decision_t, actual_schedule_id, \
                                    brushing_duration, brushing_pressure):
    user_dt_info, data_dict = get_actual_tuple_data_for_users(user_id, decision_t)
    if data_dict:
        row = list(data_dict.values())
        # impute b_bar with actual observed b_bar: the same b_bar as the one used for the morning of the same day
        actual_b_bar = get_tuple_data_col_val('state_b_bar', user_id, \
                                            actual_schedule_id, \
                                            decision_t)
        actual_b_bar = actual_b_bar if actual_b_bar else 0
        # impute actual_app_engagement
        actual_app_engagement = get_tuple_data_col_val('state_app_engage', user_id, \
                                            actual_schedule_id, \
                                            decision_t)
        # need to get reward components
        reward_comps = get_reward_components(brushing_duration, brushing_pressure, \
                                            data_dict['action'], actual_b_bar, data_dict['state_a_bar'])
        # update action selection data table with reward components
        push_actual_reward_data_for_users(user_id, decision_t, reward_comps)
        # need to add space for reward and quality
        row = row[:2] + [reward_comps["reward"], reward_comps["quality"]] + row[2:]
        row[5] = actual_b_bar
        row[7] = actual_app_engagement

        return user_dt_info, row
    else:
        return None, None

# should be called at the beginning of everyday
def update_study_info():
    push_study_description("calendar_decision_t", int(get_study_description("calendar_decision_t")) + 2)
    push_study_description("day_in_study", int(get_study_description("day_in_study")) + 1)
    push_study_description("time_updated_day_in_study", datetime.now())

def update_recent_data():
    current_users_list = get_current_study_users()
    for user_id in current_users_list:
        # grab most recent context
        try:
            recent_data_dict = get_recent_user_data(user_id)
            user_day_in_study = int(get_user_info("user_day_in_study", user_id))
            morning_schedule_id, evening_schedule_id = resolve_and_update_schedule_id(user_id, recent_data_dict)
            # push correct recent_morning data row to action selection data table
            get_and_push_actual_row(user_id, morning_schedule_id, get_morning_decision_t(user_day_in_study))
            # push correct recent_evening data row to action selection data table
            get_and_push_actual_row(user_id, evening_schedule_id, get_evening_decision_t(user_day_in_study))
            # should only get and push previous evening row after user_day_in_study=2
            previous_evening_dt_info, previous_evening_row = get_row_for_batch_data_update(user_id, get_evening_decision_t(user_day_in_study - 1), \
                                            construct_schedule_id(user_id, user_day_in_study - 1), \
                                            recent_data_dict["previous_evening_duration"], recent_data_dict["previous_evening_pressure"])
            recent_morning_dt_info, recent_morning_row = get_row_for_batch_data_update(user_id, get_morning_decision_t(user_day_in_study), \
                                    construct_schedule_id(user_id, user_day_in_study), \
                                    recent_data_dict["recent_morning_duration"], recent_data_dict["recent_morning_pressure"])
            # push previous_evening_row and recent_morning_row to update data table
            if previous_evening_row:
                push_update_data_for_user(user_id, previous_evening_dt_info, previous_evening_row)
            if recent_morning_row:
                push_update_data_for_user(user_id, recent_morning_dt_info, recent_morning_row)
            # this is needed for the app engagement state feature during action selection
            set_user_info(user_id, "user_opened_app", recent_data_dict["app_engagement"])

        except Exception as e:
            print("Error updating batch data for user {}".format(user_id))
            print(str(e))
            # ANNA TODO: needs logger
            continue

def use_data_update_posterior():
    try:
        # pull update data table data
        alg_states, actions, pis, rewards = get_update_data()
        # update parameters
        posterior_mean, posterior_var = update_posterior(alg_states, actions, pis, rewards)
        # push parameters to internal data storage
        push_updated_posterior_values(posterior_mean, posterior_var)

    except Exception as e:
        print("Could not update posterior.")
        print(str(e))
