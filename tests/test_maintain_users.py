import unittest
from unittest.mock import patch, ANY, call
from schedule import construct_schedule_id
from maintain_users import *

class MaintainUsersTest(unittest.TestCase):

    USER_DECISION_TIMES_DICT = {
    "morningTimeWeekday": "09:00:00",
    "eveningTimeWeekday": "22:00:00",
    "morningTimeWeekend": "10:00:00",
    "eveningTimeWeekend": "22:00:00"}

    @patch('maintain_users.set_user_info')
    @patch('maintain_users.get_user_decision_times', return_value=USER_DECISION_TIMES_DICT)
    def test_set_user_decision_times(self, get_user_decision_times, set_user_info):
        user_id = "robas+1"
        set_user_decision_times(user_id)
        set_user_info_calls = [
        call(user_id, "morning_time_weekday", "09:00:00"),
        call(user_id, "evening_time_weekday", "22:00:00"),
        call(user_id, "morning_time_weekend", "10:00:00"),
        call(user_id, "evening_time_weekend", "22:00:00")
        ]
        set_user_info.assert_has_calls(set_user_info_calls)

    @patch('maintain_users.set_user_info')
    @patch('maintain_users.get_study_description', return_value=2)
    @patch('maintain_users.get_user_decision_times', return_value=USER_DECISION_TIMES_DICT)
    def test_add_user_to_study(self, get_user_decision_times, \
                            get_study_description, set_user_info):
        user_id = "robas+1"
        add_user_to_study(user_id)
        set_user_info_calls = [
        call(user_id, "user_start_day", ANY),
        call(user_id, "user_end_day", ANY),
        call(user_id, "currently_in_study", 1),
        call(user_id, "user_day_in_study", 1),
        call(user_id, "user_entry_decision_t", 2),
        call(user_id, "user_last_decision_t", 142),
        call(user_id, "most_recent_schedule_id", construct_schedule_id(user_id, 0))
        ]
        set_user_info.assert_has_calls(set_user_info_calls)

    @patch('maintain_users.get_current_users', return_value=["robas+9", "robas+1"])
    @patch('maintain_users.check_user_registered', return_value=False)
    @patch('maintain_users.check_user_has_brushing_sessions', return_value=True)
    @patch('maintain_users.push_registered_user')
    @patch('maintain_users.set_user_info')
    @patch('maintain_users.set_user_decision_times')
    def test_register_new_user(self, set_user_decision_times, set_user_info, \
                                push_registered_user, check_user_has_brushing_sessions, \
                                check_user_registered, get_current_users):
        maintain_current_users()
        push_registered_user.assert_called_with(ANY)
        set_user_info_calls = [
        call(ANY, "user_day_in_study", 0),
        call(ANY, "user_opened_app", 0),
        call(ANY, "user_start_day", ANY),
        call(ANY, "user_end_day", ANY)
        ]
        set_user_info.assert_has_calls(set_user_info_calls)
        set_user_decision_times.assert_called_with(ANY)

    # if user does not have first brushing session then DO NOT REGISTER THEM
    @patch('maintain_users.get_current_users', return_value=["robas+1"])
    @patch('maintain_users.check_user_registered', return_value=False)
    @patch('maintain_users.check_user_has_brushing_sessions', return_value=False)
    @patch('maintain_users.register_user')
    def test_do_not_register_new_user(self, register_user, check_user_has_brushing_sessions, \
                                check_user_registered, get_current_users):
        maintain_current_users()
        assert not register_user.called

    @patch('maintain_users.get_current_users', return_value=["robas+9", "robas+1"])
    @patch('maintain_users.check_user_registered', return_value=True)
    @patch('maintain_users.get_user_info', return_value=USER_START_DAY_DEFAULT)
    @patch('maintain_users.set_user_info')
    @patch('maintain_users.check_user_open_app', return_value=(1, ""))
    def test_adding_user_to_study(self, check_user_open_app, set_user_info, get_user_info, \
                                check_user_registered, get_current_users):
        maintain_current_users()
        set_user_info.assert_called_with(ANY, ANY, ANY)

    @patch('maintain_users.get_current_users', return_value=["robas+9", "robas+1"])
    @patch('maintain_users.check_user_registered', return_value=True)
    @patch('maintain_users.get_user_info', return_value=71)
    @patch('maintain_users.set_user_info')
    def test_remove_finished_user(self, set_user_info, \
    get_user_info, check_user_registered, get_current_users):
        maintain_current_users()
        set_user_info.assert_called_with(ANY, "currently_in_study", 0)

    @patch('maintain_users.get_current_users', return_value=["robas+9", "robas+1"])
    @patch('maintain_users.check_user_registered', return_value=True)
    @patch('maintain_users.get_user_info', return_value=2)
    @patch('maintain_users.set_user_info')
    def test_increment_current_user(self, set_user_info, \
    get_user_info, check_user_registered, get_current_users):
        maintain_current_users()
        get_user_info.assert_called_with("user_day_in_study", ANY)
        set_user_info.assert_called_with(ANY, "user_day_in_study", 3)

if __name__ == "__main__":
    unittest.main()
