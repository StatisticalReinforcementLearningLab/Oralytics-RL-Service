import unittest
from unittest.mock import patch
import numpy as np

from rl_ohrs.process_state import *


class ProcessStateTest(unittest.TestCase):

    def test_process_alg_state(self):
        app_engagement_indict = 1
        b_bar = 100
        a_bar = 0.8
        state = process_alg_state(0, b_bar, a_bar, app_engagement_indict)

        np.testing.assert_array_equal(state, np.array([0, b_bar, a_bar, 1, 1]))

    @patch("rl_ohrs.process_state.get_user_data", return_value = 120 * np.ones(6))
    def test_get_most_recent_qualities(self, get_user_data):
        qualities = get_most_recent_qualities("robas+9")

        self.assertTrue((qualities == 120 * np.ones(6)).all())

    @patch("rl_ohrs.process_state.get_user_data", return_value = np.ones(6))
    def test_get_most_recent_actions(self, get_user_data):
        actions = get_most_recent_actions("robas+9")

        self.assertTrue((actions == np.ones(6)).all())

    def test_get_b_bar_a_bar_first_day(self):
        j = 0
        user_qualities = np.array([])
        user_actions = np.array([])
        b_bar, a_bar = get_b_bar_a_bar(user_qualities, user_actions)

        self.assertEqual(b_bar, 0)
        self.assertEqual(a_bar, 0)

    def test_get_b_bar_a_bar_first_week(self):
        j = 4
        user_qualities = 120 * np.ones(j)
        user_actions = np.zeros(j)
        b_bar, a_bar = get_b_bar_a_bar(user_qualities, user_actions)

        self.assertEqual(b_bar, 120)
        self.assertEqual(a_bar, 0)

    @patch('rl_ohrs.process_state.calculate_b_bar', return_value = 1000)
    @patch('rl_ohrs.process_state.calculate_a_bar', return_value = 1)
    def test_get_b_bar_a_bar_after_first_week(self, calculate_a_bar, calculate_b_bar):
        j = 20
        user_qualities = 120 * np.ones(j)
        user_actions = np.zeros(j)
        b_bar, a_bar = get_b_bar_a_bar(user_qualities, user_actions)

        self.assertEqual(b_bar, 1000)
        self.assertEqual(a_bar, 1)

    @patch('rl_ohrs.process_state.get_user_info', return_value = 2)
    @patch('rl_ohrs.process_state.get_b_bar_a_bar', return_value = (0, 0))
    @patch('rl_ohrs.process_state.process_alg_state', return_value = np.ones(5))
    def test_get_and_process_states(self, process_alg_state, get_b_bar_a_bar, get_user_info):
        morning_state, evening_state = get_and_process_states("robas+9", None, None)

        np.testing.assert_array_equal(morning_state, np.ones(5))
        np.testing.assert_array_equal(evening_state, np.ones(5))

if __name__ == "__main__":
    unittest.main()
