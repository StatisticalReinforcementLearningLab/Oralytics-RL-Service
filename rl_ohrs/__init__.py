from flask import Flask

app = Flask(__name__)

# resource: https://stackoverflow.com/questions/11994325/how-to-divide-flask-app-into-multiple-py-files/60441931#60441931
# we need to have a separate app and endpoints file to avoid circular dependencies
import rl_ohrs.endpoints
import rl_ohrs.external_endpoints
