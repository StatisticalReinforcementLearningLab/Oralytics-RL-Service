from flask import Flask, request
import requests
from action_selection import action_selection
from bayes_lr import BayesianLinearRegression
from schedule import *
from database.data_tables_integration import get_registered_users
from update import update_study_info, update_recent_data, use_data_update_posterior
from maintain_users import maintain_current_users

RL_ENDPOINTS_HASH = ""

# Note: everyday, the endpoints should be called in the following order
# 1. '/update_study_info/'
# 2. '/update/'
# 3. '/update_current_users/'
# 4. '/decision/all'

app = Flask(__name__)
@app.route('/decision/<user_id>', methods=['GET', 'POST'])
def decision(user_id):
    # 1. main controller will send a user_id
    # 2. we will process the most recent state
    # 3. we will then input the current state to our action selection procedure
    # 4. the action selection procedure will output a 7-day schedule of actions
    # 5. this endpoint returns a JSON object with a unique user-schedule identifier
    # and the 7-day schedule of actions
    current_alg = BayesianLinearRegression()
    action_schedule, schedule_id = action_selection(current_alg, user_id)
    response_dict = create_single_response_dict(user_id, schedule_id, action_schedule)
    response = create_json_responses(response_dict)

    return response

@app.route('/decision/all/{}'.format(RL_ENDPOINTS_HASH), methods=['GET', 'POST'])
def decision_all():
    # call endpoint for all registered users
    current_users_list = get_registered_users()
    response_list = []
    # get current posterior sampling algorithm
    current_alg = BayesianLinearRegression()
    for user_id in current_users_list:
        action_schedule, schedule_id = action_selection(current_alg, user_id)
        response = create_single_response_dict(user_id, schedule_id, action_schedule)
        response_list.append(response)

    all_response = create_json_responses(response_list)

    return all_response

@app.route('/update_study_info/{}'.format(RL_ENDPOINTS_HASH), methods=['GET'])
def update_current_study_info():
    update_study_info()

    return "Update study info"

# We want this endpoint to be called daily
@app.route('/update/{}'.format(RL_ENDPOINTS_HASH), methods=['GET'])
def update():
    update_recent_data()
    print("Updated Batch Data.")
    use_data_update_posterior()
    print("Updated Posterior Algorithm Weights.")

    return "Update batch data and posterior weights."

# - We want this endpoint to be called daily before /decisions/all
# - This endpoint updates the database that maintains which users
# are currently in the study
@app.route('/update_current_users/{}'.format(RL_ENDPOINTS_HASH), methods=['GET'])
def update_current_users():
    maintain_current_users()

    return "List of current study users updated."
