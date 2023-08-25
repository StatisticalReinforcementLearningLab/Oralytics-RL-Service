from datetime import datetime, timedelta

from rl_ohrs.global_vars import STUDY_START_DATE
from rl_ohrs.database.data_tables_integration import get_user_info, user_not_in_study

"""
Maintains the study-level day in study counter
"""

def get_date(date_string):
    return datetime.strptime(date_string, '%Y-%m-%d').date()

def calculate_day_in_study(start_date):
    curr_date = datetime.now().date()

    return (curr_date - start_date).days + 1

# study-level day in study
def get_study_level_day_in_study():
    first_day_in_study = get_date(STUDY_START_DATE)

    return calculate_day_in_study(first_day_in_study)

# user-level day in study
def get_user_day_in_study(user_id):
    # day 0 for registered users that have not started the study
    if user_not_in_study(user_id):
        return 0
    else:
        user_start_date = get_user_info("user_start_day", user_id)

        return calculate_day_in_study(user_start_date)
