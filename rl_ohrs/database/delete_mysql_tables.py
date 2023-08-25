from database_connector import MYDB

mycursor = MYDB.cursor()
TABLE_NAMES = ["policy_info_table", "user_data_table", "action_selection_data_table", "update_data_table", "posterior_weights_table", "user_info_table"]

"""
Delete Tables
"""
### WARNING: CALLING THIS FUNCTION WILL DELETE ALL TABLES IN DATABASE
def delete_all_tables():
    for table in TABLE_NAMES:
        sql_command = "DROP TABLE {}".format(table)
        mycursor.execute(sql_command)

    print("All tables deleted.")

delete_all_tables()

MYDB.close() #close the connection
