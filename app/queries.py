from app import app
from flask_login import current_user


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


def query_individual_annotations(username):
    return {"$and":[
        {"has_labeled_comment":True},
        {"toxicity.manual_labels.user":username},
        ]
    }
