from flask import Blueprint, render_template, flash, redirect, request, url_for
from flask_login import current_user, login_user, login_required, logout_user
from web.models import User
from web.forms import LoginForm
from web.utils import get_google_provider_cfg
from web import db

from oauthlib.oauth2 import WebApplicationClient
import requests
import json
import os

login_template = Blueprint('login', __name__, template_folder='../templates')
client = WebApplicationClient(os.environ.get("GOOGLE_CLIENT_ID", None))


@login_template.route('/login', methods=['GET', 'POST'])
def login():
    """Page for login."""
    if current_user.is_authenticated:
        return redirect('/')

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Check if the username exists and the password is correct.
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login.login'))

        # Use utility function from flask_login.
        login_user(user)
        return redirect('/')

    return render_template('login.html', form=form)


@login_template.route('/login/google')
def login_google():
    google_provider_cfg = get_google_provider_cfg()

    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/authorized",
        scope=["email", "profile"],
    )
    return redirect(request_uri)


@login_template.route("/login/google/authorized")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(os.environ.get("GOOGLE_CLIENT_ID", None), os.environ.get("GOOGLE_CLIENT_SECRET", None)),
    )
    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        users_email = userinfo_response.json()["email"]
    else:
        return "User email not available or not verified by Google.", 400

    user = User.query.filter_by(email=users_email).first()

    if not user:
        user = User(email=users_email, is_admin=True)
        db.session.add(user)
        db.session.commit()

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect('/')


@login_template.route('/logout')
def logout():
    """Page for logout."""
    logout_user()
    return redirect('/')
