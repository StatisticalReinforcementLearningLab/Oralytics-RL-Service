
"""
Hash
"""
HASH = ""
"""
Dependency endpoints prefix
"""
DEPENDENCY_PREFIX = ""
"""
Path to obtain user brushing data
"""
OHRS_DATA_PATH = DEPENDENCY_PREFIX + ""
DATA_DEPENDENCY_REQUEST = OHRS_DATA_PATH + "{}" + HASH

"""
Path to obtain users decision times
"""
DECISION_TIMES_PATH = DEPENDENCY_PREFIX + ""
DECISION_TIMES_REQUEST = DECISION_TIMES_PATH + "{}" + HASH

"""
Path to obtain app engagement data
"""
ANALYTICS_DATA_PATH = DEPENDENCY_PREFIX + ""
ANALYTICS_DATA_REQUEST = ANALYTICS_DATA_PATH + "{}" + HASH

"""
Path to obtain all current users
"""
STUDY_USERS_REQUEST = DEPENDENCY_PREFIX + "" + HASH
