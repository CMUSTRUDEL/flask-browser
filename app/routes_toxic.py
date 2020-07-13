from flask import render_template, flash, redirect, url_for, abort
from flask import request
from werkzeug.urls import url_parse
from flask_paginate import Pagination, get_page_parameter, get_page_args

from app import app
from app import db, mongo, pmongo
from app.models import User
from app.models import Issue, IssueComment, ToxicIssue, ToxicIssueComment
from app.forms import LabelForm
from flask_login import current_user, login_required

from datetime import datetime
from app.utils import is_toxic
from bson.objectid import ObjectId

import json

from mongoengine.queryset.visitor import Q

from app.queries import query_predicted_issues_all, \
                    query_predicted_issues_w_comments, \
                    query_annotations, \
                    query_annotations_toxic, \
                    query_individual_annotations, query_tolabel



def get_page_details():
    page = int(request.args.get('page', 1))
    per_page = app.config['PER_PAGE_PARAMETER']
    offset = (page - 1) * per_page
    return (page, per_page, offset)


def get_pagination(page, per_page, per_page_parameter, offset, total):
    return Pagination(page=page,
                    per_page=per_page,
                    per_page_parameter=per_page_parameter,
                    offset=offset,
                    prev_label="Previous",
                    next_label="Next",
                    total=total,
                    css_framework='bootstrap3',
                    search=False)


def add_toxicity_label_buttons(label_buttons, table, eid):
    label_buttons.setdefault(eid, [])
    for l in app.config['TOXICITY_LABELS']:
        d = {'url':'/toxiclabel/%s/%s/%s' % (table, eid, l[1]), 'name':l[0]}
        label_buttons[eid].append(d)
    return label_buttons


def get_toxicity_labels(labels, table, collection, eid):
    labels.setdefault(eid, [])
    r = pmongo.db[table].find_one({"_id":ObjectId(eid)})
    if r:
        llist = r.get('toxicity',{}).get(collection,[])
        seen = {}
        for label in llist:
            if not seen.get((label['user'], label['label']), False):
                labels[eid].append(label)
                seen[(label['user'], label['label'])] = True
        # # old, shouldn't need these anymore:
        # reason = r.get('toxicity',{}).get('manual',{}).get('reason', None)
        # if reason is not None:
        #     labels[eid].append({'user':'christian', 'label':reason})
    return labels



@app.route('/toxiclabel/<table>/<eid>/<label>')
@login_required
def label_toxic_entry(table, eid, label):
    score = 0
    is_toxic = False
    if label=="toxic":
        score = 1
        is_toxic = True
    reason = label
    r = pmongo.db[table].find_one_and_update(
        {"_id":ObjectId(eid)},
        {"$push":
            {"toxicity.manual_labels":
                {'user':current_user.username,
                'timestamp':datetime.now(),
                'label':reason,
                'is_toxic':score},
            },
        "$set":
            {"is_labeled":True,
            "is_labeled_toxic":is_toxic}
        }
    )

    if not r:
        flash(str(eid)+" not found in "+table, category='error')
        return redirect(request.referrer)

    # if comment, update parent issue
    if table == 'christian_toxic_issue_comments':
        comment = pmongo.db['issue_comments'].find_one({'_id':ObjectId(eid)})
        issue = pmongo.db['issues'].find_one({'owner':comment['owner'],
                                        'repo':comment['repo'],
                                        'number':comment['issue_id']})
        r = pmongo.db['christian_toxic_issues'].find_one_and_update(
            {"_id":ObjectId(issue['_id'])},
            {"$set":{
                "has_labeled_comment":True,
                "has_labeled_toxic_comment":is_toxic
                },
            "$push": { "toxicity.manual_labeled_comments": { 'user': current_user.username } }
            }
        )
        if not r:
            flash("Parent issue for comment "+str(eid)+" not found", category='error')
            return redirect(request.referrer)

    flash(str(eid)+" updated", category='info')
    return redirect(request.referrer)



def get_qualitative_label_buttons(label_buttons, table, eid):
    label_buttons.setdefault(eid, [])
    labels = [l for l in pmongo.db['bogdan_toxic_qualitative_analysis'].find()]

    for l in labels:
        d = {'url':'/qualitativelabel/%s/%s/%s' % (table, eid, l['label_sanitized']),
            'name':l['label_sanitized']}
        label_buttons[eid].append(d)
    return label_buttons



@app.route('/qualitativelabel/<table>/<eid>/<label>')
@login_required
def add_code(table, eid, label):
    # flash(label)
    label_sanitized = '-'.join(label.lower().split())
    r = pmongo.db[table].find_one_and_update(
        {"_id":ObjectId(eid)},
        {"$push":
            {"toxicity.qualitative_analysis_labels":
                {'user':current_user.username,
                # 'timestamp':datetime.now(),
                'label':label,
                'label_sanitized':label_sanitized},
            },
        "$set":
            {"is_coded":True}
        }
    )
    if not r:
        flash(str(eid)+" not found in "+table, category='error')
        return redirect(request.referrer)

    # If comment, update parent issue
    if table == 'christian_toxic_issue_comments':
        comment = pmongo.db['issue_comments'].find_one({'_id':ObjectId(eid)})
        issue = pmongo.db['issues'].find_one({'owner':comment['owner'],
                                        'repo':comment['repo'],
                                        'number':comment['issue_id']})
        r = pmongo.db['christian_toxic_issues'].find_one_and_update(
            {"_id":ObjectId(issue['_id'])},
            {"$set":
                {"has_coded_comment":True}
            }
        )
        if not r:
            flash("Parent issue for comment "+str(eid)+" not found", category='error')
            return redirect(request.referrer)

    # Add label to list of labels
    code = pmongo.db['bogdan_toxic_qualitative_analysis'].find_one({'label':label,
                                                    'label_sanitized':label_sanitized})
    if not code:
        pmongo.db['bogdan_toxic_qualitative_analysis'].insert({'label':label,
                                                    'label_sanitized':label_sanitized})

    flash(str(eid)+" updated", category='info')
    return redirect(request.referrer)



#@app.route('/list/label_toxic')
#@login_required
#def label_toxic():


@app.route('/list/<what>', methods=['GET', 'POST'])
@login_required
def list_issues(what):
    with_total = False
    order = []
    if what == 'classifier_issues_w_comments':
        q = query_predicted_issues_w_comments
    elif what == 'classifier_issues_all':
        q = query_predicted_issues_all
    elif what == 'annotated_issues':
        q = query_annotations
        with_total = True
    elif what == 'annotated_issues_toxic':
        q = query_annotations_toxic
        with_total = True
    elif what == 'individual_annotated_issues':
        q = query_individual_annotations(current_user.username)
        with_total = True
    elif what == "label_toxic":
        q = query_tolabel(current_user.username)
        order = [("random", 1)]



    page, per_page, offset = get_page_details()
    print(q)
    cursor = pmongo.db['christian_toxic_issues'].find(q, sort=order)


    issues_for_render = cursor.skip(offset).limit(per_page)

    form = LabelForm()
    if form.validate_on_submit():
        element_id = form.element_id.data
        element_type = form.element_type.data
        if element_type == 'issue':
            table = 'christian_toxic_issues'
        else:
            table = 'christian_toxic_issue_comments'
        label = '-'.join(form.element_label.data.lower().split())
        submit_pressed = form.submit.data  # this will be True if Submit was pressed, False otherwise
        add_code(table, element_id, label)
        # do stuff
        return redirect(request.referrer)


    issues = {}
    toxicity_labels = {}
    toxicity_label_buttons = {}
    qualitative_labels = {}
    qualitative_label_buttons = {}
    issue_titles = {}
    comments = {}

    for tissue in issues_for_render:
        issue = pmongo.db['issues']\
                .find_one({'_id':ObjectId(tissue['_id'])})
        issues[str(tissue['_id'])] = issue

        toxicity_labels = get_toxicity_labels(toxicity_labels,
                                            'christian_toxic_issues',
                                            'manual_labels',
                                            str(tissue['_id']))
        toxicity_label_buttons = add_toxicity_label_buttons(toxicity_label_buttons,
                                            'christian_toxic_issues',
                                            str(tissue['_id']))
        qualitative_labels = get_toxicity_labels(qualitative_labels,
                                            'christian_toxic_issues',
                                            'qualitative_analysis_labels',
                                            str(tissue['_id']))
        qualitative_label_buttons = get_qualitative_label_buttons(qualitative_label_buttons,
                                            'christian_toxic_issues',
                                            str(tissue['_id']))

        issue_titles[str(tissue['_id'])] = '{0}/{1}#{2}'.format(issue['owner'],
                                                    issue['repo'],
                                                    issue['number'])

        comments_cursor = pmongo.db['issue_comments']\
            .find({'owner':issue['owner'],
                    'repo':issue['repo'],
                    'issue_id':issue['number']})

        comments.setdefault(str(issue['_id']), [])
        for comment in comments_cursor:
            tcomment = pmongo.db['christian_toxic_issue_comments']\
                .find_one({'_id':ObjectId(comment['_id'])})
            toxicity_labels = get_toxicity_labels(toxicity_labels,
                                                'christian_toxic_issue_comments',
                                                'manual_labels',
                                                str(comment['_id']))
            toxicity_label_buttons = add_toxicity_label_buttons(toxicity_label_buttons,
                                                'christian_toxic_issue_comments',
                                                str(comment['_id']))
            qualitative_labels = get_toxicity_labels(qualitative_labels,
                                            'christian_toxic_issue_comments',
                                            'qualitative_analysis_labels',
                                            str(comment['_id']))
            qualitative_label_buttons = get_qualitative_label_buttons(qualitative_label_buttons,
                                            'christian_toxic_issue_comments',
                                            str(comment['_id']))

            if tcomment:
                if 'toxicity' in tcomment:
                    comment['toxicity'] = tcomment['toxicity']

            comments[str(tissue['_id'])] += [comment]

    cursor.rewind()
    issues_for_render = cursor.skip(offset).limit(per_page)

    if with_total:
        total = cursor.count()
    else:
        total = 12345678

    pagination = get_pagination(page, per_page, 'per_page', offset, total)

    return render_template('toxic_issues2.html',
                            tissues=issues_for_render,
                            issues=issues,
                            comments=comments,
                            toxic_labels=toxicity_labels,
                            toxic_label_buttons=toxicity_label_buttons,
                            qualitative_labels=qualitative_labels,
                            qualitative_label_buttons=qualitative_label_buttons,
                            issue_titles=issue_titles,
                            pagination=pagination,
                            is_toxic=is_toxic,
                            version=app.config['VERSION'],
                            form=form)




# @app.route('/issue/<issueid>')
# def show_issue(issueid):
#     '''issueid must be a string'''

#     (issues_for_render,
#         issues,
#         all_comments,
#         toxicity_labels,
#         toxicity_label_buttons,
#         issue_titles,
#         total) = list_issues({"_id":ObjectId(issueid)}, 0, 1)

#     tissue = issues_for_render[0]
#     issue = issues[issueid]
#     title = issue_titles[issueid]
#     comments = all_comments[issueid]


#     return render_template('issue.html',
#                             issueid=issueid,
#                             issue=issue,
#                             tissue=tissue,
#                             comments=comments,
#                             is_toxic=is_toxic,
#                             toxic_labels=toxicity_labels,
#                             toxic_label_buttons=toxicity_label_buttons,
#                             version=app.config['VERSION'],
#                             title=title)
