import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://%s:%s@%s/%s?charset=utf8mb4' % \
                                        (os.environ.get('DB_USERNAME', ''),
                                        os.environ.get('DB_PASSWORD', ''),
                                        os.environ.get('DB_HOST', ''),
                                        os.environ.get('DATABASE_NAME', ''))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    RESULTS_PER_PAGE = 20

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['vasilescu@cmu.edu']

    SECRET_KEY = '1234567890'

