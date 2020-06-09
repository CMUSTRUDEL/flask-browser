# import sqlalchemy as sa
# from sqlalchemy import Column, Table
# from sqlalchemy import Integer, String, Boolean, BigInteger, DateTime, Text
# from sqlalchemy.dialects.mysql import TIMESTAMP
# from sqlalchemy.orm import relationship, backref
#from sqlalchemy.ext.associationproxy import association_proxy
# from twitterDB.base import Base

from app import db, mongo
from dateutil import parser
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from time import time
import jwt
from app import app
from .queries import ToxicIssuesQuerySet, IssueCommentsQuerySet


#################################
#### Twitter MySQL DB Tables ####
#################################

class User(UserMixin, db.Model):
    __tablename__ = 'browser_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<User {}>'.format(self.username)    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def grab_data(self):
        return TwitterUser.query.filter(TwitterUser.id <= 100)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)



@login.user_loader
def load_user(id):
    return User.query.get(int(id))



class TwitterUser(db.Model):
    __tablename__ = 'mongo_users'
    
    id = db.Column(db.Integer, primary_key=True)
    tw_id = db.Column(db.String(255))
    mongo_collection = db.Column(db.Integer)
    ght_id = db.Column(db.BigInteger, db.ForeignKey("profiles.id"), nullable=False)
    tw_name = db.Column(db.Text)
    tw_screen_name = db.Column(db.Text)
    tw_created_at = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    tw_followers = db.Column(db.Integer)
    tw_listed = db.Column(db.Integer)
    tw_favourites = db.Column(db.Integer)
    tw_utc = db.Column(db.Text)
    tw_time_zone = db.Column(db.Text)
    tw_location = db.Column(db.Text)
    tw_statuses = db.Column(db.Integer)
    tw_friends = db.Column(db.Integer)
    tw_url = db.Column(db.Text)
    tw_desc = db.Column(db.Text)
    tw_lang = db.Column(db.Text)
    tw_img_url = db.Column(db.Text)

    gh_profile = db.relationship('GHProfile', backref='mongo_users')

    def __repr__(self):
        return 'Twitter user: %s - %s' % \
                    (self.tw_id, self.tw_name) 
    


class GHProfile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(255))
    name = db.Column(db.Text)
    email = db.Column(db.Text)
    company = db.Column(db.Text)
    blog = db.Column(db.Text)
    location = db.Column(db.Text)
    bio = db.Column(db.Text)
    public_repos = db.Column(db.Integer)
    followers = db.Column(db.Integer)
    avatar_url = db.Column(db.Text)
    twitter = db.Column(db.Text)
    linkedin = db.Column(db.Text)
    linkedin_type = db.Column(db.String(2))

    def __repr__(self):
        return 'GitHub user: %s - %s' % \
                    (self.id, self.login) 
    


class TwitterUserLabel(db.Model):
    __tablename__ = 'browser_labels'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("browser_users.id"), nullable=False)
    tw_id = db.Column(db.String(255), db.ForeignKey("mongo_users.tw_id"), nullable=False)
    text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow)
    
    author = db.relationship('User', backref='browser_labels')

    def __repr__(self):
        return 'Label for tw_user %s: %s' % \
                    (self.tw_id, self.text) 
    


#####################################
#### GHTorrent Mongo Collections ####
#####################################

class Issue(mongo.DynamicDocument):
    meta = {
        'collection': 'issues'
    }
#     body = mongo.StringField(max_length=50, required=True)
#     number = mongo.StringField(max_length=50, required=True)


class IssueComment(mongo.DynamicDocument):
    meta = {
        'collection': 'issue_comments',
        'queryset_class': IssueCommentsQuerySet
    }


class ToxicIssue(mongo.DynamicDocument):
    meta = {
        'collection': 'christian_toxic_issues',
        'queryset_class': ToxicIssuesQuerySet
    }

class ToxicIssueComment(mongo.DynamicDocument):
    meta = {
        'collection': 'christian_toxic_issue_comments',
        'queryset_class': ToxicIssuesQuerySet
    }






    # def __init__(self, username, email, password):
    #     self.username = username
    #     self.email = email
    #     self.password = password
    #     self.is_admin = False



    # def __init__(self,
    #             tw_id, 
    #             mongo_collection,
    #             ght_id, 
    #             tw_name, 
    #             tw_screen_name,
    #             tw_created_at,
    #             tw_followers, 
    #             tw_listed, 
    #             tw_favourites,
    #             tw_utc, 
    #             tw_time_zone,
    #             tw_location, 
    #             # tw_profile_location,
    #             tw_statuses, 
    #             tw_friends, 
    #             tw_url,
    #             tw_desc, 
    #             tw_lang,
    #             tw_img_url):

    #     self.tw_id = tw_id
    #     self.mongo_collection = mongo_collection
    #     self.ght_id = ght_id
    #     self.tw_name = tw_name
    #     self.tw_screen_name = tw_screen_name
    #     # self.tw_created_at = tw_created_at
    #     self.tw_followers = tw_followers
    #     self.tw_listed = tw_listed
    #     self.tw_favourites = tw_favourites
    #     self.tw_utc = tw_utc
    #     self.tw_time_zone = tw_time_zone
    #     self.tw_location = tw_location
    #     # self.tw_profile_location = tw_profile_location
    #     self.tw_statuses = tw_statuses
    #     self.tw_friends = tw_friends
    #     self.tw_url = tw_url
    #     self.tw_desc = tw_desc
    #     self.tw_lang = tw_lang
    #     self.tw_img_url = tw_img_url
        
    #     if tw_created_at is not None:
    #         st = parser.parse(tw_created_at)
    #         self.tw_created_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
    #     else:
    #         self.tw_created_at = None


