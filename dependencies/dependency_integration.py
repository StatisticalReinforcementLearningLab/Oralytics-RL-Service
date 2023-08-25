from dependencies.dependency_connector import (
    DATA_DEPENDENCY_REQUEST,
    DECISION_TIMES_REQUEST,
    BETA_USERS_REQUEST,
    ANALYTICS_DATA_REQUEST
)
from database.data_tables_integration import get_user_info
import requests
from datetime import datetime, timedelta
import json

"""
Calling Endpoints
"""
def get_json_response(request_path):
    try:
        response = requests.get(request_path)

        return response.json()

    except Exception as e:
        print(str(e))
        print("Couldn't get response for {}".format(request_path))

### Getting Brushing Data ###
def get_user_brushing_data(user_id):
    request_path = DATA_DEPENDENCY_REQUEST.format(user_id)

    return get_json_response(request_path)

### Getting Analytics Data ###
def get_user_analytics_data(user_id):
    request_path = ANALYTICS_DATA_REQUEST.format(user_id)

    return get_json_response(request_path)

### Getting Study Users ###
def process_users(users_json):
    current_users_list = []
    for block in users_json:
        current_users_list.append(block['email'])

    return current_users_list

# ANNA TODO: for pilot study RL service handles current users
# for real study, main controller will handle this functionality
def get_current_users():
    try:
        # CHANGED TO BETA USERS FOR NOW BECAUSE OF BETA TEST
        current_users_json_response = get_json_response(BETA_USERS_REQUEST)
        current_users_list = process_users(current_users_json_response)

        return current_users_list

    except Exception as e:
        print(str(e))
        print("Error in getting and processing study users.")

### Getting User-Specific Decision Times (Weekday and Weekend) ###
def process_decision_times(decision_times_json):
    decision_times_dict = decision_times_json[0]

    return decision_times_dict

def get_user_decision_times(user_id):
    try:
        json_response = get_json_response(DECISION_TIMES_REQUEST.format(user_id))
        decision_times_dict = process_decision_times(json_response)

        return decision_times_dict

    except Exception as e:
        print(str(e))
        print("Error in getting and processing user decision times for user {}.".format(user_id))

"""
Helpers for Brushing and Analytics Data
"""
def get_datetime(datetime_string):
    return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')

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
    return "message" in json_response and json_response["message"] == 'Email not found'

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
    date = app_date_time.date()
    yesterday_date = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
    if is_weekend(date):
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

# ANNA TODO: need to think about how this would work if a user sets their evening decision time to past midnight like 2AM
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

# ANNA TODO: SPLIT THIS UP INTO TWO DIFFERENT FUNCTIONS IN CASE ONE DEPENDENCY GOES WRONG!
# ANNA TODO: if there's an issue and this returns None, be able to error log and handle that
# gets brushing quality for evening (curr_day - 2), brushing quality for morning (curr_day - 1),
# app_engagement for morning (curr_day - 1), and app_engagement for evening (curr_day - 1)
def get_recent_user_data(user_id):
    result_dict = {}
    try:
        brushing_json_response = get_user_brushing_data(user_id)
        # no brushing data at all means that user has not "started the study"
        if check_no_data_for_user(brushing_json_response):
            print("THERE'S NO DATA FOR USER {}".format(user_id))
            return None
        ##### PROCESSING BRUSHING DATA FOR evening (curr_day - 2) and morning (curr_day - 1) ######
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
        ##### PROCESSING ANALYTICS DATA FOR morning (curr_day - 1) and evening (curr_day - 1) ######
        opened_app, app_timestamp = check_user_open_app(user_id)
        result_dict["app_engagement"] = opened_app
        if opened_app:
            m_ind, e_ind = check_action_from_schedule(user_id, app_timestamp)
            result_dict["morning_used_recent_schedule"] = m_ind
            result_dict["evening_used_recent_schedule"] = e_ind

        return result_dict

    except Exception as e:
        print("Error: couldn't get recent user data for user: {}.".format(user_id))
        print(str(e))
        # ANNA TODO: needs logger

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
