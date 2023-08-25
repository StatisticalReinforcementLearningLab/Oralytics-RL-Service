import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
from rl_ohrs.day_in_study import *

class DayInStudyTest(unittest.TestCase):
    DAY_BEFORE = 7

    @patch('rl_ohrs.day_in_study.get_date', return_value=datetime.now().date())
    def test_get_first_day_in_study(self, get_date):
        day_in_study = get_study_level_day_in_study()
        self.assertEqual(day_in_study, 1)

    @patch('rl_ohrs.day_in_study.get_date', return_value=datetime.now().date() - timedelta(days=DAY_BEFORE))
    def test_get_d_day_in_study(self, get_date):
        day_in_study = get_study_level_day_in_study()
        self.assertEqual(day_in_study, self.DAY_BEFORE + 1)

    @patch('rl_ohrs.day_in_study.user_not_in_study', return_value=False)
    @patch('rl_ohrs.day_in_study.get_user_info', return_value=datetime.now().date() - timedelta(days=DAY_BEFORE))
    def test_get_user_day_in_study(self, get_date):
        day_in_study = get_user_day_in_study("robas+test")
        self.assertEqual(day_in_study, self.DAY_BEFORE + 1)

    @patch('rl_ohrs.day_in_study.user_not_in_study', return_value=True)
    def test_get_user_day_in_study(self, get_date):
        day_in_study = get_user_day_in_study("robas+test")
        self.assertEqual(day_in_study, 0)

if __name__ == "__main__":
    unittest.main()
