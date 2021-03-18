from app import app
from datetime import datetime
from flask_login import current_user
from app.stratified import high_perspective
from app.survey import survey
from bson.objectid import ObjectId

query_classifier_toxic = \
    {"$and":[
        {"toxicity."+app.config['VERSION']+".score":1},
        {"toxicity."+app.config['VERSION']+".orig.persp_raw.detectedLanguages":["en"]},
        {"toxicity."+app.config['VERSION']+".en":{"$gt": .001}}
        ]
    }

query_has_predicted_toxic_comment = \
    {"toxicity."+app.config['VERSION']+".has_predicted_toxic_comment":True
    }

query_predicted_issues_all = \
    {"$or":[
        query_has_predicted_toxic_comment,
        query_classifier_toxic,
        ]
    }

query_predicted_prs_all = \
    {"$and":[
        {"$or":[
            query_has_predicted_toxic_comment,
            query_classifier_toxic,
            ]
        },
        {"is_pr":True}]
    }

query_predicted_issues_w_comments = \
    {"$and":[
            {"$or":[
                query_has_predicted_toxic_comment,
                query_classifier_toxic,
                ]
            },
            {"num_comments":{"$gt":0}}
        ]
    }


query_predicted_prs_w_comments = \
    {"$and":[
            {"$or":[
                query_has_predicted_toxic_comment,
                query_classifier_toxic,
                ]
            },
            {"num_comments":{"$gt":0}},
            {"is_pr":True}]
    }


query_predicted_prs_w_review_comments = \
    {"$and":[
            {"has_toxic_review_comment":True},
            {"num_comments":{"$gt":0}},
            {"is_pr":True}]
    }


query_ck_annotations = \
    {"$or":[
        {"toxicity.manual.score":1},
        {"toxicity.manual.score":0},
        ]
    }


query_annotations = {"has_labeled_comment":True}

query_annotations_toxic = \
    {"$or":[
        {"has_labeled_toxic_comment":True},
        {"is_labeled_toxic":True},
        ]
    }


query_confirmed_toxic = \
    {"$or":[
        {"toxicity.manual.score":1},
        {"toxicity.manual.score":0},
        {"has_labeled_comment":True},
        ]
    }

query_unlabeled = \
        {'$and': [{'is_labeled': {'$not':{'$eq': True}}}, {'has_labeled_comment': {'$not': {'$eq': True}}}]}
query_labeled_toxic = \
        {"$or" : [{"is_labeled_toxic":True}, {"has_labeled_toxic_comment": True}]}

def query_individual_annotations(username):
    return {"$and":[
        {"$or":[
            {"has_labeled_comment":True},
            {"is_labeled": True}
            ]
        },
        {"toxicity.manual_labels.user":username},
        ]
    }


def query_tolabel(username):
    return {"$and":[
        {"toxicity.manual_labels.user":{"$not": {"$regex": "^"+username+"$"}}},
        {"toxicity.manual_labeled_comments.user":{"$not": {"$regex": "^"+username+"$"}}},
        {"toxicity.todo":1}
        ]
    }

def query_closed(username):
    return {"$and":[
        {"state" : "closed" },
        {"merged" : False },
        {"$or": 
            [ {"comments": {"$gte": 10} },
              {"review_comments": {"$gte": 10} },
            ]
        },
        {"changed_files": {"$lte": 5} },
        {"created_at": {"$gte": "2020-01-01"} }
        ]
    }

def query_survey(username):
    return {"$and":[
        {"_id" : { "$in" : [ObjectId(_id) for _id in survey] } },
        {"toxicity."+app.config['VERSION']+".orig.persp_raw.detectedLanguages":["en"]},
        {"toxicity."+app.config['VERSION']+".en":{"$gt": .001}},
        {"toxicity.manual_labels.user":{"$not": {"$regex": "^"+username+"$"}}},
        {"toxicity.manual_labeled_comments.user":{"$not": {"$regex": "^"+username+"$"}}},
        ]
    }

query_stratified = \
    {"$and":[
        {"_id" : { "$in" : [ObjectId(_id) for _id in high_perspective] } },
        {"toxicity."+app.config['VERSION']+".orig.persp_raw.detectedLanguages":["en"]},
        {"toxicity."+app.config['VERSION']+".en":{"$gt": .001}}
        ]
    }


def qand(a, b):
    return {"$and": [a,b]}
def qunlabeled(a):
    return qand(a, query_unlabeled)
def qlabeled_toxic(a):
    return qand(a, query_labeled_toxic)

query_locked = {"is_locked_too_heated":True}
query_deleted= {"is_deleted":True}
query_toxiccomment= {"has_comment_classified_toxic":True}
query_coc= {"has_comment_mention_code_of_conduct":True}

