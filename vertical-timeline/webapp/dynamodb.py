# import os
# import boto3
# from botocore.exceptions import ClientError
# from boto3.dynamodb.conditions import Key


# class DataRepository:
#     def __init__(self, table_name):
#         resource = boto3.resource('dynamodb')
#         self.client = boto3.client('dynamodb')
#         self.table = resource.Table(table_name)
#         self.pk_prefix = ''
#         self.sk_prefix = ''

#     def _str_item(self, i):
#         result = {}
#         for k, v in i.items():
#             result[k] = {'S': str(v)}
#         return result

#     def _put_request_item(self, i):
#         return {
#             'PutRequest': {
#                 'Item': self._str_item(i)
#             }
#         }
#     def _delete_request_item(self, i):
#         return {
#             'DeleteRequest': {
#                 'Key': self._str_item(i)
#             }
#         }

#     def _get_key_data(self, pk, sk, sk_prefix=''):
#         return {
#             'PK': f'{self.pk_prefix}#{pk}',
#             'SK': f'{sk_prefix}{self.sk_prefix}#{sk}'
#         }



#     def _query_items(self, pk, sk_prefix):
#         try:
#             response = self.table.query(
#                 KeyConditionExpression=
#                     Key('PK').eq(f'{self.pk_prefix}#{pk}') & Key('SK').begins_with(sk_prefix)
#             )
#         except ClientError as e:
#             print(e.response['Error']['Message'])
#         else:
#             return response['Items']





#     def _get_item(self, pk):
#         key_data = self._get_key_data(pk, pk)
#         try:
#             response = self.table.get_item(Key=key_data)
#         except ClientError as e:
#             print(e.response['Error']['Message'])
#         else:
#             return response.get('Item')

#     def _put_item(self, pk, item):
#         key_data = self._get_key_data(pk, pk)
#         try:
#             response = self.table.put_item(
#                 Item={**key_data, **item}
#             )
#         except ClientError as e:
#             print(e.response['Error']['Message'])
#         else:
#             return response

#     def _delete_item(self, pk):
#         key_data = self._get_key_data(pk, pk)
#         try:
#             response = self.table.delete_item(Key=key_data)
#         except ClientError as e:
#             print(e.response['Error']['Message'])
#         else:
#             return response


#     def _batch_add_items(self, pk, sk_prefix, items):
#         if len(items) == 0:
#             return
#         key_items = map(lambda x: dict({**x, **self._get_key_data(pk, x['id'], sk_prefix)}), items)
#         db_items = list(map(self._put_request_item, key_items))
#         response = self.client.batch_write_item(
#             RequestItems={
#                 f'{self.table.name}': db_items
#             }
#         )
#         return response

#     def _batch_remove_items(self, pk, sk_prefix, items):
#         if len(items) == 0:
#             return
#         key_items = map(lambda x: self._get_key_data(pk, x['id'], sk_prefix), items)
#         db_items = list(map(self._delete_request_item, key_items))
#         response = self.client.batch_write_item(
#             RequestItems={
#                 f'{self.table.name}': db_items
#             }
#         )
#         return response

# class UserData(DataRepository):
#     def __init__(self):
#         super().__init__(os.environ['TABLE_NAME'])
#         self.pk_prefix = 'USER'
#         self.sk_prefix = 'METADATA'

#     def get_user_token(self, user_id):
#         return self._get_item(user_id)

#     def add_user_token(self, user_id, trello_token):
#         return self._put_item(user_id, {'trello_token': trello_token})

#     def update_timestamp(self, user_id, timestamp):
#         item = self._get_item(user_id)
#         item['timestamp'] = timestamp
#         return self._put_item(user_id, item)

#     def remove_user_token(self, user_id):
#         return self._delete_item(user_id)


# class UserBoard(DataRepository):
#     def __init__(self):
#         super().__init__(os.environ['TABLE_NAME'])
#         self.pk_prefix = 'USER'
#         self.sk_prefix = 'BOARD'

#     def add_boards(self, user_id, boards):
#         return self._batch_add_items(user_id, '', boards)

#     def remove_boards(self, user_id, boards):
#         return self._batch_remove_items(user_id, '', boards)

#     def get_boards(self, user_id):
#         data = self._query_items(user_id, self.sk_prefix)
#         return list(map(lambda x: dict({'id': x['id'], 'name': x['name'] }), data))


# class BoardList(DataRepository):
#     def __init__(self):
#         super().__init__(os.environ['TABLE_NAME'])
#         self.pk_prefix = 'USER'
#         self.sk_prefix = 'LIST'

#     def add_lists(self, user_id, board_id, lists):
#         return self._batch_add_items(user_id, f'USER_BOARD#{board_id}#', lists)

#     def remove_lists(self, user_id, board_id, lists):
#         return self._batch_remove_items(user_id, f'USER_BOARD#{board_id}#', lists)
    
#     def get_lists(self, user_id, board_id):
#         data = self._query_items(user_id, f'USER_BOARD#{board_id}#{self.sk_prefix}')
#         return list(map(lambda x: dict({'id': x['id'], 'name': x['name'] }), data))


# class BoardLabel(DataRepository):
#     def __init__(self):
#         super().__init__(os.environ['TABLE_NAME'])
#         self.pk_prefix = 'USER'
#         self.sk_prefix = 'LABEL'

#     def add_labels(self, user_id, board_id, labels):
#         return self._batch_add_items(user_id, f'USER_BOARD#{board_id}#', labels)

#     def remove_labels(self, user_id, board_id, labels):
#         return self._batch_remove_items(user_id, f'USER_BOARD#{board_id}#', labels)
    
#     def get_labels(self, user_id, board_id):
#         data = self._query_items(user_id, f'USER_BOARD#{board_id}#{self.sk_prefix}')
#         return list(map(lambda x: dict({'id': x['id'], 'name': x['name'], 'color': x['color'] }), data))