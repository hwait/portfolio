from flask import Flask
from flask_wtf.csrf import CSRFProtect
import os
csrf = CSRFProtect()
app = Flask(__name__)
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

app.BASE_DIR = os.path.abspath(os.path.dirname(__file__))  
#app.debug=True
app.csrf_enabled     = True
app.csrf_session_key = "FgJT4DYVdWchOEm24Wy1vl7d"
app.secret_key = "e96TBjtHB1pFHA4oid2eHTxh"
csrf.init_app(app)


import port.views
from port.mod_jobs.views import mod_jobs
from port.mod_jobs.models import *

db.bind('sqlite', 'port.db', create_db=True)
db.generate_mapping(create_tables=True)

app.register_blueprint(mod_jobs)
