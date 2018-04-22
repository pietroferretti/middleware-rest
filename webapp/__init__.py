from flask import Flask
from webapp.config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

import webapp.views
