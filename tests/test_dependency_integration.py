import unittest
from unittest.mock import patch, ANY, call
import json
from datetime import datetime

from rl_ohrs.dependencies.dependency_integration import *

## def get the request, call this for json error test
# instead of json.load, only mock request and have dependency integration do jsonify
def get_example_response(request):
    f = open('tests/example_jsons/' + request)
    response = f.read()
    f.close()

    return response

def get_example_json_data(file_name):
    f = open('tests/example_jsons/' + file_name)
    response = json.load(f)
    f.close()

    return response

# gets json data but replaces sessionStartTime with desired date
def get_recent_brushing_data():
    json_data = get_example_json_data("both_sessions_brushing.json")
    json_data[0]["sessionStartTime"] = (datetime.now().date() - timedelta(days=2)).strftime("%Y-%m-%d") + " 22:34:36"
    json_data[1]["sessionStartTime"] = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d") + " 10:00:01"

    return json_data

def get_old_brushing_data():
    json_data = get_example_json_data("both_sessions_brushing.json")
    json_data[0]["sessionStartTime"] = "2022-11-28 20:34:36"
    json_data[1]["sessionStartTime"] = "2022-11-29 10:00:01"

    return json_data

# only previous evening brushing data but no recent morning brushing data
def get_some_brushing_data():
    json_data = get_example_json_data("some_sessions_brushing.json")
    json_data[0]["sessionStartTime"] = (datetime.now().date() - timedelta(days=2)).strftime("%Y-%m-%d") + " 22:34:36"

    return json_data

def get_recent_analytics_data(app_open_time):
    json_data = get_example_json_data("analytics_data.json")
    first_block = json.loads(json_data[0]["analytics_data"])

    for analytics_block in first_block:
        if analytics_block.get("event") == "GetScheduledMessagesSuccess":
            analytics_block["app_created_at"] = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d") + " {}".format(app_open_time)
    json_data[0]["analytics_data"] = json.dumps(first_block, indent = 4)

    return json_data

# helper function
def mock_get_user_info(string_val, user_id):
    if string_val == "morning_time_weekend":
        return "10:00:00"
    elif string_val == "evening_time_weekend":
        return "22:00:00"
    elif string_val == "morning_time_weekday":
        return "09:00:00"
    elif string_val == "evening_time_weekday":
        return "22:00:00"

class DependencyIntegrationTest(unittest.TestCase):
    USER_ID = "robas+9@developers.pg.com"

    def test_is_yesterdays_data(self):
        date_string = str(datetime.now() - timedelta(hours=23)).split('.')[0]
        result = is_yesterdays_data(date_string)
        self.assertTrue(result)

        date_string = str(datetime.now() - timedelta(hours=48)).split('.')[0]
        result = is_yesterdays_data(date_string)
        self.assertEqual(result, False)

    @patch('rl_ohrs.dependencies.dependency_integration.get_user_info', side_effect=lambda a,b : mock_get_user_info(a,b))
    def test_within_previous_evening_window(self, get_user_info):
        date_string_1 = (datetime.now().date() - timedelta(days=2)).strftime("%Y-%m-%d") + " " + "23:00:00"
        date_string_2 = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d") + " " + "1:00:00"
        date_string_3 = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d") + " " + "10:00:00"
        previous_evening_start, previous_evening_end = get_previous_evening_window(self.USER_ID)
        result_1 = is_within_window(date_string_1, previous_evening_start, previous_evening_end)
        result_2 = is_within_window(date_string_2, previous_evening_start, previous_evening_end)
        result_3 = is_within_window(date_string_3, previous_evening_start, previous_evening_end)
        self.assertEqual(result_1, True)
        self.assertEqual(result_2, True)
        self.assertEqual(result_3, False)

    @patch('rl_ohrs.dependencies.dependency_integration.get_user_info', side_effect=lambda a,b : mock_get_user_info(a,b))
    def test_get_recent_morning_window(self, get_user_info):
        date_string_1 = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d") + " " + "10:30:00"
        date_string_2 = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d") + " " + "16:00:00"
        date_string_3 = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d") + " " + "23:59:00"
        recent_morning_start, recent_morning_end = get_recent_morning_window(self.USER_ID)
        result_1 = is_within_window(date_string_1, recent_morning_start, recent_morning_end)
        result_2 = is_within_window(date_string_2, recent_morning_start, recent_morning_end)
        result_3 = is_within_window(date_string_3, recent_morning_start, recent_morning_end)
        self.assertEqual(result_1, True)
        self.assertEqual(result_2, True)
        self.assertEqual(result_3, False)

    def test_get_brushing_comps(self):
        recent_response = get_example_json_data("brushing_quality_data.json")
        brushing_duration, pressure_duration = get_brushing_comps(recent_response)
        self.assertEqual(brushing_duration, 120)
        self.assertEqual(pressure_duration, 5)

    def test_check_no_data_for_user(self):
        recent_response = get_example_json_data("no_data_user.json")
        user_has_no_data = check_no_data_for_user(recent_response)
        self.assertTrue(user_has_no_data)

    @patch("rl_ohrs.dependencies.dependency_integration.get_user_analytics_data", return_value=get_example_json_data("analytics_data.json"))
    @patch("rl_ohrs.dependencies.dependency_integration.is_yesterdays_data", return_value=True)
    def test_check_user_open_app(self, is_yesterdays_data, get_user_analytics_data):
        opened_app, app_timestamp = check_user_open_app(self.USER_ID)
        self.assertEqual(opened_app, 1)
        self.assertEqual(app_timestamp, "2022-12-25 17:08:36")

    @patch('rl_ohrs.dependencies.dependency_integration.get_user_info', side_effect=lambda a,b : mock_get_user_info(a,b))
    def test_check_action_from_schedule(self, get_user_info):
        # after evening dt
        app_timestamp = datetime.now().date().strftime("%Y-%m-%d") + " 01:00:00"
        m_indicator, e_indicator = check_action_from_schedule(self.USER_ID, app_timestamp)
        self.assertEqual(m_indicator, 0)
        self.assertEqual(e_indicator, 0)
        # before morning dt
        app_timestamp = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d") + " 06:00:00"
        m_indicator, e_indicator = check_action_from_schedule(self.USER_ID, app_timestamp)
        self.assertEqual(m_indicator, 1)
        self.assertEqual(e_indicator, 1)
        # between morning and evening dt
        app_timestamp = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d") + " 13:00:00"
        m_indicator, e_indicator = check_action_from_schedule(self.USER_ID, app_timestamp)
        self.assertEqual(m_indicator, 0)
        self.assertEqual(e_indicator, 1)

    @patch('rl_ohrs.dependencies.dependency_integration.get_user_brushing_data', return_value=get_recent_brushing_data())
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_analytics_data', return_value=get_recent_analytics_data("6:00:00"))
    @patch('rl_ohrs.dependencies.dependency_integration.is_yesterdays_data', return_value=True)
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_info', side_effect=lambda a,b : mock_get_user_info(a,b))
    def test_get_user_data_all_brushing_all_recent_actions(self, get_user_info, is_yesterdays_data, \
                                get_user_analytics_data, get_user_brushing_data):
        result_dict = get_recent_user_data(self.USER_ID)
        self.assertEqual({'previous_evening_duration': 123,
          'previous_evening_pressure': 0,
          'recent_morning_duration': 117,
          'recent_morning_pressure': 0,
          'app_engagement': 1,
          'morning_used_recent_schedule': 1,
          'evening_used_recent_schedule': 1
          }, result_dict)

    @patch('rl_ohrs.dependencies.dependency_integration.get_user_brushing_data', return_value=get_old_brushing_data())
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_analytics_data', return_value=get_recent_analytics_data("6:00:00"))
    @patch('rl_ohrs.dependencies.dependency_integration.is_yesterdays_data', return_value=False)
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_info', side_effect=lambda a,b : mock_get_user_info(a,b))
    def test_get_user_data_no_brushing_no_open_app(self, get_user_info, is_yesterdays_data, \
                                get_user_analytics_data, get_user_brushing_data):
        result_dict = get_recent_user_data(self.USER_ID)
        self.assertEqual({'previous_evening_duration': 0,
          'previous_evening_pressure': 0,
          'recent_morning_duration': 0,
          'recent_morning_pressure': 0,
          'app_engagement': 0
          }, result_dict)

    @patch('rl_ohrs.dependencies.dependency_integration.get_user_brushing_data', return_value=get_some_brushing_data())
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_analytics_data', return_value=get_recent_analytics_data("23:59:00"))
    @patch('rl_ohrs.dependencies.dependency_integration.is_yesterdays_data', return_value=True)
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_info', side_effect=lambda a,b : mock_get_user_info(a,b))
    def test_get_user_data_some_brushing_no_recent_actions(self, get_user_info, is_yesterdays_data, \
                                get_user_analytics_data, get_user_brushing_data):
        result_dict = get_recent_user_data(self.USER_ID)
        self.assertEqual({'previous_evening_duration': 117,
          'previous_evening_pressure': 0,
          'recent_morning_duration': 0,
          'recent_morning_pressure': 0,
          'app_engagement': 1,
          'morning_used_recent_schedule': 0,
          'evening_used_recent_schedule': 0
          }, result_dict)

    @patch('rl_ohrs.dependencies.dependency_integration.get_user_brushing_data', return_value=get_old_brushing_data())
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_analytics_data', return_value=get_recent_analytics_data("14:00:00"))
    @patch('rl_ohrs.dependencies.dependency_integration.is_yesterdays_data', return_value=True)
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_info', side_effect=lambda a,b : mock_get_user_info(a,b))
    def test_get_user_data_no_brushing_one_recent_actions(self, get_user_info, is_yesterdays_data, \
                                get_user_analytics_data, get_user_brushing_data):
        result_dict = get_recent_user_data(self.USER_ID)
        self.assertEqual({'previous_evening_duration': 0,
          'previous_evening_pressure': 0,
          'recent_morning_duration': 0,
          'recent_morning_pressure': 0,
          'app_engagement': 1,
          'morning_used_recent_schedule': 0,
          'evening_used_recent_schedule': 1
          }, result_dict)

    @patch('rl_ohrs.dependencies.dependency_integration.requests.get')
    @patch("rl_ohrs.dependencies.dependency_integration.exception_handler")
    def test_request_path_response_error(self, exception_handler, get):
        # mocks request failing
        get.side_effect = requests.exceptions.ConnectionError()
        get_json_response(self.USER_ID, "brushing")
        self.assertRaises(Exception, get_json_response)
        exception_handler.assert_called_with(ANY, "dependency fail", ANY)

    ## change this test, instead of get_example_json_data use new function
    @patch('rl_ohrs.dependencies.dependency_integration.requests.get', return_value=get_example_response("wrong_data.json"))
    @patch("rl_ohrs.dependencies.dependency_integration.exception_handler")
    def test_jsonify_error(self, exception_handler, get):
        get_json_response(self.USER_ID, "brushing")
        # will error out when get_json_response tries to jsonify
        self.assertRaises(Exception, get_json_response)
        exception_handler.assert_called_with(ANY, "dependency json", ANY)

    # return the response
    ## will probably need to double check this
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_brushing_data', return_value=None)
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_analytics_data', return_value=get_recent_analytics_data("14:00:00"))
    @patch('rl_ohrs.dependencies.dependency_integration.is_yesterdays_data', return_value=True)
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_info', side_effect=lambda a,b : mock_get_user_info(a,b))
    @patch("rl_ohrs.dependencies.dependency_integration.exception_handler")
    def test_malformed_data_error(self, exception_handler, get_user_info, is_yesterdays_data, get_user_analytics_data, \
                                  get_user_brushing_data):
        get_recent_user_data(self.USER_ID)
        self.assertRaises(Exception, get_recent_user_data)
        exception_handler.assert_called_with(ANY, ANY, ANY)

    ## and this
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_brushing_data', return_value=get_old_brushing_data())
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_analytics_data', return_value=None)
    @patch('rl_ohrs.dependencies.dependency_integration.is_yesterdays_data', return_value=True)
    @patch('rl_ohrs.dependencies.dependency_integration.get_user_info', side_effect=lambda a,b : mock_get_user_info(a,b))
    @patch("rl_ohrs.dependencies.dependency_integration.exception_handler")
    def test_malformed_data_error(self, exception_handler, get_user_info, is_yesterdays_data, get_user_analytics_data, \
                                  get_user_brushing_data):
        get_recent_user_data(self.USER_ID)
        self.assertRaises(Exception, get_recent_user_data)
        exception_handler.assert_called_with(ANY, ANY, ANY)

    @patch('rl_ohrs.dependencies.dependency_integration.get_study_users_data', return_value=get_example_json_data("some_users_start.json"))
    def test_get_current_users(self, get_study_users_data):
        users = get_current_users()
        self.assertEqual(users, ['robas+3@developers.pg.com', 'robas+9@developers.pg.com', 'robas+92@developers.pg.com', 'robas+97@developers.pg.com'])

    @patch('rl_ohrs.dependencies.dependency_integration.get_study_users_data', return_value=get_example_json_data("still_use_prior.json"))
    def test_get_registered_users(self, get_study_users_data):
        users = get_registered_users()
        self.assertEqual(users, 16 * ['robas+9@developers.pg.com'])

    @patch('rl_ohrs.dependencies.dependency_integration.get_study_users_data', return_value=get_example_json_data("exploration_period_ends.json"))
    def test_did_pure_exploration_end(self, get_study_users_data):
        self.assertTrue(did_pure_exploration_end())

    def test_get_user_decision_times(self):
        users_dt_json = get_example_json_data("decision_times_response.json")
        dt_dict = process_decision_times(users_dt_json)
        self.assertEqual(dt_dict['morningTimeWeekday'], "09:00:00")
        self.assertEqual(dt_dict['eveningTimeWeekday'], "22:00:00")
        self.assertEqual(dt_dict['morningTimeWeekend'], "10:00:00")
        self.assertEqual(dt_dict['eveningTimeWeekend'], "22:00:00")


if __name__ == "__main__":
    unittest.main()
