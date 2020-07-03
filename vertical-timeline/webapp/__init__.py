from flask import Flask, request, render_template, session, redirect, jsonify, url_for, escape
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

from flask_lambda import FlaskLambda
from flask_awscognito import AWSCognitoAuthentication

aws_auth = AWSCognitoAuthentication()
login_manager = LoginManager()
login_manager.login_view = "auth.session_expired"


def configure_app(app):

    app.config.from_pyfile('application.cfg', silent=True)

    # Initialize Plugins
    aws_auth.init_app(app)
    login_manager.init_app(app)


    with app.app_context():
        # Include our Routes
        from webapp.main.routes import main
        from webapp.auth.routes import auth
        from webapp.trello.routes import trello

        # Register Blueprints
        app.register_blueprint(main)
        app.register_blueprint(auth)
        app.register_blueprint(trello)

        return app


def create_app():
    app = Flask(__name__)
    return configure_app(app)


def create_app_lambda():
    app = FlaskLambda(__name__)
    return configure_app(app)
