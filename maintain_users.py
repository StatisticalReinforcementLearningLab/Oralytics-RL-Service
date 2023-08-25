from database.data_tables_integration import get_user_info, set_user_info, check_user_registered, push_registered_user, get_study_description
from dependencies.dependency_integration import get_current_users, check_user_has_brushing_sessions, get_user_decision_times, check_user_open_app
from datetime import datetime, timedelta
from schedule import construct_schedule_id
from global_vars import STUDY_DURATION

USER_START_DAY_DEFAULT = datetime.strptime("0001-01-01", '%Y-%m-%d').date()

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
    set_user_info(user_id, "user_day_in_study", 0)
    set_user_info(user_id, "user_opened_app", 0)
    # default values for start and end in order for "push_tuple_data_for_users" function during
    # action-selection to work
    set_user_info(user_id, "user_start_day", USER_START_DAY_DEFAULT)
    set_user_info(user_id, "user_end_day", USER_START_DAY_DEFAULT)
    set_user_decision_times(user_id)

def add_user_to_study(user_id):
    set_user_info(user_id, "user_start_day", datetime.now().date())
    set_user_info(user_id, "user_end_day", (datetime.now().date() + timedelta(days=70)))
    set_user_info(user_id, "currently_in_study", 1)
    set_user_info(user_id, "user_day_in_study", 1)
    study_day_in_study = get_study_description("day_in_study")
    current_decision_t = (2 * study_day_in_study) - 2
    set_user_info(user_id, "user_entry_decision_t", current_decision_t)
    set_user_info(user_id, "user_last_decision_t", current_decision_t + 2 * STUDY_DURATION)
    set_user_info(user_id, "most_recent_schedule_id", construct_schedule_id(user_id, 0))
    set_user_info(user_id, "user_opened_app", 1)

def user_finished_study(user_id):
    set_user_info(user_id, "currently_in_study", 0)

def increment_user_day_in_study(user_id):
    current_day = get_user_info("user_day_in_study", user_id)
    set_user_info(user_id, "user_day_in_study", current_day + 1)

def maintain_current_users():
    for user_id in get_current_users():
        if check_user_registered(user_id):
            # user is registered but is not currently in the study
            if get_user_info("user_start_day", user_id) == USER_START_DAY_DEFAULT:
                # if the user opened their app and successfully got the first schedule of actions
                opened_app, app_timestamp = check_user_open_app(user_id)
                if opened_app:
                    print("ADDING USER: {} TO STUDY".format(user_id))
                    add_user_to_study(user_id)
            # user is currently in study
            else:
                user_in_study = get_user_info("currently_in_study", user_id)
                user_day_in_study = get_user_info("user_day_in_study", user_id)
                # check if user finished study
                if user_in_study and (user_day_in_study > STUDY_DURATION):
                    # remove users from study
                    print("USER: {} HAS FINISHED THE STUDY".format(user_id))
                    user_finished_study(user_id)
                elif user_in_study and (user_day_in_study <= STUDY_DURATION):
                    # increment day in study
                    increment_user_day_in_study(user_id)
        # if user is has not registered yet, check if we should register them
        elif check_user_has_brushing_sessions(user_id):
            print("USER: {} HAS FIRST BRUSHING SESSION".format(user_id))
            print("ADDING NEW REGISTERED USER: ", user_id)
            # check if we should add user
            # if user has any registered brushing sessions then this will be a non empty response
            # otherwise, the value will be None
            register_user(user_id)
