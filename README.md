# Oralytics-RL-Service

## Creating MySQL Data Tables
1. Make sure you have mysql installed locally ([video here](https://www.youtube.com/watch?v=1K4m6m5y9Oo)).
2. Run `brew services start mysql` to initialize.
3. To check that mysql works, try: `mysql -u root`
4. Create two databases (one for local dev, one for unit testing). Ex: `CREATE DATABASE local;` `CREATE DATABASE test_data;`
5. To connect to MySQL data tables, open the file and change the fields in `database/database_connector.py`:
`host="",
 user="",
 password="",
 database=""`

 then run `database/python3 create_data_tables.py`

## MySQL Data Tables to Pandas Dataframe
For readibility of data tables, run `python3 database/mysql_to_df.py` to turn all MySQL data tables to csv files and Pandas Dataframe pickles.

## Running Unit Tests
`python3 -m unittest discover tests` will run all unit tests in the `tests/` folder.

## Flask Mail
Flask-Mail is a package that needs to be downloaded. If you do not already have flask_mail installed, try:
`pip3 install --user Flask-Mail`

## Locally Testing Flask
This flask app was built using version 2.3.2.: https://flask.palletsprojects.com/en/2.3.x/patterns/packages/.
If this is the first time running the flask app, you need to tell Flask where the application instance is:
`export FLASK_APP=rl_ohrs`

Then install and run the application:
`pip3 install -e .`
Then run either:
`python3 -m flask run` or `flask run` depending on your system.
