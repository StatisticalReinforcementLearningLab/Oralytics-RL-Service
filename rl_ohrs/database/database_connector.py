import mysql.connector

# local mySQL table
# Note: will need to change once in cloud server
MYDB = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="local"
)

TEST_MYDB = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="test_data"
)
