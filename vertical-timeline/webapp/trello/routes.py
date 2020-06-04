from flask import (Blueprint, jsonify, redirect, render_template, request,
                   session, url_for, flash)
from flask_login import login_required

from webapp import trello_api_instance
from webapp.exceptions import UnauthorizedException, GenericException

trello = Blueprint('trello', __name__)


@trello.route('/token')
@login_required
def token():
    return render_template('token.html')

@trello.route('/token_post', methods=['POST'])
@login_required
def token_post():
    session['trello_token'] = request.json['token'] # request.form['token']
    return jsonify({'redirect':url_for('auth.account', _external=True)})


@trello.route('/revoke', methods=['POST'])
@login_required
def revoke():
    session.pop('trello_token')
    return redirect(url_for('auth.account'))

@trello.route('/timeline')
@login_required
def timeline():
    token = session.get('trello_token')
    if not token :
        return redirect(url_for('auth.account'))
    
    model = {}
    try:
        model['boards'] = trello_api_instance.get_boards(token)
        model['events'] = trello_api_instance.get_events(token)[:10]
        
    except UnauthorizedException:
        flash(f'Authorisation error from Trello, please check your account settings, you might need to authorise it again', category='danger')
    except:
        flash(f'Error while connecting to Trello, please try again later', category='danger')

    return render_template('timeline.html', model=model)
    
