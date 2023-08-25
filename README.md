# Oralytics-RL-Service

## Creating MySQL Data Tables
To create MySQL data tables open the file and change the fields in `database/database_connector.py`:
`host="",
 user="",
 password="",
 database=""`

 then run `database/python3 create_mysql_tables.py`

## MySQL Data Tables to Pandas Dataframe
For readibility of data tables, run `python3 database/mysql_to_df.py` to turn all MySQL data tables to csv files and Pandas Dataframe pickles.

## Running Unit Tests
`python3 -m unittest discover tests` will run all unit tests in the `tests/` folder.
