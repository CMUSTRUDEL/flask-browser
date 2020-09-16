from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_pymongo import PyMongo
from flask_session import Session
from flaskext.markdown import Markdown
from mdx_gfm import GithubFlavoredMarkdownExtension

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
pmongo = PyMongo(app)
md = Markdown(app, extensions=[GithubFlavoredMarkdownExtension()])
login = LoginManager(app)
login.login_view = 'login'
mail = Mail(app)
Session(app)

from app import routes, routes_twitter, routes_toxic, routes_black, models, errors, stratified

