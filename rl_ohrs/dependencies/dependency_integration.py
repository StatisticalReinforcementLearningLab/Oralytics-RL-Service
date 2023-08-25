import requests
from datetime import datetime, timedelta
import json
import traceback

from rl_ohrs.dependencies.dependency_connector import (
    DATA_DEPENDENCY_REQUEST,
    DECISION_TIMES_REQUEST,
    STUDY_USERS_REQUEST,
    ANALYTICS_DATA_REQUEST
)
from rl_ohrs.database.data_tables_integration import get_user_info
from rl_ohrs.rl_email import exception_handler

"""
Calling Endpoints
"""
def get_json_response(user_id, endpoint_name):
    if endpoint_name == "brushing":
        request_path = DATA_DEPENDENCY_REQUEST.format(user_id)
    elif endpoint_name == "app_analytics":
        request_path = ANALYTICS_DATA_REQUEST.format(user_id)
    elif endpoint_name == "study_users":
        request_path = STUDY_USERS_REQUEST
    elif endpoint_name == "decision_times":
        request_path = DECISION_TIMES_REQUEST.format(user_id)
    else:
        raise Exception("provided endpoint_name doesn't exist")
    try:
        response = requests.get(request_path)
        try:
            return response.json()

        except Exception as e:
            print(str(e))
            exception_handler([user_id, endpoint_name], "dependency json", traceback.format_exc())

    except Exception as e:
        print(str(e))
        exception_handler([user_id, endpoint_name], "dependency fail", traceback.format_exc())

### Getting Brushing Data ###
def get_user_brushing_data(user_id):

    return get_json_response(user_id, "brushing")

### Getting Analytics Data ###
def get_user_analytics_data(user_id):

    return get_json_response(user_id, "app_analytics")

### Getting Study Users ###
def get_study_users_data():

    return get_json_response(None, "study_users")

def get_current_users():
    json_response = get_study_users_data()
    try:
        return [block['email'] for block in json_response if block["user_currently_in_study"] == 1]

    except Exception as e:
        print(str(e))
        exception_handler(["study_users", None], "dependency data malformed", traceback.format_exc())

def get_registered_users():
    json_response = get_study_users_data()
    try:
        return [block['email'] for block in json_response if block["user_is_registered"] == 1]

    except Exception as e:
        print(str(e))
        exception_handler(["study_users", None], "dependency data malformed", traceback.format_exc())

def did_pure_exploration_end():
    try:
        json_response = get_study_users_data()
        num_users_started_study = len([block['email'] for block in json_response if block["user_start_date"]])

        return num_users_started_study > 15

    except Exception as e:
        print(str(e))
        exception_handler(["study_users", None], "dependency data malformed", traceback.format_exc())

### Getting User-Specific Decision Times (Weekday and Weekend) ###
def process_decision_times(decision_times_json):
    decision_times_dict = decision_times_json[0]

    return decision_times_dict

### Getting Decision Times Data ###
def get_user_decision_times(user_id):
    json_response = get_json_response(user_id, "decision_times")
    try:
        return process_decision_times(json_response)

    except Exception as e:
        print(str(e))
        exception_handler(["decision_times", user_id], "dependency data malformed", traceback.format_exc())

"""
Helpers for Brushing and Analytics Data
"""
def get_datetime(datetime_string):
    return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')

def get_date(date_string):
    return datetime.strptime(date_string, '%Y-%m-%d')

def is_weekend(date):
    if date.weekday() > 4:
      return 1
    else:
      return 0

def get_user_dt_for_date(date, type, user_id):
    if is_weekend(date):
        if type == "morning":
            dt = date.strftime("%Y-%m-%d") + " " + get_user_info("morning_time_weekend", user_id)
        elif type == "evening":
            dt = date.strftime("%Y-%m-%d") + " " + get_user_info("evening_time_weekend", user_id)
    else:
        if type == "morning":
            dt = date.strftime("%Y-%m-%d") + " " + get_user_info("morning_time_weekday", user_id)
        elif type == "evening":
            dt = date.strftime("%Y-%m-%d") + " " + get_user_info("evening_time_weekday", user_id)

    return dt

def is_yesterdays_data(date_string):
    curr_datetime = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    ct = datetime.now()
    ## FOR DEBUGGING ##
    # ct = datetime.strptime('2023-02-01 02:00:00', '%Y-%m-%d %H:%M:%S')

    return ct - timedelta(hours=24) <= curr_datetime

def get_brushing_comps(recent_response):
    brushing_duration = int(recent_response[0]["brushingDuration"])
    pressure_duration = int(recent_response[0]["pressureDuration"])

    return brushing_duration, pressure_duration

# if user has no brushing data then the json_response will be:
# {'message': 'Email not found'}
def check_no_data_for_user(json_response):
    # Email not found condition
    not_found_condition = "message" in json_response and json_response["message"] == 'Email not found'
    # Empty response condition if json_response is empty list
    empty_response = len(json_response) == 0

    return not_found_condition or empty_response

def parse_analytics_response(json_response):
    for session in json_response:
        for analytics_block in json.loads(session["analytics_data"]):
            if analytics_block.get("event") == "GetScheduledMessagesSuccess" and is_yesterdays_data(analytics_block.get("app_created_at")):
                return 1, analytics_block.get("app_created_at")

    return 0, None

def check_user_open_app(user_id):
    analytics_json_response = get_user_analytics_data(user_id)
    opened_app, app_timestamp = parse_analytics_response(analytics_json_response)

    return opened_app, app_timestamp

# returns either (0,0), (0,1), (1,1) to denote which schedule
# the most recent morning and evening actions came from
# for example:
# * user opened the app before the morning decision time so both
# the most recent morning and evening actions were from the most recent schedule
# * user opened the app after the morning decision time but before evening so
# the most recent morning action was from the last saved schedule id and evening action
# was from the most recent schedule
def check_action_from_schedule(user_id, app_timestamp):
    app_date_time = get_datetime(app_timestamp)
    yesterday_date = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
    if is_weekend(get_date(yesterday_date)):
        user_morning_dt = get_datetime(yesterday_date + " " + get_user_info("morning_time_weekend", user_id))
        user_evening_dt = get_datetime(yesterday_date + " " + get_user_info("evening_time_weekend", user_id))
    else:
        user_morning_dt = get_datetime(yesterday_date + " " + get_user_info("morning_time_weekday", user_id))
        user_evening_dt = get_datetime(yesterday_date + " " + get_user_info("evening_time_weekday", user_id))
    # opened app before morning dt
    if app_date_time < user_morning_dt:
        return 1, 1
    # opened app after evening dt
    elif app_date_time > user_evening_dt:
        return 0, 0
    # opened app between morning and evening dt
    else:
        return 0, 1

def get_previous_evening_window(user_id):
    user_evening_dt = get_user_dt_for_date(datetime.now().date() - timedelta(days=2), "evening", user_id)
    user_next_morning_dt = get_user_dt_for_date(datetime.now().date() - timedelta(days=1), "morning", user_id)
    previous_evening_start = get_datetime(user_evening_dt)
    previous_evening_end = get_datetime(user_next_morning_dt)

    return previous_evening_start, previous_evening_end

def get_recent_morning_window(user_id):
    yesterday_date = datetime.now().date() - timedelta(days=1)
    user_morning_dt = get_user_dt_for_date(yesterday_date, "morning", user_id)
    user_next_evening_dt = get_user_dt_for_date(yesterday_date, "evening", user_id)
    recent_morning_start = get_datetime(user_morning_dt)
    recent_morning_end = get_datetime(user_next_evening_dt)

    return recent_morning_start, recent_morning_end

def is_within_window(datetime_string, start_datetime, end_datetime):
    dt = datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')

    return dt >= start_datetime and dt < end_datetime

# gets brushing quality for evening (curr_day - 2), brushing quality for morning (curr_day - 1),
# app_engagement for morning (curr_day - 1), and app_engagement for evening (curr_day - 1)
def get_recent_user_data(user_id):
    result_dict = {}
    ##### PROCESSING BRUSHING DATA FOR evening (curr_day - 2) and morning (curr_day - 1) ######
    try:
        brushing_json_response = get_user_brushing_data(user_id)
        # no brushing data at all means that user has not "started the study"
        if check_no_data_for_user(brushing_json_response):
            exception_handler(["brushing", user_id], "no data for user", traceback.format_exc())
            return None
        previous_evening_start, previous_evening_end = get_previous_evening_window(user_id)
        recent_morning_start, recent_morning_end = get_recent_morning_window(user_id)
        previous_evening_filter = lambda datetime_string: is_within_window(datetime_string, previous_evening_start, previous_evening_end)
        recent_morning_filter = lambda datetime_string: is_within_window(datetime_string, recent_morning_start, recent_morning_end)
        # get evening (curr_day - 2) brushing comps
        previous_evening_brushing = [block for block in brushing_json_response if previous_evening_filter(block["sessionStartTime"])]
        # get morning (curr_day - 1) brushing comps
        recent_morning_brushing = [block for block in brushing_json_response if recent_morning_filter(block["sessionStartTime"])]
        result_dict["previous_evening_duration"], result_dict["previous_evening_pressure"] = \
                        (0, 0) if len(previous_evening_brushing) == 0 else get_brushing_comps(previous_evening_brushing)
        result_dict["recent_morning_duration"], result_dict["recent_morning_pressure"] = \
                        (0, 0) if len(recent_morning_brushing) == 0 else get_brushing_comps(recent_morning_brushing)
    except Exception as e:
        print(str(e))
        exception_handler(["brushing", user_id], "dependency data malformed", traceback.format_exc())
    ##### PROCESSING ANALYTICS DATA FOR morning (curr_day - 1) and evening (curr_day - 1) ######
    try:
        opened_app, app_timestamp = check_user_open_app(user_id)
        result_dict["app_engagement"] = opened_app
        if opened_app:
            m_ind, e_ind = check_action_from_schedule(user_id, app_timestamp)
            result_dict["morning_used_recent_schedule"] = m_ind
            result_dict["evening_used_recent_schedule"] = e_ind

        return result_dict

    except Exception as e:
        print(str(e))
        exception_handler(["app", user_id], "dependency data malformed", traceback.format_exc())

# this is to check if a user has their first brushing session
# and can therefore begin the study
def check_user_has_brushing_sessions(user_id):
    try:
        brushing_json_response = get_user_brushing_data(user_id)
        # no brushing data at all means that user has not "started the study"
        if check_no_data_for_user(brushing_json_response):
            return False
        else:
            return True
    except Exception as e:
        print("Error: couldn't check if user: {} has first brushing session.".format(user_id))
        print(str(e))
