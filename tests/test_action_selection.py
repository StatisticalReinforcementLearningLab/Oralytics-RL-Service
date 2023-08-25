import unittest
from unittest.mock import patch, ANY
import numpy as np

from rl_ohrs.action_selection import *
from rl_ohrs.process_state import get_a_bar
from rl_ohrs.bayes_lr import BayesianLinearRegression
from rl_ohrs.rl_email import exception_handler

class ActionSelectionTest(unittest.TestCase):

    CURRENT_STATES = np.array([0, 0, 0, 1, 1]), np.array([1, 0, 0, 1, 1])
    USER_ACTIONS = np.append(np.ones(7), np.zeros(7))

    def test_state_evolution(self):
        j = 14
        user_actions = np.ones(j)
        next_morning_state, next_evening_state = state_evolution(self.CURRENT_STATES, user_actions)

        np.testing.assert_array_equal(next_morning_state, np.array([0, 0, get_a_bar(user_actions[:-1]), 0, 1]))
        np.testing.assert_array_equal(next_evening_state, np.array([1, 0, get_a_bar(user_actions[:-1]), 0, 1]))

    @patch.object(BayesianLinearRegression, 'action_selection', return_value=(1, 123, 0.5))
    @patch("rl_ohrs.action_selection.get_user_dt_for_date", return_value="2022-11-29 09:00:00")
    @patch("rl_ohrs.action_selection.push_tuple_data_for_users")
    def test_impute_rest_of_schedule(self, push_tuple_data_for_users, get_user_dt_for_date, \
                                    mock_action_selection):
        schedule = np.full((SCHEDULE_LENGTH_IN_DAYS, DECISION_TIMES_PER_DAY), np.nan)
        schedule[0, 0] = 1
        schedule[0, 1] = 1
        mock_alg = BayesianLinearRegression()
        schedule = impute_rest_of_schedule("robas+9", "robas+9_1", schedule, 1, \
                    mock_alg, self.CURRENT_STATES, self.USER_ACTIONS)

        # check the first week of schedule
        np.testing.assert_array_equal(schedule[:7,:], np.ones((7, DECISION_TIMES_PER_DAY)))

    @patch("rl_ohrs.action_selection.get_most_recent_data", return_value=(None, USER_ACTIONS))
    @patch("rl_ohrs.action_selection.get_and_process_states", return_value=CURRENT_STATES)
    @patch("rl_ohrs.action_selection.get_user_day_in_study", return_value=1)
    @patch.object(BayesianLinearRegression, 'action_selection', return_value=(1, 0.5, 123))
    @patch("rl_ohrs.action_selection.get_study_level_day_in_study", return_value=1)
    @patch("rl_ohrs.action_selection.get_study_description", return_value=0)
    @patch("rl_ohrs.action_selection.get_user_dt_for_date", return_value="2022-11-29 09:00:00")
    @patch("rl_ohrs.action_selection.push_tuple_data_for_users")
    @patch("rl_ohrs.action_selection.impute_rest_of_schedule")
    def test_action_selection(self, impute_rest_of_schedule, push_tuple_data_for_users, get_user_dt_for_date, \
            get_study_description, get_study_level_day_in_study, mock_action_selection, get_user_day_in_study, \
            get_and_process_states, get_most_recent_data):
        mock_alg = BayesianLinearRegression()
        user_id = "robas+9"
        schedule, schedule_id = action_selection(mock_alg, user_id)
        calls = mock_action_selection.call_args_list
        np.testing.assert_array_equal(self.CURRENT_STATES[0], calls[0][0][0])
        np.testing.assert_array_equal(self.CURRENT_STATES[1], calls[1][0][0])
        impute_func_calls = impute_rest_of_schedule.call_args_list
        np.testing.assert_array_equal(ANY, impute_func_calls[0][0][0])
        np.testing.assert_array_equal(ANY, impute_func_calls[0][0][1])
        np.testing.assert_array_equal(ANY, impute_func_calls[0][0][2])
        np.testing.assert_array_equal(1, impute_func_calls[0][0][3])
        np.testing.assert_array_equal(mock_alg, impute_func_calls[0][0][4])
        np.testing.assert_array_equal(self.CURRENT_STATES, impute_func_calls[0][0][5])
        np.testing.assert_array_equal(np.append(self.USER_ACTIONS, [1, 1]), impute_func_calls[0][0][6])
        impute_rest_of_schedule.assert_called_with(user_id, ANY, ANY, ANY, ANY, ANY, ANY)

    @patch("rl_ohrs.action_selection.get_most_recent_data", return_value=(None, np.ones(14)))
    @patch("rl_ohrs.action_selection.get_and_process_states", return_value=CURRENT_STATES)
    @patch("rl_ohrs.action_selection.push_tuple_data_for_users")
    @patch("rl_ohrs.action_selection.exception_handler")
    def test_fallback_method_error(self, exception_handler, push_tuple_data_for_users, \
                                    get_and_process_states, get_most_recent_data):
        mock_alg = None
        user_id = "robas+9"
        schedule, schedule_id = action_selection(mock_alg, user_id)
        self.assertRaises(Exception, action_selection)
        exception_handler.assert_called_with(ANY, ANY, ANY)
        self.assertEqual(schedule.shape, (70, 2))

if __name__ == "__main__":
    unittest.main()
