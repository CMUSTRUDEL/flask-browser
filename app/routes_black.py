from flask import render_template, flash, redirect, url_for, abort
from flask import request, send_from_directory
from werkzeug.urls import url_parse
from app import app
from app import db
from app.models import User, GHProfile, GHPhotoLabel, GHBlackUser
from flask_login import current_user, login_required
from datetime import datetime


@app.route('/blabel/<gh_id>/<body>')
@login_required
def label_black(gh_id, body):
    user = User.query.filter_by(username=current_user.username).first()
    # I already have this label in the database
    exists = GHPhotoLabel.query\
        .filter_by(ght_id=gh_id)\
        .filter_by(user_id=user.id)\
        .filter_by(text=body)\
        .scalar() is not None
    if not exists:
        label = GHPhotoLabel(
                    ght_id=gh_id,
                    user_id=user.id,
                    text=body,
                    timestamp=datetime.now()
                )
        db.session.add(label)
        db.session.commit()
        flash('Labeled ght_id: %s' % gh_id, category='info')
        return redirect(request.referrer)

    flash("Label \"" + body + "\" for user " + str(gh_id) + " already exists", category='error')
    return redirect(request.referrer)



@app.route('/black')
@login_required
def black():
    page = request.args.get('page', 1, type=int)

    gh_users = GHBlackUser\
        .query\
        .order_by(GHBlackUser.probability_calibrated.desc())\
        .paginate(page, app.config['RESULTS_PER_PAGE'], True)

    gh_labels = {gh_user.ght_id: GHPhotoLabel.query\
            .filter(GHPhotoLabel.ght_id==gh_user.ght_id)\
            .all() for gh_user in gh_users.items}

    gh_label_buttons = {}
    for gh_user in gh_users.items:
        gh_label_buttons.setdefault(gh_user.ght_id, [])
        for l in app.config['PHOTO_GH_LABELS']:
            d = {'url':'/blabel/%s/%s' % (gh_user.ght_id, l[1]), 'name':l[0]}
            gh_label_buttons[gh_user.ght_id].append(d)

    return render_template('black.html', 
                            title='GitHub profile pics', 
                            gh_users=gh_users, 
                            gh_labels=gh_labels,
                            gh_label_buttons=gh_label_buttons)
    

@app.route('/black_annotations')
@login_required
def black_annotations():
    page = request.args.get('page', 1, type=int)

    annotated_users = set([u.ght_id for u in GHPhotoLabel.query.all()])
    
    gh_users = GHBlackUser\
        .query\
        .filter(GHBlackUser.ght_id.in_(annotated_users))\
        .paginate(page, app.config['RESULTS_PER_PAGE'], True)

    gh_labels = {gh_user.ght_id: GHPhotoLabel.query\
            .filter(GHPhotoLabel.ght_id==gh_user.ght_id)\
            .all() for gh_user in gh_users.items}

    gh_label_buttons = {}
    for gh_user in gh_users.items:
        gh_label_buttons.setdefault(gh_user.ght_id, [])
        for l in app.config['PHOTO_GH_LABELS']:
            d = {'url':'/blabel/%s/%s' % (gh_user.ght_id, l[1]), 'name':l[0]}
            gh_label_buttons[gh_user.ght_id].append(d)

    return render_template('black.html', 
                            title='GitHub profile pics', 
                            gh_users=gh_users, 
                            gh_labels=gh_labels,
                            gh_label_buttons=gh_label_buttons)
    

