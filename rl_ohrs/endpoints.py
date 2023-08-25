from rl_ohrs import app
from rl_ohrs.action_selection import action_selection
from rl_ohrs.bayes_lr import BayesianLinearRegression
from rl_ohrs.schedule import *
from rl_ohrs.dependencies.dependency_integration import did_pure_exploration_end, get_registered_users
from rl_ohrs.update import update_recent_data, use_data_update_posterior
from rl_ohrs.maintain_users import update_internal_users

RL_ENDPOINTS_HASH = ""

# Note: everyday, the endpoints should be called in the following order
# 1. '/update/'
# 2. main controller updates their own '/ohrsenrollmentsall/' endpoint
# 3. '/decision/all'

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
    # we update internal user database
    update_internal_users()
    print("Updated Internal Users.")
    # call endpoint for all registered users
    registered_users_list = get_registered_users()
    response_list = []
    # get current posterior sampling algorithm
    current_alg = BayesianLinearRegression()
    for user_id in registered_users_list:
        action_schedule, schedule_id = action_selection(current_alg, user_id)
        response = create_single_response_dict(user_id, schedule_id, action_schedule)
        response_list.append(response)

    all_response = create_json_responses(response_list)

    return all_response

@app.route('/update_batch_data/{}'.format(RL_ENDPOINTS_HASH), methods=['GET'])
def update_batch_data():
    update_recent_data()
    print("Updated Batch Data.")

    return "Update Batch Data Endpoint Success."

# We want this endpoint to be called daily
@app.route('/update/{}'.format(RL_ENDPOINTS_HASH), methods=['GET'])
def update():
    if did_pure_exploration_end():
        use_data_update_posterior()
        print("Updated Posterior Algorithm Weights.")

    return "Update Posterior Endpoint Success."
