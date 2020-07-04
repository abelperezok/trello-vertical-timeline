import json
import os
from datetime import datetime

from verticaltimeline_common.repository import UserDataRepository, UserBoardRepository, BoardListRepository, BoardLabelRepository, BoardCardRepository
from verticaltimeline_common.trello_api import TrelloApi

user_repo = UserDataRepository(os.environ['TABLE_NAME'])
board_repo = UserBoardRepository(os.environ['TABLE_NAME'])
list_repo = BoardListRepository(os.environ['TABLE_NAME'])
label_repo = BoardLabelRepository(os.environ['TABLE_NAME'])
card_repo = BoardCardRepository(os.environ['TABLE_NAME'])


# Message sample
# {
#     "TrelloAppName": "app1",
#     "TrelloAuthScope": "scope",
#     "TrelloApiKey": "key1",
#     "UserId": "user-000"
# }


def lambda_handler(event, context):
    for record in event['Records']:
        body = record["body"]
        message = json.loads(body)
        print(message)
        process_message(message)


def process_message(message):

    trello = TrelloApi(
        trello_app_name = message['TrelloAppName'],
        trello_auth_scope =  message['TrelloAuthScope'],
        trello_api_key = message['TrelloApiKey']
    )
    user_id = message['UserId']
    wipe_data(user_id)
    populate_data(user_id, trello)


def wipe_data(user_id):
    # get the stored boards
    boards = board_repo.get_boards(user_id)
    print(f'Found {len(boards)} boards')
    for board in boards:
        # get the lists for each board
        board_lists = list_repo.get_lists(user_id, board['id'])
        print(f'Found {len(board_lists)} lists in board {board["name"]}')
        # remove the lists from each board
        list_repo.delete_lists(user_id, board['id'], board_lists)
        # get the labels for each board
        board_labels = label_repo.get_labels(user_id, board['id'])
        print(f'Found {len(board_labels)} labels in board {board["name"]}')
        # remove the labels from each board
        label_repo.delete_labels(user_id, board['id'], board_labels)

    # get all the cards for the current user
    board_cards = card_repo.get_cards(user_id)
    print(f'Found {len(board_cards)} cards in user {user_id}')
    # remove all the cards for the current user
    card_repo.delete_cards(user_id, board_cards)
    # remove the boards
    board_repo.delete_boards(user_id, boards)
    print(f'all done')


def populate_data(user_id, trello):
    user_record = user_repo.get_user_data(user_id)
    if not user_record:
        print('No user record found for this user, aborting.')
        return
    print('Found user_record')
    trello_token = user_record.get('trello_token')
    if not trello_token:
        print('No trello token found for this user, aborting.')
        return
    print('Found trello token')
    # get the fresh boards
    boards = trello.get_boards(trello_token)
    total_boards = len(boards)
    print(f'Found {total_boards} boards')
    user_repo.update_progress(user_id, 0, total_boards)
    board_repo.add_boards(user_id, boards)
    for i, board in enumerate(boards):
        # get the fresh lists
        board_lists = trello.get_lists(trello_token, board['id'])
        # add the fresh lists
        print(f'Adding {len(board_lists)} lists to board {board["name"]}')
        list_repo.add_lists(user_id, board['id'], board_lists)
        # get the fresh labels
        board_labels = trello.get_labels(trello_token, board['id'])
        # add the fresh labels
        print(f'Adding {len(board_labels)} labels to board {board["name"]}')
        label_repo.add_labels(user_id, board['id'], board_labels)
        # get the fresh cards
        card_list = trello.get_cards(trello_token, board['id'])
        # add the fresh cards
        print(f'Adding {len(card_list)} cards to board {board["name"]}')
        card_repo.add_cards(user_id, card_list)
        user_repo.update_progress(user_id, i+1, total_boards)
    print(f'Updating timestamp')
    user_repo.update_timestamp(user_id, datetime.utcnow().isoformat())
    print(f'all done')
