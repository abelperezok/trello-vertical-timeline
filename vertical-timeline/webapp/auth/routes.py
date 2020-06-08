from flask import Blueprint, render_template, request, session, url_for, redirect, current_app
from flask_login import login_user, login_required, logout_user, current_user
from webapp import aws_auth
from webapp.models import User


auth = Blueprint('auth', __name__)

@auth.route('/session_expired')
def session_expired():
    session.clear()
    return 'your session has expired, please log in again <a href="' + url_for('auth.login', _external=True) + '">here</a>'

# go to cognito UI
@auth.route('/login')
def login():
    aws_auth.redirect_url = url_for('auth.aws_cognito_redirect', _external=True)
    return redirect(aws_auth.get_sign_in_url())


# return from cognito UI -> go to private
@auth.route('/aws_cognito_redirect')
def aws_cognito_redirect():
    access_token = aws_auth.get_access_token(request.args)
    aws_auth.token_service.verify(access_token)
    claims = aws_auth.token_service.claims
    session['claims'] = claims
    user = User(claims['username'])
    login_user(user)

    return redirect(url_for('trello.account'))


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('main.home'))

