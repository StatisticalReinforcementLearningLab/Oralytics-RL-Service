import unittest
from unittest.mock import patch
from unittest.mock import ANY
from unittest.mock import Mock
import numpy as np
from datetime import datetime

from rl_ohrs.database.data_tables_integration import *
from rl_ohrs.database.database_connector import TEST_MYDB
from rl_ohrs.maintain_users import add_user_to_study, register_user
from rl_ohrs.global_vars import PRIOR_MU, PRIOR_SIGMA
from create_test_data_tables import (
                init_user_info_table,
                create_update_data_table,
                create_action_selection_data_table,
                create_user_data_table,
                init_policy_info_table,
                init_posterior_table
)

def drop_test_table(table_name):
    test_cursor = TEST_MYDB.cursor()
    execute_push("DROP TABLE {}".format(table_name))

@patch('rl_ohrs.database.data_tables_integration.get_db', return_value=TEST_MYDB)
class DataTablesIntegrationTest(unittest.TestCase):
    USER_ID = 'robas+1'
    SCHEDULE_ID = "test"
    USER_DECISION_TIMES_DICT = {
    "morningTimeWeekday": "09:00:00",
    "eveningTimeWeekday": "22:00:00",
    "morningTimeWeekend": "10:00:00",
    "eveningTimeWeekend": "22:00:00"}

    ### USER INFO TABLE ###

    @patch('rl_ohrs.maintain_users.get_user_decision_times', return_value=USER_DECISION_TIMES_DICT)
    def test_user_registered(self, get_user_decision_times, mock_MYDB):
        init_user_info_table()
        register_user(self.USER_ID)
        registered_but_not_started = get_user_info("user_start_day", self.USER_ID)
        self.assertEqual(datetime.strptime("0001-01-01", '%Y-%m-%d').date(), registered_but_not_started)
        self.assertEqual(get_user_info("morning_time_weekday", self.USER_ID), "09:00:00")
        self.assertEqual(get_user_info("evening_time_weekday", self.USER_ID), "22:00:00")
        self.assertEqual(get_user_info("morning_time_weekend", self.USER_ID), "10:00:00")
        self.assertEqual(get_user_info("evening_time_weekend", self.USER_ID), "22:00:00")

        drop_test_table("user_info_table")

    @patch('rl_ohrs.maintain_users.get_study_level_day_in_study', return_value=1)
    def test_set_and_get_user_info(self, get_study_description, mock_MYDB):
        # add fake users to table
        init_user_info_table()
        push_registered_user(self.USER_ID)
        add_user_to_study(self.USER_ID)
        set_user_info(self.USER_ID, "user_opened_app", 1)
        set_user_info(self.USER_ID, "most_recent_schedule_id", self.SCHEDULE_ID)
        self.assertEqual(get_user_info("user_start_day", self.USER_ID), datetime.now().date())
        self.assertEqual(get_user_info("user_entry_decision_t", self.USER_ID), 0)
        self.assertEqual(get_user_info("user_last_decision_t", self.USER_ID), 140)
        self.assertEqual(get_user_info("user_opened_app", self.USER_ID), 1)
        self.assertEqual(get_user_info("most_recent_schedule_id", self.USER_ID), self.SCHEDULE_ID)
        drop_test_table("user_info_table")

    ### UPDATE DATA TABLE ###
    @patch("rl_ohrs.database.data_tables_integration.get_study_description", return_value=3)
    def test_set_and_get_user_values_for_state(self, get_study_description, mock_MYDB):
        create_update_data_table()
        for day in range(1, 8):
            evening_row = [1, 0.5, -120, 180, 1, 0, 0, 1, 1]
            morning_row = [1, 0.5, -120, 180, 0, 0, 0, 1, 1]
            evening_dt_info = {
            "user_start_day": "2023-02-17",
            "user_end_day": "2023-04-28",
            "user_decision_t": get_evening_decision_t(day),
            "decision_time": "2023-02-19 20:00:00"
            }
            morning_dt_info = {
            "user_start_day": "2023-02-17",
            "user_end_day": "2023-04-28",
            "user_decision_t": get_morning_decision_t(day),
            "decision_time": "2023-02-20 08:00:00"
            }
            push_update_data_for_user(self.USER_ID, evening_dt_info, evening_row)
            push_update_data_for_user(self.USER_ID, morning_dt_info, morning_row)
        result = get_user_data("quality", self.USER_ID)
        np.testing.assert_array_equal(result, 180 * np.ones(14))
        result = get_user_data("action", self.USER_ID)
        np.testing.assert_array_equal(result, np.ones(14))
        drop_test_table("update_data_table")

    def test_get_user_values_empty(self, mock_MYDB):
        create_update_data_table()
        result = get_user_data("quality", self.USER_ID)
        np.testing.assert_array_equal(result, [])
        result = get_user_data("action", self.USER_ID)
        np.testing.assert_array_equal(result, [])
        drop_test_table("update_data_table")

    @patch("rl_ohrs.database.data_tables_integration.get_study_description", return_value=3)
    def test_get_batch_data_for_update(self, get_study_description, mock_MYDB):
        create_update_data_table()
        for day in range(1, 8):
            evening_row = [1, 0.5, -120, 0, 1, 0, 0, 1, 1]
            morning_row = [1, 0.5, -120, 0, 0, 0, 0, 1, 1]
            evening_dt_info = {
            "user_start_day": "2023-02-17",
            "user_end_day": "2023-04-28",
            "user_decision_t": get_evening_decision_t(day),
            "decision_time": "2023-02-19 20:00:00"
            }
            morning_dt_info = {
            "user_start_day": "2023-02-17",
            "user_end_day": "2023-04-28",
            "user_decision_t": get_morning_decision_t(day),
            "decision_time": "2023-02-20 08:00:00"
            }
            push_update_data_for_user(self.USER_ID, evening_dt_info, evening_row)
            push_update_data_for_user(self.USER_ID, morning_dt_info, morning_row)

        alg_states, actions, pis, rewards = get_update_data()
        np.testing.assert_array_equal(alg_states, np.array([[[1, 0, 0, 1, 1], [0, 0, 0, 1, 1]] for _ in range(7)]).reshape(14, 5))
        np.testing.assert_array_equal(actions, np.ones(14))
        np.testing.assert_array_equal(pis, 0.5 * np.ones(14))
        np.testing.assert_array_equal(rewards, -120 * np.ones(14))
        drop_test_table("update_data_table")

    ### ACTION SELECTION DATA TABLE ###
    def test_set_and_get_actual_tuple_data_for_users(self, mock_MYDB):
        create_action_selection_data_table()
        morning_dt = 2
        evening_dt = 3
        day_in_study = 2
        mock_morning_state = [0, -1, 0.8, 1, 1]
        mock_evening_state = [1, -1, 0.8, 1, 1]
        policy_idx = 0
        morning_vals = [self.USER_ID, "2022-11-01", "2022-12-01", "2022-11-29 02:00:00", self.SCHEDULE_ID, \
                        morning_dt, "2022-11-29 08:00:00", day_in_study, policy_idx, 123, 1, 0.7, \
                        mock_morning_state[0], mock_morning_state[1], mock_morning_state[2], \
                        mock_morning_state[3], mock_morning_state[4]]
        evening_vals = [self.USER_ID, "2022-11-01", "2022-12-01", "2022-11-29 02:00:00", self.SCHEDULE_ID, \
                        evening_dt, "2022-11-29 20:00:00", day_in_study, policy_idx, 123, 0, 0.45, \
                        mock_evening_state[0], mock_evening_state[1], mock_evening_state[2], \
                        mock_evening_state[3], mock_evening_state[4]]
        # first push recent morning
        push_actual_tuple_data_for_users(morning_vals)
        # then push recent evening
        push_actual_tuple_data_for_users(evening_vals)
        expected_morning_dict = {
        'action': 1.0,
        'prob': 0.7,
        'state_tod': 0.0,
        'state_b_bar': -1.0,
        'state_a_bar': 0.8,
        'state_app_engage': 1.0,
        'state_bias': 1.0
        }
        expected_evening_dict = {
        'action': 0.0,
        'prob': 0.45,
        'state_tod': 1.0,
        'state_b_bar': -1.0,
        'state_a_bar': 0.8,
        'state_app_engage': 1.0,
        'state_bias': 1.0
        }
        expected_morning_dt_info = {
        "user_start_day": datetime.strptime("2022-11-01", '%Y-%m-%d').date(),
        "user_end_day": datetime.strptime("2022-12-01", '%Y-%m-%d').date(),
        "user_decision_t": 2,
        "decision_time": datetime.strptime("2022-11-29 08:00:00", '%Y-%m-%d %H:%M:%S')
        }
        expected_evening_dt_info = {
        "user_start_day": datetime.strptime("2022-11-01", '%Y-%m-%d').date(),
        "user_end_day": datetime.strptime("2022-12-01", '%Y-%m-%d').date(),
        "user_decision_t": 3,
        "decision_time": datetime.strptime("2022-11-29 20:00:00", '%Y-%m-%d %H:%M:%S')
        }
        recent_morning_dt_info, recent_morning_row = \
                        get_actual_tuple_data_for_users(self.USER_ID, morning_dt)
        previous_evening_dt_info, previous_evening_row = \
                        get_actual_tuple_data_for_users(self.USER_ID, evening_dt)
        self.assertEqual(recent_morning_row, expected_morning_dict)
        self.assertEqual(previous_evening_row, expected_evening_dict)
        self.assertEqual(recent_morning_dt_info, expected_morning_dt_info)
        self.assertEqual(previous_evening_dt_info, expected_evening_dt_info)

        reward_comps = {
        "brushing_duration": 120,
        "pressure_duration": 0,
        "quality": 120,
        "raw_quality": 120,
        "reward": 20,
        "cost_term": 100,
        "B_condition": 1,
        "A1_condition": 0,
        "A2_condition": 0
        }
        push_actual_reward_data_for_users(self.USER_ID, morning_dt, reward_comps)
        _, result = get_actual_tuple_data_for_users(self.USER_ID, morning_dt, col_names=reward_comps.keys())
        self.assertEqual(result, reward_comps)

        drop_test_table("action_selection_data_table")

    ### USER DATA TABLE ###
    @patch('rl_ohrs.database.data_tables_integration.get_user_info', return_value="2022-11-29")
    @patch("rl_ohrs.database.data_tables_integration.get_study_description", return_value=100)
    def test_set_and_get_tuple_data_for_users(self, get_study_description, \
                                            get_user_decision_times, mock_MYDB):
        create_user_data_table()
        mock_morning_state = [0, -1, 0.8, 1, 1]
        mock_evening_state = [1, -1, 0.8, 1, 1]
        user_decision_t = 50
        day_in_study = 24
        policy_idx = 0
        seed = 123
        push_tuple_data_for_users(self.USER_ID, self.SCHEDULE_ID, user_decision_t, \
                                    "2022-11-29 09:00:00", day_in_study, policy_idx, \
                                    mock_morning_state, seed, 1, 0.5)
        push_tuple_data_for_users(self.USER_ID, self.SCHEDULE_ID, user_decision_t - 1, \
                                    "2022-11-29 20:00:00", day_in_study, policy_idx, \
                                    mock_evening_state, seed, 1, 0.5)
        result = get_tuple_data_for_users(self.USER_ID, self.SCHEDULE_ID, user_decision_t)

        self.assertEqual(result[0], self.USER_ID)
        self.assertEqual(result[4], self.SCHEDULE_ID)
        self.assertEqual(result[5], user_decision_t)
        self.assertEqual(result[9], 123)
        self.assertEqual(result[10], 1)
        self.assertEqual(result[11], 0.5)
        self.assertEqual(list(result[12:]), mock_morning_state)

        result = get_tuple_data_for_users(self.USER_ID, self.SCHEDULE_ID, user_decision_t - 1)
        self.assertEqual(result[0], self.USER_ID)
        self.assertEqual(result[4], self.SCHEDULE_ID)
        self.assertEqual(result[5], user_decision_t - 1)
        self.assertEqual(result[9], 123)
        self.assertEqual(result[10], 1)
        self.assertEqual(result[11], 0.5)
        self.assertEqual(list(result[12:]), mock_evening_state)

        drop_test_table("user_data_table")

    ### POLICY INFO TABLE ###

    def test_set_and_get_study_description(self, mock_MYDB):
        init_policy_info_table()
        push_study_description("time_updated_policy", datetime.now())
        push_study_description("policy_idx", 1)

        self.assertTrue(get_study_description("time_updated_policy") != None)
        self.assertEqual(get_study_description("policy_idx"), 1)

        drop_test_table("policy_info_table")

    ### POSTERIOR WEIGHTS TABLE ###

    def test_set_and_get_prior_values(self, mock_MYDB):
        init_policy_info_table()
        init_posterior_table()
        policy_idx, mean, var = get_posterior_values()
        self.assertEqual(policy_idx, 0)
        np.testing.assert_array_equal(mean, PRIOR_MU)
        np.testing.assert_array_equal(var, PRIOR_SIGMA)
        drop_test_table("policy_info_table")
        drop_test_table("posterior_weights_table")

    def test_set_and_get_posterior_values(self, mock_MYDB):
        init_policy_info_table()
        init_posterior_table()
        posterior_mu = np.zeros(15)
        posterior_var = np.diag(np.ones(15))
        push_updated_posterior_values(posterior_mu, posterior_var)
        policy_idx, mean, var = get_posterior_values()
        self.assertEqual(policy_idx, 1)
        np.testing.assert_array_equal(mean, posterior_mu)
        np.testing.assert_array_equal(var, posterior_var)
        drop_test_table("policy_info_table")
        drop_test_table("posterior_weights_table")

if __name__ == "__main__":
    unittest.main()
