import pymongo
import config
import random
from pymongo import MongoClient
def connect_to_database():
	mongo_name = config.mongo["user"]
	mongo_password = config.mongo["passwd"]
    # Connect to the Mongo Databases
	client = pymongo.MongoClient()
	db = client[config.mongo["db"]]
	db.authenticate(name=mongo_name, password=mongo_password)
	return db
db = connect_to_database()

q_istoxic = {"toxicity.v2.score":1}
q_isdeleted= {"toxicity.deleted":1}
q_tooheated= {"toxicity.locked":1}
q_notrecent = { "updated_at": {"$lt": "2020-06-01"} }
q_fewcomments = { "num_comments": {"$lte": 3} }
q_manycomments = { "num_comments": {"$gt": 3} }
q_unlabeled = {"$or": [
	{"toxicity.manual_labels":{"$exists": 0}},
	{"toxicity.manual_labels":{"$size": 0}} ]}
q_partiallylabeled = {"$or": [
	{"toxicity.manual_labels":{"$size": 1}},
	{"toxicity.manual_labels":{"$size": 2}},
	{"toxicity.manual_labels":{"$size": 3}}
	]}

def q(query,num):
  print(query)
  c=db.christian_toxic_issues.find(query, limit=num, sort=[("updated_at", -1)])
  i = 0
  for r in c:
    db.christian_toxic_issues.find_one_and_update(
      {"_id": r["_id"] },
      {"$set": {"toxicity.todo": 1,"random":random.random()}}
    )
    i = i + 1
  print(i)
  return True


#reset all todos
db.christian_toxic_issues.update_many({"toxicity.todo":1},{"$set":{"toxicity.todo":0}})

unlabeled_with_few_comments=q({ "$and":[q_istoxic, q_notrecent, q_fewcomments, q_unlabeled]},50)
unlabeled_with_many_comments=q({ "$and":[q_istoxic, q_notrecent, q_manycomments, q_unlabeled]},100)
partially_labeled_with_few_comments=q({ "$and":[q_istoxic, q_notrecent, q_fewcomments, q_partiallylabeled]},100)
partially_labeled_with_many_comments=q({ "$and":[q_istoxic, q_notrecent, q_manycomments, q_partiallylabeled]},200)
unlabeled_too_heated=q({ "$and":[q_tooheated, q_notrecent, q_unlabeled]},100)
partially_labeled_too_heated=q({ "$and":[q_tooheated, q_notrecent, q_partiallylabeled]},200)
unlabeled_deleted=q({ "$and":[q_isdeleted, q_notrecent, q_unlabeled]},50)
partially_labeled_deleted=q({ "$and":[q_isdeleted, q_notrecent, q_partiallylabeled]},100)
