from flask import Flask
# from flask import jsonify
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_mongoengine import MongoEngine
from flask_pymongo import PyMongo
from flask_session import Session
# from flask_fontawesome import FontAwesome
# from flask_bootstrap import Bootstrap
from flaskext.markdown import Markdown
from mdx_gfm import GithubFlavoredMarkdownExtension

import csv

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
# session = Session(app)
Session(app)

from app import routes, routes_twitter, routes_toxic, routes_black, models, errors, stratified

# reader = csv.reader(open('/data1/bogdan/twitter/tw_gh_photo_matches.csv'))
# cv2_data = {}
# for row in reader:
#     tw_id, gh_login, num_keypoints_tw, num_keypoints_gh, num_keypoints_matched = row
#     cv2_data[(tw_id, gh_login)] = num_keypoints_tw, num_keypoints_gh, num_keypoints_matched
