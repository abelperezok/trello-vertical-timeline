import os
from datetime import datetime, date

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for, current_app)
from flask_login import current_user, login_required

from verticaltimeline_common.exceptions import GenericException, UnauthorizedException
from verticaltimeline_common.repository import UserDataRepository, UserBoardRepository, BoardListRepository, BoardLabelRepository, BoardCardRepository
from verticaltimeline_common.trello_api import TrelloApi


trello = Blueprint('trello', __name__)
user_repo = UserDataRepository(os.environ['TABLE_NAME'])
board_repo = UserBoardRepository(os.environ['TABLE_NAME'])
list_repo = BoardListRepository(os.environ['TABLE_NAME'])
label_repo = BoardLabelRepository(os.environ['TABLE_NAME'])
card_repo = BoardCardRepository(os.environ['TABLE_NAME'])

@trello.route('/account')
@login_required
def account():

    trello_api_instance = TrelloApi(
        trello_app_name = current_app.config['TRELLO_APP_NAME'],
        trello_auth_scope =  current_app.config['TRELLO_AUTH_SCOPE'],
        trello_api_key = current_app.config['TRELLO_API_KEY']
    )

    return_url = url_for('trello.token', _external=True)
    model = {}
    user_record = user_repo.get_user_data(current_user.get_id())
    model['authorize_url'] = trello_api_instance.get_authorize_url(return_url)
    model['token'] = '**********' if user_record else None
    model['boards'] = board_repo.get_boards(current_user.get_id())
    model['last_updated'] = datetime.fromisoformat(user_record.get('timestamp')) if user_record else None
    
    return render_template('account.html', model=model)


@trello.route('/token')
@login_required
def token():
    return render_template('token.html')


@trello.route('/token_post', methods=['POST'])
@login_required
def token_post():
    trello_token = request.json['token']  # request.form['token']
    user_repo.update_user_token(current_user.get_id(), trello_token)
    # populate_data() ## here to put the message to populate the data
    return jsonify({'redirect': url_for('trello.account', _external=True)})


@trello.route('/revoke', methods=['POST'])
@login_required
def revoke():
    user_repo.delete_user_data(current_user.get_id())
    # wipe_data() ## here to put the message to wipe the data
    return redirect(url_for('trello.account'))


@trello.route('/trello/boards')
@login_required
def trello_boards():
    boards = board_repo.get_boards(current_user.get_id())
    return jsonify(boards)

@trello.route('/trello/lists')
@login_required
def trello_lists():
    boards = request.args['boards'].split(',')
    result = []
    all_boards = board_repo.get_boards(current_user.get_id())
    for board in boards:
        board_item = [b for b in all_boards if b['id'] == board]
        if len(board_item) > 0:
            board_lists = list_repo.get_lists(current_user.get_id(), board)
            result.append({
                'name': board_item[0]['name'],
                'items':board_lists
            })
    return jsonify(result)


@trello.route('/trello/labels')
@login_required
def trello_labels():
    boards = request.args['boards'].split(',')
    result = []
    all_boards = board_repo.get_boards(current_user.get_id())
    for board in boards:
        board_item = [b for b in all_boards if b['id'] == board]
        if len(board_item) > 0:
            board_lists = label_repo.get_labels(current_user.get_id(), board)
            board_lists_mapped = list(map(lambda x: dict({'id': x['id'], 'name': f"{x['name']} ({x['color']})" }), board_lists))
            result.append({
                'name': board_item[0]['name'],
                'items':board_lists_mapped
            })
    return jsonify(result)


@trello.route('/trello/cards')
@login_required
def trello_cards():
    lists = list(filter(lambda x: x, request.args['lists'].split(',')))
    labels = list(filter(lambda x: x, request.args['labels'].split(',')))

    cards = card_repo.get_cards_filtered(current_user.get_id(), lists=lists, labels=labels)

    # to filter only those with due data and not dueComplete
    # if item['due'] is not None and item['dueComplete'] == False:

    result = []
    for item in cards:        
        date_only = date.fromisoformat(item['due'].split('T')[0]) if item['due'] != 'None' else date(1900, 1, 1)
        desc = item['desc']
        if len(desc) > 150:
            desc = item['desc'][:150] + '...'
        result.append({
            'id': item['id'],
            'name': item['name'],
            'due_formatted': date_only.strftime('%d %B %Y') if date_only != date(1900, 1, 1) else 'No due date',
            'desc': desc,
            'url': item['url']
        })

    return jsonify(result)


@trello.route('/trello/populate', methods=['POST'])
@login_required
def populate():
    # wipe_data() # put the message in the queue
    # populate_data()
    return redirect(url_for('trello.account'))



@trello.route('/timeline')
@login_required
def timeline():
    user_record = user_repo.get_user_data(current_user.get_id())
    if not user_record:
        return redirect(url_for('trello.account'))

    token = user_record.get('trello_token')
    if not token:
        return redirect(url_for('trello.account'))

    model = {}
    try:
        model['boards'] = board_repo.get_boards(current_user.get_id())
        model['events'] = [] # trello_api_instance.get_events(token)[:10]

    except UnauthorizedException:
        flash(f'Authorisation error from Trello, please check your account settings, you might need to authorise it again', category='danger')
    except:
        flash(f'Error while connecting to Trello, please try again later', category='danger')

    return render_template('timeline.html', model=model)




