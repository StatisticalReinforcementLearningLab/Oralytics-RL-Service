from database_connector import MYDB
import pandas as pd
import os

mycursor = MYDB.cursor()

TABLE_NAMES = ["policy_info_table", "user_data_table", "action_selection_data_table", "update_data_table", "posterior_weights_table", "user_info_table"]

"""
Turns MySQL table to Pandas DF for easy readability
"""
def sql_to_df(table_name):
    print("For Table: {}".format(table_name))
    try:
        query = "SELECT * FROM {};".format(table_name)
        df = pd.read_sql(query, MYDB)
        write_path = "dataframes"
        if not os.path.exists(write_path):
            os.mkdir(write_path)
        # save pickle
        pd.to_pickle(df, write_path + "/{}.p".format(table_name))
        # save csv file
        df.to_csv(write_path + "/{}.csv".format(table_name))
    except Exception as e:
        print(str(e))

for table_name in TABLE_NAMES:
    sql_to_df(table_name)

MYDB.close() #close the connection
