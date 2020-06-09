import os
from datetime import datetime

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required

from webapp import trello_api_instance
from webapp.dynamodb import UserData, BoardList, UserBoard, BoardLabel
from webapp.exceptions import GenericException, UnauthorizedException

trello = Blueprint('trello', __name__)
user_data = UserData()
user_board = UserBoard()
board_list = BoardList()
board_label = BoardLabel()

@trello.route('/account')
@login_required
def account():
    return_url = url_for('trello.token', _external=True)
    model = {}
    user_record = user_data.get_user_token(current_user.get_id())
    model['authorize_url'] = trello_api_instance.get_authorize_url(return_url)
    model['token'] = '**********' if user_record else None
    model['boards'] = user_board.get_boards(current_user.get_id())
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
    user_data.add_user_token(current_user.get_id(), trello_token)
    populate_data()
    return jsonify({'redirect': url_for('trello.account', _external=True)})


@trello.route('/revoke', methods=['POST'])
@login_required
def revoke():
    user_data.remove_user_token(current_user.get_id())
    wipe_data()
    return redirect(url_for('trello.account'))


@trello.route('/trello/boards')
@login_required
def trello_boards():
    boards = user_board.get_boards(current_user.get_id())
    return jsonify(boards)

@trello.route('/trello/lists')
@login_required
def trello_lists():
    boards = request.args['boards'].split(',')
    result = []
    for board in boards:
        board_lists = board_list.get_lists(current_user.get_id(), board)
        result.extend(board_lists)
    return jsonify(result)


@trello.route('/trello/labels')
@login_required
def trello_labels():
    boards = request.args['boards'].split(',')
    result = []
    for board in boards:
        board_lists = board_label.get_labels(current_user.get_id(), board)
        board_lists_mapped = map(lambda x: dict({'id': x['id'], 'name': f"{x['name']} ({x['color']})" }), board_lists)
        result.extend(board_lists_mapped)
    return jsonify(result)












def wipe_data():
    # get the stored boards
    boards = user_board.get_boards(current_user.get_id())
    for board in boards:
        # get the lists for each board
        board_lists = board_list.get_lists(current_user.get_id(), board['id'])
        # remove the lists from each board
        board_list.remove_lists(current_user.get_id(), board['id'], board_lists)
        # get the labels for each board
        board_labels = board_label.get_labels(current_user.get_id(), board['id'])
        # remove the labels from each board
        board_label.remove_labels(current_user.get_id(), board['id'], board_labels)

    # remove the boards
    user_board.remove_boards(current_user.get_id(), boards)

def populate_data():
    trello_token = user_data.get_user_token(current_user.get_id()).get('trello_token')
    # get the fresh boards
    boards = trello_api_instance.get_boards(trello_token)
    user_board.add_boards(current_user.get_id(), boards)
    for board in boards:
        # get the fresh lists
        board_lists = trello_api_instance.get_lists(trello_token, board['id'])
        # add the fresh lists
        board_list.add_lists(current_user.get_id(), board['id'], board_lists)
        # get the fresh labels
        board_labels = trello_api_instance.get_labels(trello_token, board['id'])
        # add the fresh labels
        board_label.add_labels(current_user.get_id(), board['id'], board_labels)

    user_data.update_timestamp(current_user.get_id(), datetime.utcnow().isoformat())    



@trello.route('/trello/populate', methods=['POST'])
@login_required
def populate():
    wipe_data()
    populate_data()
    return redirect(url_for('trello.account'))






@trello.route('/timeline')
@login_required
def timeline():
    user_record = user_data.get_user_token(current_user.get_id())
    if not user_record:
        return redirect(url_for('trello.account'))

    token = user_record.get('trello_token')
    if not token:
        return redirect(url_for('trello.account'))

    model = {}
    try:
        model['boards'] = user_board.get_boards(current_user.get_id())
        model['events'] = [] # trello_api_instance.get_events(token)[:10]

    except UnauthorizedException:
        flash(f'Authorisation error from Trello, please check your account settings, you might need to authorise it again', category='danger')
    except:
        flash(f'Error while connecting to Trello, please try again later', category='danger')

    return render_template('timeline.html', model=model)






# @trello.route('/trello/data')
# @login_required
# def trello_data():
    # list = [ k for k,v in os.environ.items() ]

    # put_user_data(current_user.get_id(), None)
    # put_user_data(current_user.get_id(), session.get('trello_token'))
    # delete_user_data(current_user.get_id())

    # token = user_data.get_user_token(current_user.get_id()).get('trello_token')
    # boards = trello_api_instance.get_boards(token)

    # def _attr(a):
    #     print(a)
    #     return { f'{a[0]}':{'S': str(a[1])}}
    
    # def _str_item(i):
    #     result = {}
    #     for k,v in i.items():
    #         result[k] = {'S': str(v)}
    #     return result
    
    # def _put_request_item(i):
    #     return {
    #         'PutRequest': {
    #             'Item': _str_item(i)
    #         }
    #     }

    # result = map(_str_item, boards)
    # result = map(_put_request_item, boards)

    # repo = DataRepository(os.environ['TABLE_NAME'])

    # result = repo._batch_add_items(current_user.get_id(), boards)

    # repo = UserBoard()
    # # result = repo.add_boards(current_user.get_id(), boards)
    # boards = repo.get_boards(current_user.get_id())
    # token = user_data.get_user_token(current_user.get_id()).get('trello_token')

    # repo.remove_boards(current_user.get_id(), result)

    # board_id = boards[0]['id']
    # lists = trello_api_instance.get_lists(token, board_id)
    # listRepo = BoardList()

    # listRepo.add_lists(board_id, lists)


    # return jsonify({
    #     'data': lists,
    #     'current_user': current_user.get_id()
    #     })
