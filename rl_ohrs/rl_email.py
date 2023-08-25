from flask import Flask
import logging
from flask_mail import Mail, Message

from rl_ohrs.config import params
from rl_ohrs import app

# # configuration of mail
app.config['MAIL_SERVER']= params['MAIL_SERVER']
app.config['MAIL_PORT'] = params['MAIL_PORT']
app.config['MAIL_USERNAME'] = params['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = params['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = params['MAIL_USE_TLS']
app.config['MAIL_USE_SSL'] = params['MAIL_USE_SSL']
mail = Mail(app)

logging.basicConfig(filename='record.log', level=logging.DEBUG, filemode="w")

# for each type of exception, add exception type: text as dictionary entry
email_text = {
    "dependency fail": "Endpoint call to {} failed for user {}.",
    "dependency json": "Endpoint call response to {} cannot be jsonified for user {}.",
    "dependency data malformed": "Endpoint call to {} returned malformed data for user {}.",
    "no data for user": "Endpoint call to {} returned no data for user {}.",
    "fallback": "Action selection procedure failed and fallback method was executed for user {}.",
    "user batch data update": "Error in user data update for user {}.",
    "posterior update fail": "Algorithm could not update policy (posterior parameters) with given batch data.",
    "test email": "This is a test email from the Oralytics monitoring system."
}

recipient_emails = params['recipient_emails']

# when throwing exception/calling this handler function,
# in each different place it's called pass in diff exception type
def exception_handler(params, exception_type, trace):
    content = email_text[exception_type].format(*params)
    app.logger.error(content)
    app.logger.debug(trace)
    send_message(content, trace)

def send_message(error, trace):
    msg = Message(error,
                  sender=params['MAIL_USERNAME'],
                  recipients=recipient_emails)
    msg.body=trace
    with app.app_context():
        mail.send(msg)
