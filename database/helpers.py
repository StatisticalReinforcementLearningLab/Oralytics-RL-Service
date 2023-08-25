import numpy as np

"""
Helpers
"""

def format_batch_data_result(results):

    return np.array(results)

def format_float_result(results):
    # recast this nested tuple to a python list and flatten it so it's a proper iterable:
    x = map(list, list(results)) # change the type
    x = sum(x, [])
    D = np.fromiter(x, dtype=np.double, count=-1)

    return D

def format_string_result(results):

    return [string_val[0] for string_val in results]

def list_to_columns(column_list):
    return ''.join(["{}, ".format(val) for val in column_list])[:-2]

def list_to_vals(val_list):
    return ''.join(["'{}', ".format(val) for val in val_list])[:-2]

def set_multiple_values_from_dict(dict):
    return ''.join(["{} = {}, ".format(col_name, dict[col_name]) for col_name in dict.keys()])[:-2]
