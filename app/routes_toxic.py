"""
Foo
"""
from flask import render_template, flash, redirect, url_for, abort
from flask import request
from werkzeug.urls import url_parse
from flask_paginate import Pagination, get_page_parameter, get_page_args
from flask_login import current_user, login_required
from app import app
from app import db, pmongo
from app.forms import LabelForm
from app.models import User
from app.utils import is_toxic
from datetime import datetime
from bson.objectid import ObjectId

# Sophie's handpicked list of PR ids 
from app.survey import survey

from app.queries import query_predicted_issues_all, \
                    query_predicted_issues_w_comments, \
                    query_annotations, \
                    query_annotations_toxic, \
                    query_individual_annotations, \
                    query_tolabel, \
                    query_predicted_prs_all, \
                    query_predicted_prs_w_comments, \
                    query_predicted_prs_w_review_comments, \
                    query_stratified, \
                    query_survey, \
                    query_closed



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



def get_label_buttons(label_buttons, endpoint, labels, collection, eid):
    """
    Creates endpoints with the prefix 'endpoint' to assign qualitative 
    analysis codes to a given document 'eid' in a given 'collection'. 
    The codes are taken from 'labels' (typically part of the app config).
    Appends the new endpoints to an existing dictionary 'label_buttons'.
    """
    label_buttons.setdefault(eid, [])
    for l in labels:
        d = {'url':'/%s/%s/%s/%s' % (endpoint, collection, eid, l[1]), 
            'name':l[0]}
        label_buttons[eid].append(d)
    return label_buttons



def get_labels(labels, collection, prefix, header, eid):
    """
    Retrieves all the unique labels of type 'header' (e.g., 
    qualitative_analysis_labels) nested under 'prefix' (e.g., 
    'toxicity'), that have been assigned to a given document
    'eid' in a given 'collection' (e.g., christian_toxic_issues).
    Appends the labels to an existing dictionary 'labels'.
    """
    labels.setdefault(eid, [])
    r = pmongo.db[collection].find_one({"_id":ObjectId(eid)})
    if r:
        llist = r.get(prefix, {}).get(header,[])
        seen = {}
        for label in llist:
            if not seen.get((label['user'], label['label']), False):
                labels[eid].append(label)
                seen[(label['user'], label['label'])] = True
    return labels



def get_label_buttons_from_db(label_buttons, endpoint, labels, collection, eid):
    """
    Creates endpoints with the prefix 'endpoint' to assign qualitative 
    analysis codes to a given document 'eid' in a given 'collection'. 
    The codes are taken from the database (so they can change dynamically).
    Appends the new endpoints to an existing dictionary 'label_buttons'.
    """
    label_buttons.setdefault(eid, [])
    # The 'labels' argument is not currently used
    labels = [l for l in pmongo.db['bogdan_toxic_qualitative_analysis'].find()]

    for l in labels:
        d = {'url':'/%s/%s/%s/%s' % (endpoint, collection, eid, l['label_sanitized']),
            'name':l['label_sanitized']}
        label_buttons[eid].append(d)
    return label_buttons




@app.route('/pushbacklabel/<table>/<eid>/<label>')
@login_required
def label_pushback_entry(table, eid, label):
    score = 0
    is_pushback = False
    if label=="pushback":
        score = 1
        is_pushback = True
    reason = label
    r = pmongo.db[table].find_one_and_update(
        {"_id":ObjectId(eid)},
        {"$push":
            {"pushback.manual_labels":
                {'user':current_user.username,
                'timestamp':datetime.now(),
                'label':reason,
                'is_pubshback':score},
            },
        "$set":
            {"has_pb_label":True,
            "is_labeled_pushback":is_pushback}
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
        r1 = pmongo.db['christian_toxic_issues'].find_one_and_update(
            {"_id":ObjectId(issue['_id'])},
            {"$set":{
                "has_pb_labeled_comment":True,
                "has_labeled_pb_comment":is_pushback
                },
            "$push": { "pushback.manual_labeled_comments": { 'user': current_user.username, 'is_pushback': score } }
            }
        )
        r2 = pmongo.db['christian_toxic_pull_requests'].find_one_and_update(
            {"_id":ObjectId(issue['_id'])},
            {"$set":{
                "has_pb_labeled_comment":True,
                "has_labeled_pb_comment":is_pushback
                },
            "$push": { "pushback.manual_labeled_comments": { 'user':
            current_user.username, 'is_pushback': score } }
            }
        )
        if not r1 and not r2:
            flash("Parent issue / PR for comment "+str(eid)+" not found", category='error')
            return redirect(request.referrer)

    # if review comment, update parent PR
    if table == 'christian_toxic_pull_request_comments':
        comment = pmongo.db['pull_request_comments'].find_one({'_id':ObjectId(eid)})
        issue = pmongo.db['pull_requests'].find_one({'owner':comment['owner'],
                                        'repo':comment['repo'],
                                        'number':comment['pullreq_id']})
        r1 = pmongo.db['christian_toxic_issues'].find_one_and_update(
            {"_id":ObjectId(issue['_id'])},
            {"$set":{
                "has_pb_labeled_comment":True,
                "has_labeled_pb_comment":is_pushback
                },
            "$push": { "pushback.manual_labeled_comments": { 'user': current_user.username, 'is_pushback': score } }
            }
        )
        r2 = pmongo.db['christian_toxic_pull_requests'].find_one_and_update(
            {"_id":ObjectId(issue['_id'])},
            {"$set":{
                "has_pb_labeled_comment":True,
                "has_labeled_pb_comment":is_pushback
                },
            "$push": { "pushback.manual_labeled_comments": { 'user': current_user.username, 'is_pushback': score } }
            }
        )
        if not r1 and not r2:
            flash("Parent issue / PR for comment "+str(eid)+" not found", category='error')
            return redirect(request.referrer)



    flash(str(eid)+" updated", category='info')
    return redirect(request.referrer)


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
        r1 = pmongo.db['christian_toxic_issues'].find_one_and_update(
            {"_id":ObjectId(issue['_id'])},
            {"$set":{
                "has_labeled_comment":True,
                "has_labeled_toxic_comment":is_toxic
                },
            "$push": { "toxicity.manual_labeled_comments": { 'user': current_user.username, 'is_toxic': score } }
            }
        )
        r2 = pmongo.db['christian_toxic_pull_requests'].find_one_and_update(
            {"_id":ObjectId(issue['_id'])},
            {"$set":{
                "has_labeled_comment":True,
                "has_labeled_toxic_comment":is_toxic
                },
            "$push": { "toxicity.manual_labeled_comments": { 'user': current_user.username, 'is_toxic': score } }
            }
        )
        if not r1 and not r2:
            flash("Parent issue / PR for comment "+str(eid)+" not found", category='error')
            return redirect(request.referrer)

    # if review comment, update parent PR
    if table == 'christian_toxic_pull_request_comments':
        comment = pmongo.db['pull_request_comments'].find_one({'_id':ObjectId(eid)})
        issue = pmongo.db['pull_requests'].find_one({'owner':comment['owner'],
                                        'repo':comment['repo'],
                                        'number':comment['pullreq_id']})
        r1 = pmongo.db['christian_toxic_issues'].find_one_and_update(
            {"_id":ObjectId(issue['_id'])},
            {"$set":{
                "has_labeled_comment":True,
                "has_labeled_toxic_comment":is_toxic
                },
            "$push": { "toxicity.manual_labeled_comments": { 'user': current_user.username, 'is_toxic': score } }
            }
        )
        r2 = pmongo.db['christian_toxic_pull_requests'].find_one_and_update(
            {"_id":ObjectId(issue['_id'])},
            {"$set":{
                "has_labeled_comment":True,
                "has_labeled_toxic_comment":is_toxic
                },
            "$push": { "toxicity.manual_labeled_comments": { 'user': current_user.username, 'is_toxic': score } }
            }
        )
        if not r1 and not r2:
            flash("Parent issue / PR for comment "+str(eid)+" not found", category='error')
            return redirect(request.referrer)



    flash(str(eid)+" updated", category='info')
    return redirect(request.referrer)




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






@app.route('/list/<what>', methods=['GET', 'POST'])
@login_required
def list_issues(what):
    with_total = False
    order = []
    disable_coding = False
    is_pr = False
    post_type = "issue"

    top_collection = 'issues'
    toxic_top_collection = 'christian_toxic_issues'
    comments_collection = 'issue_comments'
    toxic_comments_collection = 'christian_toxic_issue_comments'
    review_comments_collection = 'pull_request_comments'
    toxic_review_comments_collection = 'christian_toxic_pull_request_comments'
    prediction_labels = 'TOXICITY_LABELS'
    doc_prefix = 'toxicity'
    endpoint_prefix = 'toxiclabel'
    definition = ''
    task_type = 'toxicity'

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
        disable_coding = True
    elif what == 'classifier_prs_all':
        q = query_predicted_prs_all
        is_pr = True
    elif what == 'classifier_prs_w_comments':
        q = query_predicted_prs_w_comments
        is_pr = True
    elif what == 'classifier_prs_w_review_comments':
        q = query_predicted_prs_w_review_comments
        is_pr = True
    elif what == 'sophie_sampled_prs':
        q = query_tolabel(current_user.username)
        is_pr = True
        toxic_top_collection = 'christian_toxic_pull_requests'
        top_collection = 'pull_requests'
    elif what == 'sophie_survey_prs':
        q = query_survey(current_user.username)
        is_pr = True
        toxic_top_collection = 'christian_toxic_pull_requests'
        top_collection = 'pull_requests'
        prediction_labels = 'PUSHBACK_LABELS'
        doc_prefix = 'pushback'
        definition = 'Definition: the perception of unnecessary interpersonal conflict in code review while a reviewer is blocking a change request'
        task_type = 'pushback'
        endpoint_prefix = 'pushbacklabel'
    elif what == 'sophie_closed':
        q = query_closed(current_user.username)
        is_pr = True
        toxic_top_collection = 'pull_requests'
        top_collection = 'pull_requests'
        prediction_labels = 'PUSHBACK_LABELS'
        doc_prefix = 'pushback'
        definition = 'Definition: the perception of unnecessary interpersonal conflict in code review while a reviewer is blocking a change request'
        task_type = 'pushback'
        endpoint_prefix = 'pushbacklabel'
    if is_pr:
        post_type = "pr"


    page, per_page, offset = get_page_details()
    
    cursor = pmongo.db[toxic_top_collection].find(q, sort=order)

    issues_for_render = cursor.skip(offset).limit(per_page)

    form = LabelForm()
    if form.validate_on_submit():
        element_id = form.element_id.data
        element_type = form.element_type.data
        if element_type == 'issue':
            table = 'christian_toxic_issues'
        elif element_type == 'issue_comment':
            table = 'christian_toxic_issue_comments'
        elif element_type == 'pull_request':
            table = 'christian_toxic_pull_requests'
        elif element_type == 'pull_request_comment':
            table = 'christian_toxic_issue_comments'
        else:
            table = 'christian_toxic_pull_request_comments'
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
        issue = pmongo.db[top_collection]\
                .find_one({'_id':ObjectId(tissue['_id'])})
        issues[str(tissue['_id'])] = issue

        toxicity_labels = get_labels(toxicity_labels,
                                        toxic_top_collection, 
                                        doc_prefix, 
                                        'manual_labels',
                                        str(tissue['_id']))
        toxicity_label_buttons = get_label_buttons(toxicity_label_buttons,
                                        endpoint_prefix,
                                        app.config[prediction_labels],
                                        toxic_top_collection,
                                        str(tissue['_id']))

        if not disable_coding:
            qualitative_labels = get_labels(qualitative_labels,
                                            toxic_top_collection,
                                            doc_prefix,
                                            'qualitative_analysis_labels',
                                            str(tissue['_id']))
            qualitative_label_buttons = get_label_buttons_from_db(qualitative_label_buttons,
                                            'qualitativelabel',
                                            None, # not used currently
                                            toxic_top_collection,
                                            str(tissue['_id']))

        issue_titles[str(tissue['_id'])] = '{0}/{1}#{2}'.format(issue['owner'],
                                                    issue['repo'],
                                                    issue['number'])

        comments_cursor = pmongo.db[comments_collection]\
            .find({'owner':issue['owner'],
                    'repo':issue['repo'],
                    'issue_id':issue['number']})

        comments.setdefault(str(issue['_id']), [])
        for comment in comments_cursor:
            tcomment = pmongo.db[toxic_comments_collection]\
                .find_one({'_id':ObjectId(comment['_id'])})
            toxicity_labels = get_labels(toxicity_labels,
                                            toxic_comments_collection,
                                            doc_prefix,
                                            'manual_labels',
                                            str(comment['_id']))
            toxicity_label_buttons = get_label_buttons(toxicity_label_buttons,
                                            endpoint_prefix,
                                            app.config[prediction_labels],
                                            toxic_comments_collection,
                                            str(comment['_id']))

            if not disable_coding:
                qualitative_labels = get_labels(qualitative_labels,
                                            toxic_comments_collection,
                                            doc_prefix,
                                            'qualitative_analysis_labels',
                                            str(comment['_id']))
                qualitative_label_buttons = get_label_buttons_from_db(qualitative_label_buttons,
                                            'qualitativelabel',
                                            None, # not used currently
                                            toxic_comments_collection,
                                            str(comment['_id']))

            if tcomment:
                if doc_prefix in tcomment:
                    comment[doc_prefix] = tcomment[doc_prefix]

            comments[str(tissue['_id'])] += [comment]


        # PR review comments
        if is_pr:
            review_comments_cursor = pmongo.db[review_comments_collection]\
                .find({'owner':issue['owner'],
                        'repo':issue['repo'],
                        'pullreq_id':issue['number']})

            comments.setdefault(str(issue['_id']), [])
            for comment in review_comments_cursor:
                tcomment = pmongo.db[toxic_review_comments_collection]\
                    .find_one({'_id':ObjectId(comment['_id'])})
                toxicity_labels = get_labels(toxicity_labels,
                                            toxic_review_comments_collection,
                                            doc_prefix,
                                            'manual_labels',
                                            str(comment['_id']))
                toxicity_label_buttons = get_label_buttons(toxicity_label_buttons,
                                            endpoint_prefix,
                                            app.config[prediction_labels],
                                            toxic_review_comments_collection,
                                            str(comment['_id']))

                if not disable_coding:
                    qualitative_labels = get_labels(qualitative_labels,
                                                toxic_review_comments_collection,
                                                doc_prefix,
                                                'qualitative_analysis_labels',
                                                str(comment['_id']))
                    qualitative_label_buttons = get_label_buttons_from_db(qualitative_label_buttons,
                                                'qualitativelabel',
                                                None, # not used currently
                                                toxic_review_comments_collection,
                                                str(comment['_id']))

                if tcomment:
                    if doc_prefix in tcomment:
                        comment[doc_prefix] = tcomment[doc_prefix]

                comments[str(tissue['_id'])] += [comment]

            
            comments[str(issue['_id'])] = sorted(comments[str(issue['_id'])], key=lambda e: e['created_at'])



    cursor.rewind()
    issues_for_render = cursor.skip(offset).limit(per_page)

    if with_total:
        total = cursor.count()
    else:
        total = 12345678

    pagination = get_pagination(page, per_page, 'per_page', offset, total)

    return render_template('toxic_issues2.html',
                            task_type = task_type,
                            definition=definition,
                            tissues=issues_for_render,
                            issues=issues,
                            post_type=post_type,
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

