from flask import render_template, flash, redirect, session, url_for, abort
from flask import request
from werkzeug.urls import url_parse

from app import app
from app import db, mongo, pmongo
from app.models import User, GHProfile, TwitterUser, TwitterUserLabel, GHUser, GHUserPrivate
from app.models import Issue, IssueComment, ToxicIssue, ToxicIssueComment
from app.forms import ResetPasswordRequestForm
from app.forms import ResetPasswordForm
from app.flemail import send_password_reset_email

from flask_login import current_user, login_user, logout_user, login_required

from datetime import datetime
from .utils import deep_get, is_toxic
from bson.objectid import ObjectId

import json


@app.route('/label/<tw_id>/<body>')
@login_required
def label_entry(tw_id, body):
    # page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=current_user.username).first()
    # I already have this label in the database
    exists = TwitterUserLabel.query\
        .filter_by(tw_id=tw_id)\
        .filter_by(user_id=user.id)\
        .filter_by(text=body)\
        .scalar() is not None
    if not exists:
        label = TwitterUserLabel(
                    tw_id=tw_id,
                    user_id=user.id,
                    text=body,
                    timestamp=datetime.now()
                )
        db.session.add(label)
        db.session.commit()
        flash('Labeled tw_id: %s' % tw_id, category='info')
        return redirect(request.referrer)
        # return str(tw_id) + " updated"
    flash("Label \"" + body + "\" for user " + str(tw_id) + " already exists", category='error')
    return redirect(request.referrer)


@app.route('/twitter/<what>')
@login_required
def twitter(what):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=current_user.username).first()

    if what == 'all':
        tw_users = TwitterUser.query\
            .join(GHProfile, TwitterUser.ght_id==GHProfile.id)\
            .paginate(page, app.config['RESULTS_PER_PAGE'], False)
    elif what == 'different_screen_name':
        tw_users = TwitterUser.query\
            .join(GHUser, TwitterUser.ght_id==GHUser.id)\
            .join(GHUserPrivate, GHUser.login==GHUserPrivate.login)\
            .filter(TwitterUser.tw_img_url!=None)\
            .paginate(page, app.config['RESULTS_PER_PAGE'], False)

    tw_labels = {tw_user.tw_id: TwitterUserLabel.query\
            .filter(TwitterUserLabel.tw_id==tw_user.tw_id)\
            # .filter(TwitterUserLabel.user_id==user.id)
            .all() for tw_user in tw_users.items}

    tw_label_buttons = {}
    for tw_user in tw_users.items:
        tw_label_buttons.setdefault(tw_user.tw_id, [])
        for l in app.config['TW_GH_LABELS']:
            d = {'url':'/label/%s/%s' % (tw_user.tw_id, l[1]), 'name':l[0]}
            tw_label_buttons[tw_user.tw_id].append(d)

    # tw_users = current_user.grab_data()\
    #     .paginate(page, app.config['RESULTS_PER_PAGE'], False)
    # next_url = get_next_url('twitter', tw_users)
    # prev_url = get_prev_url('twitter', tw_users)

    # url_for('twitter', page=tw_users.next_num) \
    #     if tw_users.has_next else None
    # prev_url = url_for('twitter', page=tw_users.prev_num) \
    #     if tw_users.has_prev else None
    return render_template('twitter_local.html', 
                            title='Twitter', 
                            tw_users=tw_users, 
                            tw_labels=tw_labels,
                            tw_label_buttons=tw_label_buttons,
                            cv2_data=cv2_data)  # session.get('cv2_data'))
                            # render_label_buttons=render_label_buttons,
                            # next_url=next_url,
                            # prev_url=prev_url)
    

