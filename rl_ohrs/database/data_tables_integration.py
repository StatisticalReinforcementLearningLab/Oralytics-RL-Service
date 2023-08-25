import numpy as np
import pandas as pd
from datetime import datetime

from rl_ohrs.database.database_connector import MYDB
from rl_ohrs.database.helpers import *
from rl_ohrs.global_vars import RL_ALG_FEATURE_DIM, POSTERIOR_TABLE_COLS

### S, A, R Columns ###
SAR_COLUMN_NAMES = ["action", "prob", "reward", "quality", "state_tod", \
                     "state_b_bar", "state_a_bar", "state_app_engage", "state_bias"]
SA_COLUMN_NAMES = ["action", "prob", "state_tod", "state_b_bar", \
                    "state_a_bar", "state_app_engage", "state_bias"]
USER_START_DAY_DEFAULT = datetime.strptime("0001-01-01", '%Y-%m-%d').date()

### HELPERS ###
def get_db():
    return MYDB

# Solving the mysql connection issue:
# https://stackoverflow.com/questions/27537892/cursor-raise-errors-operationalerrormysql-connection-not-available-operat
def execute_pull(command_string):
    DB = get_db()
    DB.reconnect()
    MYCURSOR = DB.cursor()
    MYCURSOR.execute(command_string)
    pull_result = MYCURSOR.fetchall()

    return pull_result

def execute_push(command_string):
    DB = get_db()
    DB.reconnect()
    MYCURSOR = DB.cursor()
    MYCURSOR.execute(command_string)
    DB.commit()

def get_morning_decision_t(user_day_in_study):
    return (2 * user_day_in_study) - 2

def get_evening_decision_t(user_day_in_study):
    return (2 * user_day_in_study) - 1

def array_to_row_dict(col_names, row_array):
    return dict(zip(col_names, row_array))

def get_user_start_and_end_date(user_id):
    user_start_day = get_user_info("user_start_day", user_id)
    user_end_day = get_user_info("user_end_day", user_id)

    return user_start_day, user_end_day

## Helper functions for filtering by date
def get_date(date_string):
    return datetime.strptime(date_string, '%Y-%m-%d')

"""
Pull Data
"""
# returns either 0 if user_id is not in the tables or 1 otherwise
def check_user_registered(user_id):
    value = "SELECT * FROM user_info_table WHERE user_id='{}'".format(user_id)
    command_string = "SELECT EXISTS({})".format(value)
    result = execute_pull(command_string)[0][0]

    return result

def user_not_in_study(user_id):
    return get_user_info("user_start_day", user_id) == USER_START_DAY_DEFAULT

def get_user_info(col_name, user_id):
    command_string = "SELECT {} FROM user_info_table WHERE user_id='{}'".format(col_name, user_id)
    result = execute_pull(command_string)[0][0]

    return result

# Note: will return empty array or list if there's no data on the user
def get_user_data(col_name, user_id):
    command_string = "SELECT {} FROM update_data_table WHERE user_id='{}'".format(col_name, user_id)
    result = execute_pull(command_string)

    return format_float_result(result)

# Note: we need to keep col_names as an argument in case someone wants to get column values such as reward comps
def get_actual_tuple_data_for_users(user_id, user_decision_t, col_names=SA_COLUMN_NAMES):
    command_template = "SELECT {} FROM action_selection_data_table WHERE user_id='{}' AND user_decision_t='{}'"
    command_string = command_template.format(list_to_columns(col_names), user_id, user_decision_t)
    result = execute_pull(command_string)
    row = format_float_result(result)
    # edge case for init: if there is no action selection tuple data for user_decision_t then return None, None
    if len(row) == 0:
        return None, None
    # get additional info to push to update data table:
    # user_start_day, user_end_day, user_decision_t, decision_time
    user_dt_col_names = ["user_start_day", "user_end_day", "user_decision_t", "decision_time"]
    command_string = command_template.format(list_to_columns(user_dt_col_names), user_id, user_decision_t)
    user_dt_row = execute_pull(command_string)[0]

    return array_to_row_dict(user_dt_col_names, user_dt_row), array_to_row_dict(col_names, row)

def get_tuple_data_for_users(user_id, schedule_id, user_decision_t):
    command_template = "SELECT * FROM user_data_table WHERE user_id='{}' AND user_decision_t='{}' AND schedule_id='{}'"
    command_string = command_template.format(user_id, user_decision_t, schedule_id)
    # if there are multiple rows, then should return the last added one
    # this is important because the action for that decision time could change if /decision/all endpoint was called multiple times
    result = list(execute_pull(command_string)[-1])

    return result

def get_tuple_data_col_val(col_name, user_id, schedule_id, user_decision_t):
    command_template = "SELECT {} FROM user_data_table WHERE user_id='{}' AND user_decision_t='{}' AND schedule_id='{}'"
    command_string = command_template.format(col_name, user_id, user_decision_t, schedule_id)
    result = execute_pull(command_string)[0][0]

    return result

# gets study description data such as:
# policy_idx
def get_study_description(col_name):
    command_string = "SELECT {} FROM policy_info_table".format(col_name)
    result = execute_pull(command_string)[0][0]

    return result

def get_update_data():
    command_string = "SELECT {} FROM update_data_table".format(list_to_columns(SAR_COLUMN_NAMES))
    results = execute_pull(command_string)
    results = format_batch_data_result(results)
    if len(results) == 0:
        return None, None, None, None
    alg_states = results[:,4:]
    actions = results[:, 0]
    pis = results[:, 1]
    rewards = results[:, 2]

    return alg_states, actions, pis, rewards

# used for decision times
def get_posterior_values():
    print("GETTING POSTERIOR VALUES")
    policy_idx = get_study_description("policy_idx")
    command_string = "SELECT * FROM posterior_weights_table WHERE policy_idx={}".format(policy_idx)
    results = execute_pull(command_string)
    # [2:] removes the policy_idx and the timestamp
    D = format_float_result([results[0][2:]])
    # 'restore' the original dimensions of the result set:
    mean = D[:RL_ALG_FEATURE_DIM]
    var = D[RL_ALG_FEATURE_DIM:].reshape(RL_ALG_FEATURE_DIM, RL_ALG_FEATURE_DIM)

    return policy_idx, mean, var

"""
Push Data
"""
def push_registered_user(user_id):
    command_string = "INSERT INTO user_info_table (user_id) VALUES ('{}')".format(user_id)
    execute_push(command_string)

def set_user_info(user_id, col_name, col_val):
    command_string = "UPDATE user_info_table SET {}='{}' WHERE user_id='{}'".format(col_name, col_val, user_id)
    execute_push(command_string)

def push_study_description(col_name, col_val):
    command_string = "UPDATE policy_info_table SET {}='{}'".format(col_name, col_val)
    execute_push(command_string)

def push_actual_tuple_data_for_users(vals):
    column_names = ["user_id", "user_start_day", "user_end_day", "timestamp", "schedule_id", \
                    "user_decision_t", "decision_time", "day_in_study", "policy_idx", "random_seed", "action", "prob", \
                    "state_tod", "state_b_bar", "state_a_bar", "state_app_engage", "state_bias"]
    command_template = "INSERT INTO action_selection_data_table ({}) VALUES ({})"
    command_string = command_template.format(list_to_columns(column_names), list_to_vals(vals))
    execute_push(command_string)

# ref: https://ubiq.co/database-blog/how-to-update-multiple-columns-in-mysql/
# reward_comps keys: ["brushing_duration", "pressure_duration", "quality", "raw_quality", "reward", \
#                 "cost_term", "B_condition", "A1_condition", "A2_condition", "actual_b_bar"]
def push_actual_reward_data_for_users(user_id, decision_t, reward_comps):
    command_template = "UPDATE action_selection_data_table SET {} WHERE user_id='{}' AND user_decision_t='{}'"
    key_value_pairs = set_multiple_values_from_dict(reward_comps)
    command_string = command_template.format(key_value_pairs, user_id, decision_t)
    execute_push(command_string)

def push_tuple_data_for_users(user_id, schedule_id, decision_t, decision_time, \
                    day_in_study, policy_idx, state, random_seed, action, action_prob):
    column_names = ["user_id", "user_start_day", "user_end_day", "timestamp", "schedule_id", \
                    "user_decision_t", "decision_time", "day_in_study", "policy_idx", "random_seed", "action", "prob", \
                    "state_tod", "state_b_bar", "state_a_bar", "state_app_engage", "state_bias"]
    user_start_day, user_end_day = get_user_start_and_end_date(user_id)
    vals = [user_id, user_start_day, user_end_day, datetime.now(), schedule_id, \
            decision_t, decision_time, day_in_study, policy_idx, random_seed, action, action_prob, \
            state[0], state[1], state[2], state[3], state[4]]
    command_template = "INSERT INTO user_data_table ({}) VALUES ({})"
    command_string = command_template.format(list_to_columns(column_names), list_to_vals(vals))
    execute_push(command_string)

def push_update_data_for_user(user_id, user_dt_info, row):
    column_names = ["user_id", "user_start_day", "user_end_day", "timestamp", \
                    "decision_time", "user_decision_t", "first_policy_idx", \
                    "action", "prob", "reward", "quality", "state_tod", \
                    "state_b_bar", "state_a_bar", "state_app_engage", "state_bias"]
    user_info_vals = [user_id, user_dt_info["user_start_day"], user_dt_info["user_end_day"], datetime.now()]
    first_policy_idx = get_study_description("policy_idx") + 1
    decision_t_vals = [user_dt_info["decision_time"], user_dt_info["user_decision_t"], first_policy_idx]
    # update with actually observed tuple
    command_template = "INSERT INTO update_data_table ({}) VALUES ({})"
    row_vals = list_to_vals(user_info_vals + decision_t_vals + row)
    command_string = command_template.format(list_to_columns(column_names), row_vals)
    execute_push(command_string)

# push updated posterior parameters
def push_updated_posterior_values(posterior_mu, posterior_var):
    policy_idx = get_study_description("policy_idx") + 1
    push_study_description("policy_idx", policy_idx)
    current_datetime = datetime.now()
    push_study_description("time_updated_policy", current_datetime)
    posterior_vals = list(np.concatenate([posterior_mu, posterior_var.flatten()]))
    vals = list_to_vals([policy_idx, str(current_datetime)] + posterior_vals)
    command_string = "INSERT INTO posterior_weights_table ({}) VALUES ({})".format(POSTERIOR_TABLE_COLS, vals)
    execute_push(command_string)

"""
Integration With Clinician Dashboard
"""

def get_entire_data_table(data_table_name):
    query = "SELECT * FROM {};".format(data_table_name)
    DB = get_db()
    DB.reconnect()
    df = pd.read_sql(query, DB)

    return df.to_json(date_format='iso')

def get_data_table_from_timestamp(data_table_name, start_date, end_date):
    start_date = get_date(start_date)
    end_date = get_date(end_date)
    query = "SELECT * FROM {} WHERE timestamp > '{}' AND timestamp < '{}'".format(data_table_name, start_date, end_date)
    DB = get_db()
    DB.reconnect()
    df = pd.read_sql(query, DB)

    return df.to_json(date_format='iso')
