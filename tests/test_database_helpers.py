import unittest
import numpy as np
from rl_ohrs.database.helpers import *

class DataTablesIntegrationTest(unittest.TestCase):

    TEST_STRING_RESPONSE = [('robas+15@developers.pg.com',), ('robas+16@developers.pg.com',), \
                        ('robas+23@developers.pg.com',), ('robas+24@developers.pg.com',)]

    TEST_FLOAT_RESPONSE = [(0, 0.0, 4.925, 0.0, 0.0, 82.209)]

    def test_format_string_results(self):
        formatted_result = format_string_result(self.TEST_STRING_RESPONSE)
        self.assertEqual(formatted_result, ['robas+15@developers.pg.com', 'robas+16@developers.pg.com', \
                        'robas+23@developers.pg.com', 'robas+24@developers.pg.com',])

    def test_format_float(self):
        formatted_result = format_float_result(self.TEST_FLOAT_RESPONSE)
        np.testing.assert_array_equal(formatted_result, np.array([0, 0.0, 4.925, 0.0, 0.0, 82.209]))


    def test_list_to_columns(self):
        column_list = ["action", "prob", "reward", "quality", "state_tod"]
        cols = list_to_columns(column_list)
        self.assertEqual(cols, "action, prob, reward, quality, state_tod")

    # in mysql, values each have '' around them
    def test_list_to_vals(self):
        vals_list = ["string val", 123]
        vals = list_to_vals(vals_list)
        self.assertEqual(vals, "'string val', '123'")

if __name__ == "__main__":
    unittest.main()
