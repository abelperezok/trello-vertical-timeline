import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr, Key, Or
from functools import reduce
from dynamodb_repository.base import IndependentEntityRepository, DependentEntityRepository, AssociativeEntityRepository

class UserDataRepository:
    def __init__(self, table_name, endpoint_url=None):
        self.repo = IndependentEntityRepository(table_name, endpoint_url=endpoint_url)        
        self.repo.pk_prefix = 'USER'
        self.repo.sk_prefix = 'METADATA'

    def get_user_data(self, user_id):
        return self.repo.get_item(user_id)

    def delete_user_data(self, user_id):
        return self.repo.delete_item(user_id)

    def update_user_token(self, user_id, token):
        item = self.repo.get_item(user_id) or dict()
        item['trello_token'] = token
        return self.repo.add_item(user_id, item)

    def update_timestamp(self, user_id, timestamp):
        item = self.repo.get_item(user_id) or dict()
        item['timestamp'] = timestamp
        return self.repo.add_item(user_id, item)



class UserBoardRepository:
    def __init__(self, table_name, endpoint_url=None):
        self.repo = DependentEntityRepository(table_name, endpoint_url=endpoint_url)        
        self.repo.pk_prefix = 'USER'
        self.repo.sk_prefix = 'BOARD'

    def add_boards(self, user_id, boards):
        items_to_create = []
        for board in boards:
            item = (board['id'], board)
            items_to_create.append(item)
        return self.repo.batch_add_items(user_id, items_to_create)

    def delete_boards(self, user_id, boards):
        items_to_delete = []
        for board in boards:
            item = board['id']
            items_to_delete.append(item)
        self.repo.batch_delete_items(user_id, items_to_delete)

    def get_boards(self, user_id):
        data = self.repo.table_query_by_parent_id(user_id)
        return list(map(lambda x: dict({'id': x['id'], 'name': x['name'] }), data))
        


class BoardListRepository:
    def __init__(self, table_name, endpoint_url=None):
        self.repo = DependentEntityRepository(table_name, endpoint_url=endpoint_url)        
        self.repo.pk_prefix = 'USER'
        self.repo.sk_prefix = 'USER_BOARD'

    def add_lists(self, user_id, board_id, lists):
        items_to_create = []
        for l in lists:
            item = (f"{board_id}#LIST#{l['id']}" , l)
            items_to_create.append(item)
        return self.repo.batch_add_items(user_id, items_to_create)

    def delete_lists(self, user_id, board_id, lists):
        items_to_delete = []
        for l in lists:
            item = f"{board_id}#LIST#{l['id']}"
            items_to_delete.append(item)
        self.repo.batch_delete_items(user_id, items_to_delete)

    def get_lists(self, user_id, board_id):
        sk_prefix = f"{self.repo.sk_prefix}#{board_id}#LIST"
        data = self.repo.table_query_by_parent_id(user_id, sk_prefix)
        return list(map(lambda x: dict({'id': x['id'], 'name': x['name'] }), data))


class BoardLabelRepository:
    def __init__(self, table_name, endpoint_url=None):
        self.repo = DependentEntityRepository(table_name, endpoint_url=endpoint_url)        
        self.repo.pk_prefix = 'USER'
        self.repo.sk_prefix = 'USER_BOARD'

    def add_labels(self, user_id, board_id, labels):
        items_to_create = []
        for label in labels:
            item = (f"{board_id}#LABEL#{label['id']}" , label)
            items_to_create.append(item)
        return self.repo.batch_add_items(user_id, items_to_create)

    def delete_labels(self, user_id, board_id, labels):
        items_to_delete = []
        for label in labels:
            item = f"{board_id}#LABEL#{label['id']}"
            items_to_delete.append(item)
        self.repo.batch_delete_items(user_id, items_to_delete)

    def get_labels(self, user_id, board_id):
        sk_prefix = f"{self.repo.sk_prefix}#{board_id}#LABEL"
        data = self.repo.table_query_by_parent_id(user_id, sk_prefix)
        return list(map(lambda x: dict({'id': x['id'], 'name': x['name'], 'color': x['color'] }), data))


class BoardCardRepository:
    def __init__(self, table_name, endpoint_url=None):
        self.repo = DependentEntityRepository(table_name, endpoint_url=endpoint_url)        
        self.repo.pk_prefix = 'USER'
        self.repo.sk_prefix = 'CARD'

    def add_cards(self, user_id, cards):
        items_to_create = []
        for card in cards:
            item = (card['id'], card)
            items_to_create.append(item)
        return self.repo.batch_add_items(user_id, items_to_create)

    def delete_cards(self, user_id, cards):
        items_to_delete = []
        for card in cards:
            item = card['id']
            items_to_delete.append(item)
        self.repo.batch_delete_items(user_id, items_to_delete)

    def get_cards(self, user_id):
        data = self.repo.table_query_by_parent_id(user_id)
        return list(map(lambda x: dict({'id': x['id'], 'name': x['name'] }), data))

    def get_cards_filtered(self, user_id, lists=[], labels=[]):
        list_filters = reduce(Or, ([Attr('idList').eq(l) for l in lists])) if len(lists) > 0 else Attr('idList').exists()
        labels_filters = reduce(Or, ([Attr('idLabels').contains(l) for l in labels])) if len(labels) > 0 else Attr('idLabels').exists()

        filters = list_filters & labels_filters

        data = self.repo.table_query_by_parent_id(user_id, filter_expression=filters)
        return list(map(lambda x: dict({
            'id': x['id'], 
            'name': x['name'],
            'due': x['due'],
            'dueComplete': x['dueComplete'],
            'desc': x['desc'],
            'url': x['url'],
            'idBoard': x['idBoard'],
            'idList': x['idList'],
            'idLabels': x['idLabels']
            }), data))