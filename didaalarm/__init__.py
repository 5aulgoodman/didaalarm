from flask import Flask, url_for, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
# set the secret key.  keep this really secret:
app.secret_key = b'\xad\xf3s\xa4u\xbf \x1dM\xc9\xb2\x1e%\x91\x1cG\xdaF\x91c\x99!\xeb\xe8'
db = SQLAlchemy(app)
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from didaalarm import models,views
#db.create_all()