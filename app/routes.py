from flask import render_template, flash, redirect, url_for, abort
from flask import request, send_from_directory
from werkzeug.urls import url_parse
from app import app
from app.forms import LoginForm, RegistrationForm
from app.models import User
from app.forms import ResetPasswordRequestForm
from app.forms import ResetPasswordForm
from app.flemail import send_password_reset_email
from flask_login import current_user, login_user, logout_user, login_required
import json



@app.route('/twuploads/<path:tw_filename>')
def download_tw(tw_filename):
    return send_from_directory(app.config['FOLDER_TW'], tw_filename, as_attachment=True)


@app.route('/ghuploads/<path:gh_filename>')
def download_gh(gh_filename):
    return send_from_directory(app.config['FOLDER_GH'], gh_filename, as_attachment=True)


@app.route('/cv2uploads/<path:tw_gh_filename>')
def download_tw_gh(tw_gh_filename):
    return send_from_directory(app.config['FOLDER_TW_GH'], tw_gh_filename, as_attachment=True)


@app.template_filter('tojson_pretty')
def to_pretty_json(value):
    return json.dumps(value, 
                    indent=4, separators=(',', ': '))
                    # sort_keys=True,


@app.route('/')
@app.route('/index')
@login_required
def index():
    user = User.query.filter_by(username=current_user.username).first()

    return render_template('index.html', 
                            user=user,
                            title='Home')



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