from flask import render_template, flash, redirect, url_for, abort
from flask import request
from werkzeug.urls import url_parse

from app import app
from app import db
from app.forms import LoginForm, RegistrationForm
from app.models import User, GHProfile, TwitterUser, TwitterUserLabel
from app.forms import ResetPasswordRequestForm
from app.forms import ResetPasswordForm
from app.email import send_password_reset_email

from flask_login import current_user, login_user, logout_user, login_required

from flask_admin import Admin, expose, BaseView
from flask_admin.contrib import sqla
from flask_admin.helpers import get_form_data
from flask_admin.babel import gettext
from markupsafe import Markup

from datetime import datetime


# def _format_pay_now(model):

#     if model.is_confirmed:
#         return 'Valid'

#     # render a form with a submit button, include a hidden field for the user id
#     # note how checkout_view method is exposed as a route below
#     checkout_url = url_for('.checkout_view')

#     _html = '''
#         <form action="{checkout_url}" method="POST">
#             <input id="tw_id" name="tw_id"  type="hidden" value="{tw_id}">
#             <button type='submit'>Confirm match</button>
#         </form
#     '''.format(checkout_url=checkout_url, tw_id=model.tw_id)

#     return Markup(_html)

# # column_formatters = {
# #     'Pay Now': _format_pay_now
# # }

# @expose('checkout', methods=['POST'])
# def checkout_view(self):

#     return_url = self.get_url('.index_view')

#     form = get_form_data()

#     if not form:
#         flash(gettext('Could not get form from request.'), 'error')
#         return redirect(return_url)

#     # Form is an ImmutableMultiDict
#     student_id = form['student_id']

#     # Get the model from the database
#     model = self.get_one(student_id)

#     if model is None:
#         flash(gettext('Student not not found.'), 'error')
#         return redirect(return_url)

#     # process the model
#     model.is_paid = True

#     try:
#         self.session.commit()
#         flash(gettext('Student, ID: {student_id}, set as paid'.format(student_id=student_id)))
#     except Exception as ex:
#         if not self.handle_view_exception(ex):
#             raise

#         flash(gettext('Failed to set student, ID: {student_id}, as paid'.format(student_id=student_id), error=str(ex)), 'error')

#     return redirect(return_url)



@app.route('/label/<tw_id>/<body>')
@login_required
def label_entry(tw_id, body):
    page = request.args.get('page', 1, type=int)
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

labels = [
            ["Confirm","valid"], 
            ["Invalid", "invalid"]
        ]
def label_buttons(link, tw_id):
    # current_label = deep_get(titem,"toxicity.manual.reason")
    # current_label = 
    result = []
    for l in labels:
        # flash({'url':link + tw_id + "/" + l[1],
        #             'name':l[0]})
        result += {'url':link + tw_id + "/" + l[1],
                    'name':l[0]}
    return result

# def render_label_buttons(label_buttons):
#     result = ""
#     for idx, b in enumerate(label_buttons):
#         result += "<a href=\""+b[0]+"\">"+b[1]+"</a>"
#         if idx < len(label_buttons)-1:
#             result += "<br>"
#         # result += "<a href=\""+b[0]+"\" class=\"labelbtn labelbtn_"+str(b[2])+"\">"+b[1]+"</a> "
#     return result


@app.route('/')
@app.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=current_user.username).first()

    tw_users = TwitterUser.query\
        .join(GHProfile, TwitterUser.ght_id==GHProfile.id)\
        .paginate(page, app.config['RESULTS_PER_PAGE'], False)

    tw_labels = {tw_user.tw_id: TwitterUserLabel.query\
            .filter(TwitterUserLabel.tw_id==tw_user.tw_id)\
            # .filter(TwitterUserLabel.user_id==user.id)
            .all() for tw_user in tw_users.items}

    tw_label_buttons = {}
    for tw_user in tw_users.items:
        tw_label_buttons.setdefault(tw_user.tw_id, [])
        for l in labels:
            d = {'url':'/label/%s/%s' % (tw_user.tw_id, l[1]), 'name':l[0]}
            tw_label_buttons[tw_user.tw_id].append(d)

    # tw_users = current_user.grab_data()\
    #     .paginate(page, app.config['RESULTS_PER_PAGE'], False)
    next_url = url_for('index', page=tw_users.next_num) \
        if tw_users.has_next else None
    prev_url = url_for('index', page=tw_users.prev_num) \
        if tw_users.has_prev else None
    return render_template('index.html', 
                            title='Home', 
                            tw_users=tw_users.items, 
                            tw_labels=tw_labels,
                            tw_label_buttons=tw_label_buttons,
                            # render_label_buttons=render_label_buttons,
                            next_url=next_url,
                            prev_url=prev_url)
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # if current_user.is_authenticated:
        # return redirect(url_for('index'))
    # prevent non-admins from accessing the page
    if not current_user.is_admin:
        abort(403)
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
                username=form.username.data, 
                email=form.email.data
                )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('New registered user: %s' % form.username.data)
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
@login_required
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
@login_required
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)