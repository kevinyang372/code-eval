from flask import Blueprint, render_template, flash, redirect, request, url_for
from flask_login import current_user, login_user, login_required, logout_user
from web.models import User
from web.forms import LoginForm

login_template = Blueprint('login', __name__, template_folder='../templates')


@login_template.route('/login', methods=['GET', 'POST'])
def login():
    """Page for login"""
    if current_user.is_authenticated:
        return redirect('/')

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login.login'))
        login_user(user)
        return redirect('/')
    return render_template('login.html', form=form)


@login_template.route('/logout')
def logout():
    logout_user()
    return redirect('/')
