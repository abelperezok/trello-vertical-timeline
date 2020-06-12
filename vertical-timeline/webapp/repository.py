import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

class RepositoryBase:
    def __init__(self, table_name, endpoint_url):
        resource = boto3.resource('dynamodb', endpoint_url=endpoint_url)
        self.client = boto3.client('dynamodb', endpoint_url=endpoint_url)
        self.table = resource.Table(table_name)
        self.pk_prefix = ''
        self.sk_prefix = ''
        self.gsi1_prefix = ''

    def _pk_value(self, id):
        return f'{self.pk_prefix}#{id}'

    def _sk_value(self, id):
        return f'{self.sk_prefix}#{id}'

    def _gsi1_value(self, id):
        return f'{self.gsi1_prefix}#{id}'

    def _get_key_data(self, pk, sk):
        return { 'PK': pk, 'SK': sk }

    def _put_item(self, pk, sk, item):
        key_data = self._get_key_data(pk, sk)
        try:
            response = self.table.put_item(
                Item={**key_data, **item}
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            return response

    def _get_item(self, pk, sk):
        key_data = self._get_key_data(pk, sk)
        try:
            response = self.table.get_item(Key=key_data)
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            return response.get('Item')
    
    def _delete_item(self, pk, sk):
        key_data = self._get_key_data(pk, sk)
        try:
            response = self.table.delete_item(Key=key_data)
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            return response

    def _gsi1_query(self, gsi1, sk_prefix):
        try:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=
                    Key('GSI1').eq(gsi1) & Key('SK').begins_with(sk_prefix)
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            return response['Items']

    def _table_query(self, pk, sk_prefix):
        try:
            response = self.table.query(
                KeyConditionExpression=
                    Key('PK').eq(pk) & Key('SK').begins_with(sk_prefix)
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            return response['Items']

    def _str_item(self, i):
        result = {}
        for k, v in i.items():
            result[k] = {'S': str(v)}
        return result

    def _put_request_item(self, i):
        return {
            'PutRequest': {
                'Item': self._str_item(i)
            }
        }

    def _delete_request_item(self, i):
        return {
            'DeleteRequest': {
                'Key': self._str_item(i)
            }
        }

    def _batch_add_items(self, items):
        if len(items) == 0:
            return
        db_items = list(map(self._put_request_item, items))

        response = self.client.batch_write_item(
            RequestItems={
                f'{self.table.name}': db_items
            }
        )
        return response

    def _batch_delete_items(self, items):
        if len(items) == 0:
            return
        db_items = list(map(self._delete_request_item, items))

        response = self.client.batch_write_item(
            RequestItems={
                f'{self.table.name}': db_items
            }
        )
        return response




class IndependentEntityRepository(RepositoryBase):
    def __init__(self, table_name, endpoint_url=None):
        super().__init__(table_name, endpoint_url=endpoint_url)

    def add_item(self, key, item):
        pk = self._pk_value(key)
        sk = self._sk_value(key)
        item['GSI1'] = self.pk_prefix
        return self._put_item(pk, sk, item)

    def get_item(self, key):
        pk = self._pk_value(key)
        sk = self._sk_value(key)
        return self._get_item(pk, sk)

    def delete_item(self, key):
        pk = self._pk_value(key)
        sk = self._sk_value(key)
        return self._delete_item(pk, sk)

    def gsi1_query_all(self):
        return self._gsi1_query(self.pk_prefix, self.sk_prefix)


    def batch_add_items(self, items):
        db_items = []
        for key,item in items:
            pk = self._pk_value(key)
            sk = self._sk_value(key)
            key_data = self._get_key_data(pk, sk)
            item['GSI1'] = self.pk_prefix
            db_item = { **key_data, **item }
            db_items.append(db_item)
        return self._batch_add_items(db_items)

    def batch_delete_items(self, keys):
        db_items = []
        for key in keys:
            pk = self._pk_value(key)
            sk = self._sk_value(key)
            key_data = self._get_key_data(pk, sk)
            db_items.append(key_data)        
        return self._batch_delete_items(db_items)



class DependentEntityRepository(RepositoryBase):
    def __init__(self, table_name, endpoint_url=None):
        super().__init__(table_name, endpoint_url=endpoint_url)

    def add_item(self, parent_key, entity_key, item):
        pk = self._pk_value(parent_key)
        sk = self._sk_value(entity_key)
        return self._put_item(pk, sk, item)

    def get_item(self, parent_key, entity_key):
        pk = self._pk_value(parent_key)
        sk = self._sk_value(entity_key)
        return self._get_item(pk, sk)

    def table_query_by_parent_id(self, parent_key, sk_prefix=None):
        pk = self._pk_value(parent_key)
        return self._table_query(pk, sk_prefix or self.sk_prefix)

    def delete_item(self, parent_key, entity_key):
        pk = self._pk_value(parent_key)
        sk = self._sk_value(entity_key)
        return self._delete_item(pk, sk)

    def batch_add_items(self, parent_key, items):
        pk = self._pk_value(parent_key)
        db_items = []
        for key,item in items:
            sk = self._sk_value(key)
            key_data = self._get_key_data(pk, sk)
            db_item = { **key_data, **item }
            db_items.append(db_item)
        return self._batch_add_items(db_items)

    def batch_delete_items(self, parent_key, keys):
        pk = self._pk_value(parent_key)
        db_items = []
        for key in keys:
            sk = self._sk_value(key)
            key_data = self._get_key_data(pk, sk)
            db_items.append(key_data)        
        return self._batch_delete_items(db_items)








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