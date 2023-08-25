import unittest
from unittest.mock import patch, ANY, call
from update import *
import numpy as np
from datetime import datetime

class UpdateTest(unittest.TestCase):

    USER_ID = 'robas+9'

    @patch('update.get_schedule_id', return_value = "robas+9_day=1")
    @patch('update.get_user_info', return_value = "3")
    @patch('update.set_user_info')
    def test_resolve_and_update_schedule_id(self, set_user_info, get_user_info, get_schedule_id):
        # expect schedule to be updated and morning_schedule_id to be old and
        # evening_schedule_id to be new
        recent_data_dict = {
          'app_engagement': 1,
          'morning_used_recent_schedule': 0,
          'evening_used_recent_schedule': 1
        }
        morning_schedule_id, evening_schedule_id = resolve_and_update_schedule_id(self.USER_ID, recent_data_dict)
        set_user_info.assert_called_with(self.USER_ID, "most_recent_schedule_id", 'robas+9_day=3')
        self.assertEqual(morning_schedule_id, "robas+9_day=1")
        self.assertEqual(evening_schedule_id, "robas+9_day=3")

        # expect schedule to be updated and morning_schedule_id to be old and
        # evening_schedule_id to be old
        recent_data_dict = {
          'app_engagement': 1,
          'morning_used_recent_schedule': 0,
          'evening_used_recent_schedule': 0
        }
        morning_schedule_id, evening_schedule_id = resolve_and_update_schedule_id(self.USER_ID, recent_data_dict)
        set_user_info.assert_called_with(self.USER_ID, "most_recent_schedule_id", 'robas+9_day=3')
        self.assertEqual(morning_schedule_id, "robas+9_day=1")
        self.assertEqual(evening_schedule_id, "robas+9_day=1")

    @patch('update.get_schedule_id', return_value = "robas+9_day=1")
    @patch('update.set_user_info')
    def test_no_update_schedule_id(self, set_user_info, get_schedule_id):
        # expect schedule to be not be updated
        recent_data_dict = {
          'app_engagement': 0
        }
        morning_schedule_id, evening_schedule_id = resolve_and_update_schedule_id(self.USER_ID, recent_data_dict)
        assert not set_user_info.called
        self.assertEqual(morning_schedule_id, "robas+9_day=1")
        self.assertEqual(evening_schedule_id, "robas+9_day=1")


    @patch('update.get_user_info', return_value = "robas+9_2")
    def test_get_schedule_id_old(self, get_user_info):
        schedule_id = get_schedule_id(self.USER_ID)

        self.assertEqual(schedule_id, "robas+9_2")

    SAR_COLUMN_NAMES = ["action", "prob", "reward", "quality", "state_tod", \
                    "state_b_bar", "state_a_bar", "state_app_engage", "state_bias"]
    SA_COLUMN_NAMES = ["action", "prob", "state_tod", "state_b_bar", \
                        "state_a_bar", "state_app_engage", "state_bias"]
    ACTUAL_TUPLE_DATA_TEST = dict(zip(SA_COLUMN_NAMES, [1, 0.45, 0, 0, 0, 0, 1]))
    USER_DT_INFO = {
    "user_start_day": "2023-02-17",
    "user_end_day": "2023-04-28",
    "user_decision_t": get_evening_decision_t(2),
    "decision_time": "2023-02-19 20:00:00"
    }
    TUPLE_DATA_TEST = dict(zip(SAR_COLUMN_NAMES, [0, 0.5, None, None, 0, 1000, 0, 0, 1]))

    @patch('update.get_actual_tuple_data_for_users', return_value = (USER_DT_INFO, ACTUAL_TUPLE_DATA_TEST))
    @patch('update.get_tuple_data_col_val', return_value = 1)
    @patch('update.push_actual_reward_data_for_users')
    def test_get_row_for_batch_data_update(self, push_actual_reward_data_for_users, \
                                            get_tuple_data_for_users, \
                                            get_actual_tuple_data_for_users):
        schedule_id = "robas+9_2"
        brushing_duration = 120
        brushing_pressure = 1
        decision_t = 2
        user_dt_info, row = get_row_for_batch_data_update(self.USER_ID, decision_t, schedule_id, \
                                        brushing_duration, brushing_pressure)
        b_bar = 1
        app_engage = 1

        self.assertTrue(row == [1, 0.45, 119, 119, 0, b_bar, 0, app_engage, 1])
        self.assertEqual(user_dt_info, self.USER_DT_INFO)
        push_actual_reward_data_for_users.assert_called_with(self.USER_ID, decision_t, ANY)

    @patch('update.get_tuple_data_for_users', return_value = TUPLE_DATA_TEST)
    @patch('update.push_actual_tuple_data_for_users')
    def test_get_and_push_actual_row(self, push_actual_tuple_data_for_users, \
                        get_tuple_data_for_users):
        schedule_id = "robas+9_1"
        decision_t = 1
        get_and_push_actual_row(self.USER_ID, schedule_id, decision_t)

        push_actual_tuple_data_for_users.assert_called_with(ANY)

    @patch('update.get_study_description', return_value = "2")
    @patch('update.push_study_description')
    def test_update_study_info(self, push_study_description, get_study_description):
        update_study_info()
        push_study_description_calls = [
        call("calendar_decision_t", 4),
        call("day_in_study", 3)
        ]
        push_study_description.assert_has_calls(push_study_description_calls)

    MOCK_STATES = np.zeros(shape=(100, 5))
    MOCK_ACTIONS = np.zeros(100)
    MOCK_PIS = 0.5 * np.ones(100)
    MOCK_REWARDS = np.zeros(100)
    MOCK_MEAN = np.zeros(15)
    MOCK_VAR = np.diag(np.ones(15))

    @patch('update.get_current_study_users', return_value = ["robas+9", "robas+8", "robas+1"])
    @patch('update.get_recent_user_data', return_value = {'previous_evening_duration': 0,
      'previous_evening_pressure': 0,
      'recent_morning_duration': 0,
      'recent_morning_pressure': 0,
      'app_engagement': 1,
      'morning_used_recent_schedule': 0,
      'evening_used_recent_schedule': 1
      })
    @patch('update.get_user_info', return_value = 2)
    @patch('update.resolve_and_update_schedule_id', return_value = ("robas_day=1", "robas_day=2"))
    @patch('update.get_and_push_actual_row')
    @patch('update.get_row_for_batch_data_update', return_value = (USER_DT_INFO, [0, 0.5, 120, 120, 1, 1000, 0, 0, 1]))
    @patch('update.push_update_data_for_user')
    @patch('update.set_user_info')
    def test_update_recent_data(self, set_user_info, push_update_data_for_user, \
                                get_row_for_batch_data_update, \
                                get_and_push_actual_row, \
                                resolve_and_update_schedule_id, \
                                get_user_info, get_recent_user_data, get_current_study_users):
        update_recent_data()
        get_and_push_actual_row_calls = [call('robas+9', "robas_day=1", 2),
        call('robas+9', "robas_day=2", 3),
        call('robas+8', "robas_day=1", 2),
        call('robas+8', "robas_day=2", 3),
        call('robas+1', "robas_day=1", 2),
        call('robas+1', "robas_day=2", 3)]
        get_and_push_actual_row.assert_has_calls(get_and_push_actual_row_calls)
        # check for pushing previous evening decision_t = 1
        # check for pushing recent morning decision_t = 2
        get_row_for_batch_data_update_calls = [call('robas+9', 1, 'robas+9_day=1', 0, 0),
        call('robas+9', 2, 'robas+9_day=2', 0, 0),
        call('robas+8', 1, 'robas+8_day=1', 0, 0),
        call('robas+8', 2, 'robas+8_day=2', 0, 0),
        call('robas+1', 1, 'robas+1_day=1', 0, 0),
        call('robas+1', 2, 'robas+1_day=2', 0, 0)]
        get_row_for_batch_data_update.assert_has_calls(get_row_for_batch_data_update_calls)
        push_update_data_for_user_calls = [call('robas+9', self.USER_DT_INFO, [0, 0.5, 120, 120, 1, 1000, 0, 0, 1]),
        call('robas+9', self.USER_DT_INFO, [0, 0.5, 120, 120, 1, 1000, 0, 0, 1]),
        call('robas+8', self.USER_DT_INFO, [0, 0.5, 120, 120, 1, 1000, 0, 0, 1]),
        call('robas+8', self.USER_DT_INFO, [0, 0.5, 120, 120, 1, 1000, 0, 0, 1]),
        call('robas+1', self.USER_DT_INFO, [0, 0.5, 120, 120, 1, 1000, 0, 0, 1]),
        call('robas+1', self.USER_DT_INFO, [0, 0.5, 120, 120, 1, 1000, 0, 0, 1])]
        push_update_data_for_user.assert_has_calls(push_update_data_for_user_calls)
        set_user_info.assert_called_with(ANY, "user_opened_app", 1)

    # ANNA TODO: after you add in a logger or monitoring system, test that you called it
    @patch('update.get_current_study_users', return_value = ["robas+1", "robas+2", "robas+3"])
    @patch('update.get_recent_user_data', return_value = None)
    def test_update_recent_data_handles_exceptions(self, get_recent_user_data, get_current_study_users):
        update_recent_data()

    @patch('update.get_update_data', return_value = (MOCK_STATES, MOCK_ACTIONS, MOCK_PIS, MOCK_REWARDS))
    @patch('update.update_posterior', return_value = (MOCK_MEAN, MOCK_VAR))
    @patch('update.push_updated_posterior_values')
    def test_posterior_update(self, push_updated_posterior_values, update_posterior, get_update_data):
        use_data_update_posterior()

        push_updated_posterior_values.assert_called_with(self.MOCK_MEAN, self.MOCK_VAR)

if __name__ == "__main__":
    unittest.main()
