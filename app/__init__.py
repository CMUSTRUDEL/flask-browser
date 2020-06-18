from flask import Flask
# from flask import jsonify
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_mongoengine import MongoEngine
from flask_pymongo import PyMongo
# from flask_fontawesome import FontAwesome
# from flask_bootstrap import Bootstrap
from flaskext.markdown import Markdown
from mdx_gfm import GithubFlavoredMarkdownExtension


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
mongo = MongoEngine(app)
pmongo = PyMongo(app)
# fa = FontAwesome(app)
# md = Markdown(app, extensions=['fenced_code'])
md = Markdown(app, extensions=[GithubFlavoredMarkdownExtension()])
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
mail = Mail(app)
# bootstrap = Bootstrap(app)

from app import routes, routes_twitter, routes_toxic, routes_black, models, errors

