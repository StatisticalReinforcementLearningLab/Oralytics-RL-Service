from rl_ohrs import app
from rl_ohrs.database.data_tables_integration import get_entire_data_table, get_data_table_from_timestamp

DATA_ENDPOINTS_HASH = ""

# should only be called for data tables where we maintain and update values such as:
# * policy_info_table
# * user_info_table
# Note: these data tables are small enough to not need timestamps to pull periodic data
@app.route('/get_study_rl_data/<data_table_name>/{}'.format(DATA_ENDPOINTS_HASH), methods=['GET', 'POST'])
def get_study_rl_data(data_table_name):
    result = get_entire_data_table(data_table_name)

    return result

# should only be called for data tables with timestamps:
# * action_selection_data_table
# * user_data_table
# * update_data_table
# * posterior_weights_table
@app.route('/get_rl_data/<data_table_name>/<start_date>/<end_date>/{}'.format(DATA_ENDPOINTS_HASH), methods=['GET', 'POST'])
def get_rl_data(data_table_name, start_date, end_date):
    result = get_data_table_from_timestamp(data_table_name, start_date, end_date)

    return result
