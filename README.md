# Oralytics-RL-Service
This is the backend code for the RL algorithm used in the [Oralytics clinical trial](https://clinicaltrials.gov/study/NCT05624489). The RL algorithm in Oralytics optimizes the delivery of engagement prompts to participants to maximize their brushing quality (or oral self-care behaviors). For more information about Oralytics, please see the following papers:
* [Designing Reinforcemnt Learning Algorithms for Digital Interventions: Pre-Implementation Guidelines](https://scholar.google.com/citations?view_op=view_citation&hl=en&user=mAgilOsAAAAJ&citation_for_view=mAgilOsAAAAJ:u-x6o8ySG0sC)
* [Reward Design For An Online Reinforcement Learning Algorithm Supporting Oral Self-Care](https://scholar.google.com/citations?view_op=view_citation&hl=en&user=mAgilOsAAAAJ&citation_for_view=mAgilOsAAAAJ:d1gkVwhDpl0C)
  
## Citing Our Code
If you use our code or algorithm in anyway, please cite us:
```
@article{trella2022designing,
  title={Designing reinforcement learning algorithms for digital interventions: pre-implementation guidelines},
  author={Trella, Anna L and Zhang, Kelly W and Nahum-Shani, Inbal and Shetty, Vivek and Doshi-Velez, Finale and Murphy, Susan A},
  journal={Algorithms},
  volume={15},
  number={8},
  pages={255},
  year={2022},
  publisher={MDPI}
}
```
```
@inproceedings{trella2023reward,
  title={Reward design for an online reinforcement learning algorithm supporting oral self-care},
  author={Trella, Anna L and Zhang, Kelly W and Nahum-Shani, Inbal and Shetty, Vivek and Doshi-Velez, Finale and Murphy, Susan A},
  booktitle={Proceedings of the AAAI Conference on Artificial Intelligence},
  volume={37},
  number={13},
  pages={15724--15730},
  year={2023}
}
```

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
