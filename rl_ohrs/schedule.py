import json
import numpy as np

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def create_schedule(action_schedule):
    schedule = {}
    for i, day_schedule in enumerate(action_schedule):
        schedule["morning_{}".format(i)] = day_schedule[0]
        schedule["evening_{}".format(i)] = day_schedule[1]

    return schedule


def create_single_response_dict(user, schedule_id, action_schedule):
    response_dict = {
    "email": user,
    "schedule_id": schedule_id,
    "action_schedule": create_schedule(action_schedule),
    }

    return response_dict

def create_json_responses(response_dict):
    response = json.dumps(response_dict, indent=4, cls=NpEncoder)

    return response

def construct_schedule_id(user_id, user_day_in_study):
    return "{}_day={}".format(user_id, user_day_in_study)
