import numpy as np
import pandas as pd
from datetime import datetime

from database_connector import MYDB
from helpers import *

RL_ALG_FEATURE_DIM = 15

MEAN_COLS = ["posterior_mu_{}, ".format(i) for i in range(RL_ALG_FEATURE_DIM)]
POSTERIOR_COLS = ["posterior_var_{}_{}, ".format(i, j) for i in range(RL_ALG_FEATURE_DIM) for j in range(RL_ALG_FEATURE_DIM)]
POSTERIOR_TABLE_COLS = "policy_idx, " + "timestamp," + ''.join(MEAN_COLS) + ''.join(POSTERIOR_COLS)
POSTERIOR_TABLE_COLS = POSTERIOR_TABLE_COLS[:-2]

ALPHA_0_MU = [18, 0, 30, 0, 73]
BETA_MU = [0, 0, 0, 53, 0]
PRIOR_MU = np.array(ALPHA_0_MU + BETA_MU + BETA_MU)
ALPHA_0_SIGMA = [73**2, 25**2, 95**2, 27**2, 83**2]
BETA_SIGMA = [12**2, 33**2, 35**2, 56**2, 17**2]
PRIOR_SIGMA = np.diag(np.array(ALPHA_0_SIGMA + BETA_SIGMA + BETA_SIGMA))

mycursor = MYDB.cursor()

def init_user_info_table():
    try:
        command_string = """CREATE TABLE user_info_table (
                                                            user_id varchar(255),
                                                            user_start_day DATE,
                                                            user_end_day DATE,
                                                            morning_time_weekday varchar(255),
                                                            evening_time_weekday varchar(255),
                                                            morning_time_weekend varchar(255),
                                                            evening_time_weekend varchar(255),
                                                            user_entry_decision_t int,
                                                            user_last_decision_t int,
                                                            currently_in_study int,
                                                            user_day_in_study int,
                                                            user_opened_app int,
                                                            most_recent_schedule_id varchar(255)
                                                            )"""
        mycursor.execute(command_string)
    except Exception as e:
        print(str(e))


"""
Create algorithm policy information table
"""
def init_policy_info_table():
    try:
        command_string = """CREATE TABLE policy_info_table (
                                                            time_updated_policy DATETIME,
                                                            policy_idx int
                                                            )"""
        mycursor.execute(command_string)

        # inputting values
        vals = list_to_vals([str(datetime.now()), 0])
        sql_command = "INSERT INTO policy_info_table (time_updated_policy, policy_idx) VALUES ({})".format(vals)
        mycursor.execute(sql_command)
        MYDB.commit()
    except Exception as e:
        print(str(e))

"""
Create action selection data table
"""
def create_action_selection_data_table():
    try:
        command_string = """CREATE TABLE action_selection_data_table (
                                                        user_id varchar(255),
                                                        user_start_day DATE,
                                                        user_end_day DATE,
                                                        timestamp DATETIME,
                                                        schedule_id varchar(255),
                                                        user_decision_t int,
                                                        decision_time DATETIME,
                                                        day_in_study int,
                                                        policy_idx int,
                                                        random_seed int,
                                                        action int,
                                                        prob double,
                                                        state_tod int,
                                                        state_b_bar double,
                                                        state_a_bar double,
                                                        state_app_engage int,
                                                        state_bias int,
                                                        brushing_duration int,
                                                        pressure_duration int,
                                                        quality int,
                                                        raw_quality int,
                                                        reward double,
                                                        cost_term double,
                                                        B_condition BOOL,
                                                        A1_condition BOOL,
                                                        A2_condition BOOL,
                                                        actual_b_bar double
                                                        )"""
        mycursor.execute(command_string)
    except Exception as e:
        print(str(e))

"""
Create user data table
"""
def create_user_data_table():
    try:
        command_string = """CREATE TABLE user_data_table (
                                                        user_id varchar(255),
                                                        user_start_day DATE,
                                                        user_end_day DATE,
                                                        timestamp DATETIME,
                                                        schedule_id varchar(255),
                                                        user_decision_t int,
                                                        decision_time DATETIME,
                                                        day_in_study int,
                                                        policy_idx int,
                                                        random_seed int,
                                                        action int,
                                                        prob double,
                                                        state_tod int,
                                                        state_b_bar double,
                                                        state_a_bar double,
                                                        state_app_engage int,
                                                        state_bias int
                                                        )"""
        mycursor.execute(command_string)
    except Exception as e:
        print(str(e))

"""
Create data used by the RL algorithm to update table
"""
def create_update_data_table():
    try:
        command_string = """CREATE TABLE update_data_table (
                                                        user_id varchar(255),
                                                        user_start_day DATE,
                                                        user_end_day DATE,
                                                        timestamp DATETIME,
                                                        decision_time DATETIME,
                                                        user_decision_t int,
                                                        first_policy_idx int,
                                                        action int,
                                                        prob double,
                                                        reward double,
                                                        quality int,
                                                        state_tod int,
                                                        state_b_bar double,
                                                        state_a_bar double,
                                                        state_app_engage int,
                                                        state_bias int
                                                        )"""
        mycursor.execute(command_string)
    except Exception as e:
        print(str(e))

"""
Create posterior parameters table
"""
mean_string_template = "posterior_mu_{} double, "
posterior_string_template = "posterior_var_{}_{} double, "

def init_posterior_table():
    try:
        mean_fields = [mean_string_template.format(i) for i in range(RL_ALG_FEATURE_DIM)]
        posterior_fields = [posterior_string_template.format(i, j) for i in range(RL_ALG_FEATURE_DIM) for j in range(RL_ALG_FEATURE_DIM)]
        mean_fields_string = ''.join(mean_fields)
        posterior_fields_string = ''.join(posterior_fields)
        mean_and_posterior_fields = mean_fields_string + posterior_fields_string
        # removes extra ", " for the last column field
        mean_and_posterior_fields = mean_and_posterior_fields[:-2]
        column_fields = """CREATE TABLE posterior_weights_table (policy_idx int, timestamp DATETIME, {})""".format(mean_and_posterior_fields)

        mycursor.execute(column_fields)

        # inputting values
        policy_idx = 0
        vals = list_to_vals([policy_idx, str(datetime.now())] + list(np.concatenate([PRIOR_MU, PRIOR_SIGMA.flatten()])))
        sql_command = "INSERT INTO posterior_weights_table ({}) VALUES ({})".format(POSTERIOR_TABLE_COLS, vals)
        mycursor.execute(sql_command)
        MYDB.commit()
    except Exception as e:
        print(str(e))

init_user_info_table()
print("Created user info table.")
init_policy_info_table()
print("Created policys info table.")
create_action_selection_data_table()
print("Created action selection data table.")
create_user_data_table()
print("Created user data table.")
create_update_data_table()
print("Created update data table.")
init_posterior_table()
print("Created posterior weights table.")

MYDB.close() #close the connection
