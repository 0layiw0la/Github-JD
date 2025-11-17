from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import json
import itertools

load_dotenv() 

DATABASE = os.environ.get("SQL_DATABASE_URL")
SECRET_KEY = os.environ.get("SECRET_KEY")


db = SQLAlchemy()

def create_app():
    app = Flask(__name__,template_folder='templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
    app.secret_key = SECRET_KEY
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    
    app.jinja_env.filters['fromjson'] = json.loads
    app.jinja_env.filters['zip'] = lambda *seqs: list(itertools.zip_longest(*seqs, fillvalue=None))
    app.jinja_env.globals['range'] = range
    app.jinja_env.filters['select'] = lambda seq: [x for x in seq if x]

    db.init_app(app)

    #import later
    from routes import register_routes
    register_routes(app,db)

    migrate = Migrate(app,db)

    return app
