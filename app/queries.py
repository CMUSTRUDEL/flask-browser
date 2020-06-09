# from flask_mongoengine import MongoEngine
from app import app
# from app import mongo
from flask_mongoengine import BaseQuerySet

class ToxicIssuesQuerySet(BaseQuerySet):

    def get_toxic_issues(self):
        '''
        {
          "toxicity.<v>.score":1, 
          "toxicity.<v>.orig.persp_raw.detectedLanguages":"en", 
          "toxicity.<v>.en":{$gt:0.001}
        }
        '''
        # Note: fields cannot contain '.' --> replace by '_'
        kwargs = {
            'toxicity__{0}__score'.format(app.config['VERSION']): 1,
            'toxicity__{0}__orig__persp_raw__detectedLanguages'.format(app.config['VERSION']): ["en"],
            'toxicity__{0}__en__{1}'.format(app.config['VERSION'], 'gt'): 0.001
        }
        return self.filter(**kwargs)


class IssueCommentsQuerySet(BaseQuerySet):

    def get_comments(self, owner, repo, number):
        kwargs = {
            'owner': owner,
            'repo': repo,
            'issue_id': number
        }
        return self.filter(**kwargs)
