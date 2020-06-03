from flask import session
from webapp import login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    claims = session['claims']
    user = User(claims['username'])
    user.claims = claims
    return user

class User(UserMixin):
    
    def __init__(self, username):
        self.username = username
        self.claims = None

    def get_id(self):
        return self.username