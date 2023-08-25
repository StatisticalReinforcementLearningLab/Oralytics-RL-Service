from datetime import datetime, timedelta

from rl_ohrs.database.data_tables_integration import user_not_in_study, check_user_registered, get_user_info, set_user_info, push_registered_user, get_study_description, USER_START_DAY_DEFAULT
from rl_ohrs.dependencies.dependency_integration import get_user_decision_times, get_registered_users, get_current_users
from rl_ohrs.day_in_study import get_study_level_day_in_study
from rl_ohrs.schedule import construct_schedule_id
from rl_ohrs.global_vars import STUDY_DURATION

def set_user_decision_times(user_id):
    decision_times_dict = get_user_decision_times(user_id)
    set_user_info(user_id, "morning_time_weekday", decision_times_dict["morningTimeWeekday"])
    set_user_info(user_id, "evening_time_weekday", decision_times_dict["eveningTimeWeekday"])
    set_user_info(user_id, "morning_time_weekend", decision_times_dict["morningTimeWeekend"])
    set_user_info(user_id, "evening_time_weekend", decision_times_dict["eveningTimeWeekend"])

def register_user(user_id):
    push_registered_user(user_id)
    # this value denotes that the user has not entered the study yet
    # but is needed for indexing in action selection
    set_user_info(user_id, "user_opened_app", 0)
    # default values for start and end in order for "push_tuple_data_for_users" function during
    # action-selection to work
    set_user_info(user_id, "user_start_day", USER_START_DAY_DEFAULT)
    set_user_info(user_id, "user_end_day", USER_START_DAY_DEFAULT)
    set_user_decision_times(user_id)

def add_user_to_study(user_id):
    set_user_info(user_id, "user_start_day", datetime.now().date())
    set_user_info(user_id, "user_end_day", (datetime.now().date() + timedelta(days=70)))
    study_day_in_study = get_study_level_day_in_study()
    current_decision_t = (2 * study_day_in_study) - 2
    set_user_info(user_id, "user_entry_decision_t", current_decision_t)
    set_user_info(user_id, "user_last_decision_t", current_decision_t + 2 * STUDY_DURATION)
    set_user_info(user_id, "most_recent_schedule_id", construct_schedule_id(user_id, 0))
    set_user_info(user_id, "user_opened_app", 1)

# update data table with users that are registered
def update_internal_registered_users(registered_users_list):
    for user_id in registered_users_list:
        # check if user_id has already been registered
        if check_user_registered(user_id) == 0:
            register_user(user_id)

# update data table with users that are currently in the study
def update_internal_current_users(current_users_list):
    for user_id in current_users_list:
        # check if main controller enrollments endpoint says the user has entered the study
        # but we have not recorded that the user has started the study
        if user_not_in_study(user_id):
            add_user_to_study(user_id)

def update_internal_users():
    update_internal_registered_users(get_registered_users())
    update_internal_current_users(get_current_users())
