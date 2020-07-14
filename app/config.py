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

    MONGO_URI = 'mongodb://%s:%s@%s:27017/%s' % \
                    (os.environ.get('MONGO_USER', ''),
                    os.environ.get('MONGO_PASSWORD', ''),
                    os.environ.get('MONGO_HOST', ''),
                    os.environ.get('MONGO_DB', ''))

    MONGODB_SETTINGS = {'db':os.environ.get('MONGO_DB', ''),
                        'host':MONGO_URI}

    RESULTS_PER_PAGE = 20
    PER_PAGE_PARAMETER = 1

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['vasilescu@cmu.edu']

    VERSION = 'v2'

    PHOTO_GH_LABELS = [
            ['Confirm','valid'], 
            ['Invalid', 'invalid']
        ]

    TW_GH_LABELS = [
            ['Confirm','valid'], 
            ['Invalid', 'invalid']
        ]

    TOXICITY_LABELS = [
            ['Confirm toxic','toxic'], 
            ['Potentially problematic', 'maybe'],
            ['Not toxic -- Non english', 'not-english'], 
            ['Not toxic -- Selfdirected', 'self-directed'],
            ['Not toxic -- Owner', 'owner'],
            ['Not toxic -- Mild/colloquial', 'mild'],
            ['Not toxic -- Other', 'other'],
            ['Other, maybe, revisit', 'revisit']
        ]

    SESSION_TYPE = 'filesystem'

    FOLDER_TW = os.environ.get('FOLDER_TW')
    FOLDER_GH = os.environ.get('FOLDER_GH')
    FOLDER_TW_GH = os.environ.get('FOLDER_TW_GH')
