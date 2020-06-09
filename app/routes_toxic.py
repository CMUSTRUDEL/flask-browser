from flask import render_template, flash, redirect, url_for, abort
from flask import request
from werkzeug.urls import url_parse

from app import app
from app import db, mongo, pmongo
from app.models import User
from app.models import Issue, IssueComment, ToxicIssue, ToxicIssueComment

from flask_login import current_user, login_required

from datetime import datetime
from .utils import deep_get, is_toxic
from bson.objectid import ObjectId

import json

@app.template_filter('tojson_pretty')
def to_pretty_json(value):
    return json.dumps(value, 
                    indent=4, separators=(',', ': '))
                    # sort_keys=True,


@app.route('/toxiclabel/<table>/<eid>/<label>')
@login_required
def label_toxic_entry(table, eid, label):
    # page = request.args.get('page', 1, type=int)
    # user = User.query.filter_by(username=current_user.username).first()
    score = 0
    if label=="toxic":
        score = 1
    reason = label
    r = pmongo.db[table].find_one_and_update({"_id":ObjectId(eid)},
        # {"$set":{"toxicity.manual.score":score,
        #         "toxicity.manual.reason":reason,
        #         "toxicity.manual.user":current_user.username
        #         }
        # }
        {"$push":{
            "toxicity.manual_labels":{
                'user':current_user.username,
                'timestamp':datetime.now(),
                'label':reason,
                'is_toxic':score
            },
        }
        }
        )
    if not r:
        flash(str(eid)+" not found in "+table, category='error')
        return redirect(request.referrer)
    flash(str(eid)+" updated", category='info')
    return redirect(request.referrer)

        #return str(eid)+" not found in "+table
    # return str(eid)+" updated"

    # flash('Labeled tw_id: %s' % tw_id, category='info')
    #     return redirect(request.referrer)
    #     # return str(tw_id) + " updated"
    # flash("Label \"" + body + "\" for user " + str(tw_id) + " already exists", category='error')
    # return redirect(request.referrer)



@app.route('/list_toxic')
@login_required
def list_toxic():
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=current_user.username).first()

    # Properties of the pagination object include: 
    # iter_pages, next, prev, has_next, has_prev, next_num, prev_num
    paginated_issues = ToxicIssue.objects\
                        .get_toxic_issues()\
                        .order_by('-updated_at')\
                        .paginate(page=page, 
                                    per_page=app.config['RESULTS_PER_PAGE'])

    return render_template('toxic_issues.html', 
                            user=user,
                            version=app.config['VERSION'],
                            issues=paginated_issues,
                            deep_get=deep_get,
                            title='Toxic issues')


def add_toxicity_label_buttons(label_buttons, table, eid):
    label_buttons.setdefault(eid, [])
    for l in app.config['TOXICITY_LABELS']:
        d = {'url':'/toxiclabel/%s/%s/%s' % (table, eid, l[1]), 'name':l[0]}
        label_buttons[eid].append(d)
    return label_buttons


def get_toxicity_labels(labels, table, eid):
    labels.setdefault(eid, [])
    r = pmongo.db[table].find_one({"_id":ObjectId(eid)})
    if r:
        labels[eid].extend(r.get('toxicity',{}).get('manual_labels',[]))
    return labels




@app.route('/issue/<issueid>')
def show_issue(issueid, commentid=0):
    '''issueid must be a string'''
    issue = Issue.objects\
                .get_or_404(_id=ObjectId(issueid))
    tissue = ToxicIssue.objects\
                .get_or_404(_id=ObjectId(issueid))
    
    toxicity_labels = {}
    toxicity_labels = get_toxicity_labels(toxicity_labels, 'christian_toxic_issues', issueid)

    toxicity_label_buttons = {}
    toxicity_label_buttons = add_toxicity_label_buttons(toxicity_label_buttons, 'christian_toxic_issues', issueid)
    
    title = '{0}/{1}#{2}'.format(issue['owner'], issue['repo'], issue['number'])

    # flash('owner:' + issue['owner'] + ' ' + 'repo:' + issue['repo'] + ' ' + 'number:' + str(issue['number']))

    # comments = IssueComment.objects\
    #                 .get_comments(issue['owner'], issue['repo'], issue['number'])\
    #                 .order_by('updated_at')
    comments_cursor = pmongo.db.issue_comments.find({'owner':issue['owner'],
                                                'repo':issue['repo'],
                                                'issue_id':issue['number']})
    # toxic_comments = ToxicIssueComment.objects\
    #                 .get_comments(issue['owner'], issue['repo'], issue['number'])\
    #                 .order_by('updated_at')

    comments = []
    for comment in comments_cursor:
        comment['actual_id'] = comment['_id']
        tcomment = pmongo.db.christian_toxic_issue_comments.find_one({'_id':comment['_id']})
        
        toxicity_labels = get_toxicity_labels(toxicity_labels, 'christian_toxic_issue_comments', str(comment['_id']))

        toxicity_label_buttons = add_toxicity_label_buttons(toxicity_label_buttons, 'christian_toxic_issue_comments', comment['_id'])

        # tcomment = ToxicIssueComment.objects\
        #                 .get_or_404(_id=comment['_id'])
        if tcomment:
            if 'toxicity' in tcomment:
                comment['toxicity'] = tcomment['toxicity']

    #     # 	c["labels"] = label_buttons("/label/comment/", c)
        comments += [comment]

    # flash(toxicity_labels)

	# return render_template('./issue.html', issue=issue, tissue=tissue, is_toxic=is_toxic, comments = comments, render_label_buttons=render_label_buttons)
    return render_template('issue.html', 
                            issueid=issueid,
                            issue=issue, 
                            tissue=tissue, 
                            comments=comments,
                            # tcomments=tcomments,
                            is_toxic=is_toxic,
                            toxic_labels=toxicity_labels,
                            toxic_label_buttons=toxicity_label_buttons,
                            version=app.config['VERSION'],
                            title=title)

