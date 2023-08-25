# Naming Convention For Dataframes

This document explains the column names and data frames that are used by the Oralytics RL Service.

## user_info_table
Use to keep track of study users and user information

* `user_id`: unique user id given to user in the form of `robas+{}@developers.pg.com`.
* `user_start_day`: first day that the user enters the study
* `user_end_day`: last day that the user is in the study
* `morning_time_weekday`: user-specific weekday morning decision time
* `evening_time_weekday`: user-specific weekday evening decision time
* `morning_time_weekend`: user-specific weekend morning decision time 
* `evening_time_weekend`: user-specific weekend evening decision time
* `user_entry_decision_t`: study-level decision time when the user enters the study
* `user_last_decision_t`: study-level decision time when the user exits the study
* `currently_in_study`: 1 if the user is currently in the study, 0 otherwise
* `user_day_in_study`: user-level day in study [1, 70]
* `user_opened_app`: 1 if the user opened the app the prior day, 0 otherwise
* `most_recent_schedule_id`: the schedule id of the schedule of actions most recently obtained by the app

* `user_decision_t`: indexes the user-specific decision time starts with 0, ends with 139 (note: even values denote the morning decision time, odd values denote the evening decision time)

## policy_info_table
Use to keep track of study level information and policy information 
* `time_updated_policy`: timestamp of most recent policy update
* `policy_idx`: indexes the current policy (0 - denotes the prior)
* `time_updated_day_in_study`: timestamp of most recent day in study update
* `calendar_decision_t`: study-level current decision time
* `day_in_study`: study-level day in study

## posterior_weights_table
Stores the posterior mean and variance of the RL algorithm
* `policy_idx`: index for the update time and the policy, starts with 0. 0 index refers to the prior distribution before any data update and 1 index refers to the first posterior update using data.
* `timestamp`: timestamp of policy update
* `posterior_mu.{}`: flattened posterior mean vector where `{}` indexes into the vector, starts with 0
* `posterior_var.{}.{}`: flattened posterior covariance matrix where `{}` indexes the row and the second `{}` indexes the column, starts with 0

## user_data_table
Stores every user data tuple from every schedule formed for that user

* `user_id`: unique user id given to user in the form of `robas+{}@developers.pg.com`.
* `user_start_day`: first day that the user enters the study
* `user_end_day`: last day that the user is in the study
* `timestamp`: timestamp of when the action from the corresponding schedule_id was created
* `schedule_id`: id of the schedule that this action came from
* `user_decision_t`: unique user decision time index [0, 139]
* `decision_time`: unique datetime (i.e., '%Y-%m-%d %H:%M:%S') for when the action was executed
* `day_in_study`: study-level day in study
* `policy_idx`: policy used to select action
* `action int`: \{0, 1\} where 1 denotes a message being sent and 0 denotes a message not being sent
* `prob`: action selection probability
* `state.{}`: flattened state (context) vector observed by the algorithm at decision time (Note: this is the state used for action-selection as b_bar, a_bar are imputed value depending on what schedule the user gets.)

## action_selection_data_table
Stores the user data tuple corresponding to the action that was actually executed and the components of the reward for that user decision time

* `user_id`: unique user id given to user in the form of `robas+{}@developers.pg.com`.
* `user_start_day`: first day that the user enters the study
* `user_end_day`: last day that the user is in the study
* `timestamp`: timestamp of when the action from the corresponding schedule_id was created
* `schedule_id`: id of the schedule that this action came from
* `user_decision_t`: unique user decision time index [0, 139]
* `decision_time`: unique datetime (i.e., '%Y-%m-%d %H:%M:%S') for when the action was executed
* `day_in_study`: study-level day in study
* `policy_idx`: policy used to select action
* `action int`: \{0, 1\} where 1 denotes a message being sent and 0 denotes a message not being sent
* `prob`: action selection probability
* `state.{}`: flattened state (context) vector observed by the algorithm at decision time (Note: this is the state used for action-selection as b_bar is an imputed value depending on what schedule the user gets.)
* `brushing_duration`: brushing durations in seconds
* `pressure_duration`: pressure durations in seconds
* `quality`: brushing quality truncated at 180 seconds
* `raw_quality`: actual brushing quality for that decision time
* `reward`: our designed surrogate reward given to the algorithm
* `cost_term`: cost term of surrogate reward
* `B_condition`: B_condition of the cost term
* `A1_condition`: A1_condition of the cost term
* `A2_condition`: A2_condition of the cost term
* `actual_b_bar`: actual observed b_bar state value used in calculating B_condition (notice that a_bar used in calculating A1_condition and A2_condition is the same a_bar in the state value above)

## update_data_table
Stores the batch data tuples (S, A, R, pi) that are used to update the RL algorithm

* `user_id`: unique user id given to user in the form of `robas+{}@developers.pg.com`.
* `user_start_day`: first day that the user enters the study
* `user_end_day`: last day that the user is in the study
* `timestamp`: timestamp of when this data tuple was added to the table
* `user_decision_t`: unique user decision time index [0, 139]
* `decision_time`: unique datetime (i.e., '%Y-%m-%d %H:%M:%S') for when the action was executed
* `first_policy_idx`: first policy idx to use this data tuple for update
* `action int`: \{0, 1\} where 1 denotes a message being sent and 0 denotes a message not being sent
* `prob`: action selection probability
* `reward`: our designed surrogate reward given to the algorithm
* `quality`: brushing quality truncated at 180 seconds
* `state.{}`: flattened state (context) vector observed by the algorithm at decision time (Note: this is the state used to update the algorithm, b_bar and a_bar are the actual observed values for that decision time)

