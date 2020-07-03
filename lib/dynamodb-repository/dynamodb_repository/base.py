import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr, Key, Or
from functools import reduce

def buffered(size):
    def wrap(f):
        def wrapped(self, arg1=None, arg2=None):
            parent_key = ''
            items = []

            if (f.__code__.co_argcount == 3):
                parent_key = arg1
                items = arg2
            else:
                items = arg1

            count = len(items)
            start = 0
            while count > 0:
                buffer = items[start : start + size]
                if (f.__code__.co_argcount == 3):
                    f(self, parent_key, buffer)
                else:
                    f(self, buffer)
                count = count - len(buffer)
                start = start + len(buffer)
        return wrapped
    return wrap



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

    def _table_query(self, pk, sk_prefix, filter_expression = None):
        try:
            query_args = {
                'KeyConditionExpression': Key('PK').eq(pk) & Key('SK').begins_with(sk_prefix)
            }
            if filter_expression:
                query_args['FilterExpression'] = filter_expression
            response = self.table.query(**query_args)
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

    @buffered(25)
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

    @buffered(25)
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

    def table_query_by_parent_id(self, parent_key, sk_prefix=None, filter_expression=None):
        pk = self._pk_value(parent_key)
        return self._table_query(pk, sk_prefix or self.sk_prefix, filter_expression)

    def delete_item(self, parent_key, entity_key):
        pk = self._pk_value(parent_key)
        sk = self._sk_value(entity_key)
        return self._delete_item(pk, sk)

    @buffered(25)
    def batch_add_items(self, parent_key, items):
        pk = self._pk_value(parent_key)
        db_items = []
        for key,item in items:
            sk = self._sk_value(key)
            key_data = self._get_key_data(pk, sk)
            db_item = { **key_data, **item }
            db_items.append(db_item)
        result = self._batch_add_items(db_items)

    @buffered(25)
    def batch_delete_items(self, parent_key, keys):
        pk = self._pk_value(parent_key)
        db_items = []
        for key in keys:
            sk = self._sk_value(key)
            key_data = self._get_key_data(pk, sk)
            db_items.append(key_data)        
        return self._batch_delete_items(db_items)



class AssociativeEntityRepository(RepositoryBase):
    def __init__(self, table_name, endpoint_url=None):
        super().__init__(table_name, endpoint_url=endpoint_url)

    def _get_relation_key(self, parent1_key, parent2_key):
        return parent1_key + parent2_key

    def add_item(self, parent1_key, parent2_key, item):
        relation_key = self._get_relation_key(parent1_key, parent2_key)
        pk = self._pk_value(parent1_key)
        sk = self._sk_value(relation_key)
        item['GSI1'] = self._gsi1_value(parent2_key)
        return self._put_item(pk, sk, item)

    def delete_item(self, parent1_key, parent2_key):
        relation_key = self._get_relation_key(parent1_key, parent2_key)
        pk = self._pk_value(parent1_key)
        sk = self._sk_value(relation_key)
        return self._delete_item(pk, sk)

    def table_query_by_parent_id(self, parent_key, sk_prefix=None, filter_expression=None):
        pk = self._pk_value(parent_key)
        return self._table_query(pk, sk_prefix or self.sk_prefix, filter_expression)

    def gsi1_query_by_parent_id(self, parent_key):
        gsi1 = self._gsi1_value(parent_key)
        return self._gsi1_query(gsi1, self.sk_prefix)

    @buffered(25)
    def batch_add_items(self, parent_key, items):
        pk = self._pk_value(parent_key)
        db_items = []
        for key,item in items:
            relation_key = self._get_relation_key(parent_key, key)
            sk = self._sk_value(relation_key)
            key_data = self._get_key_data(pk, sk)
            db_item = { **key_data, **item }
            db_item['GSI1'] = self._gsi1_value(key)
            db_items.append(db_item)
        return self._batch_add_items(db_items)

    @buffered(25)
    def batch_delete_items(self, parent_key, keys):
        pk = self._pk_value(parent_key)
        db_items = []
        for key in keys:
            relation_key = self._get_relation_key(parent_key, key)
            sk = self._sk_value(relation_key)
            key_data = self._get_key_data(pk, sk)
            db_items.append(key_data)        
        return self._batch_delete_items(db_items)

