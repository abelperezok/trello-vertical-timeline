import sys
import os
sys.path.append(os.path.realpath(
    os.path.dirname(__file__)+"/../vertical-timeline/"))
from webapp.repository import IndependentEntityRepository, DependentEntityRepository, AssociativeEntityRepository

from tests.conftest import table_name, local_url

class TestRepository:

    def test_GenericOperations_IndependentEntityRepository(self, docker_dynamodb):

        repo = IndependentEntityRepository(table_name, local_url)
        repo.pk_prefix = 'ENTITY'
        repo.sk_prefix = 'METADATA'

        item_list = repo.gsi1_query_all()
        assert len(item_list) == 0

        repo.add_item(1, {'id': 1, 'name': 'p1'})

        item_list = repo.gsi1_query_all()

        assert len(item_list) == 1

        repo.add_item(2, {'id': 2, 'name': 'p2'})

        item_list = repo.gsi1_query_all()

        assert len(item_list) == 2

        item1 = repo.get_item(1)

        assert item1 is not None
        assert item1['id'] == 1
        assert item1['name'] == 'p1'

        item2 = repo.get_item(2)
        assert item2 is not None
        assert item2['id'] == 2
        assert item2['name'] == 'p2'        

        assert item_list[0] is not None
        assert item_list[0]['id'] == 1
        assert item_list[0]['name'] == 'p1'
        assert item_list[1] is not None
        assert item_list[1]['id'] == 2
        assert item_list[1]['name'] == 'p2'

        repo.delete_item(1)

        item_list = repo.gsi1_query_all()
        assert len(item_list) == 1

        item1 = repo.get_item(1)
        assert item1 is None

        repo.delete_item(2)

        item_list = repo.gsi1_query_all()
        assert len(item_list) == 0

        item2 = repo.get_item(2)
        assert item2 is None

    def test_BatchOperations_IndependentEntityRepository(self, docker_dynamodb):

        repo = IndependentEntityRepository(table_name, local_url)
        repo.pk_prefix = 'ENTITY'
        repo.sk_prefix = 'METADATA'

        items_to_create = []
        for i in range(10):
            item = (f'TE{i}',  {'id': f'TE{i}', 'name': f'p{i}'})
            items_to_create.append(item)

        repo.batch_add_items(items_to_create)

        item_list = repo.gsi1_query_all()

        assert len(item_list) == 10

        for i in range(len(item_list)):
            item = item_list[i]
            assert item is not None
            assert item['id'] == f'TE{i}'
            assert item['name'] == f'p{i}'

        # self.scan_table()
        items_to_delete = []
        for i in range(len(item_list)):
            item = item_list[i]['id']
            items_to_delete.append(item)

        repo.batch_delete_items(items_to_delete)

        item_list = repo.gsi1_query_all()

        assert len(item_list) == 0

    def test_GenericOperations_DependentEntityRepository(self, docker_dynamodb):

        repo = DependentEntityRepository(table_name, local_url)
        repo.pk_prefix = 'PARENT'
        repo.sk_prefix = 'ENTITY'
        parent_id = 'p1'

        item_list = repo.table_query_by_parent_id(parent_id)
        assert len(item_list) == 0

        repo.add_item(parent_id, 'e1', {'id': 'e1', 'name': 'p1-e1'})

        item_list = repo.table_query_by_parent_id(parent_id)
        assert len(item_list) == 1

        repo.add_item(parent_id, 'e2', {'id': 'e2', 'name': 'p1-e2'})

        item_list = repo.table_query_by_parent_id(parent_id)
        assert len(item_list) == 2


        item1 = repo.get_item(parent_id, 'e1')

        assert item1 is not None
        assert item1['id'] == 'e1'
        assert item1['name'] == 'p1-e1'

        item2 = repo.get_item(parent_id, 'e2')

        assert item2 is not None
        assert item2['id'] == 'e2'
        assert item2['name'] == 'p1-e2'


        repo.delete_item(parent_id, 'e1')

        item_list = repo.table_query_by_parent_id(parent_id)
        assert len(item_list) == 1

        item1 = repo.get_item(parent_id, 'e1')
        assert item1 is None

        repo.delete_item(parent_id, 'e2')

        item_list = repo.table_query_by_parent_id(parent_id)
        assert len(item_list) == 0

        item2 = repo.get_item(parent_id, 'e2')
        assert item2 is None

    def test_BatchOperations_DependentEntityRepository(self, docker_dynamodb):

        repo = DependentEntityRepository(table_name, local_url)
        repo.pk_prefix = 'PARENT'
        repo.sk_prefix = 'ENTITY'
        parent_id = 'p1'

        items_to_create = []
        for i in range(10):
            item = (f'TE{i}',  {'id': f'TE{i}', 'name': f'p{i}'})
            items_to_create.append(item)

        repo.batch_add_items(parent_id, items_to_create)

        item_list = repo.table_query_by_parent_id(parent_id)

        assert len(item_list) == 10

        for i in range(len(item_list)):
            item = item_list[i]
            assert item is not None
            assert item['id'] == f'TE{i}'
            assert item['name'] == f'p{i}'

        items_to_delete = []
        for i in range(len(item_list)):
            item = item_list[i]['id']
            items_to_delete.append(item)

        repo.batch_delete_items(parent_id, items_to_delete)

        item_list = repo.table_query_by_parent_id(parent_id)

        assert len(item_list) == 0

    def test_GenericOperations_AssociativeEntityRepository(self, docker_dynamodb):

        repo = AssociativeEntityRepository(table_name, local_url)
        repo.pk_prefix = 'PARENT'
        repo.sk_prefix = 'PARENT_ENTITY'
        repo.gsi1_prefix = 'ENTITY'

        parent_id = 'P1'

        item_list = repo.table_query_by_parent_id(parent_id)
        assert len(item_list) == 0

        repo.add_item(parent_id, 'E1', {'name': 'p1e1'})

        item_list = repo.table_query_by_parent_id(parent_id)

        assert len(item_list) == 1

        repo.add_item(parent_id, 'E2', {'name': 'p1e2'})

        item_list = repo.table_query_by_parent_id(parent_id)

        assert len(item_list) == 2
        assert item_list[0] is not None
        assert item_list[0]['PK'] == 'PARENT#P1'
        assert item_list[0]['SK'] == 'PARENT_ENTITY#P1E1'
        assert item_list[0]['GSI1'] == 'ENTITY#E1'
        assert item_list[0]['name'] == 'p1e1'
        assert item_list[1] is not None
        assert item_list[1]['PK'] == 'PARENT#P1'
        assert item_list[1]['SK'] == 'PARENT_ENTITY#P1E2'
        assert item_list[1]['GSI1'] == 'ENTITY#E2'
        assert item_list[1]['name'] == 'p1e2'


        item_list = repo.gsi1_query_by_parent_id('E1')
        
        assert len(item_list) == 1
        assert item_list[0] is not None
        assert item_list[0]['PK'] == 'PARENT#P1'
        assert item_list[0]['SK'] == 'PARENT_ENTITY#P1E1'
        assert item_list[0]['GSI1'] == 'ENTITY#E1'
        assert item_list[0]['name'] == 'p1e1'

        item_list = repo.gsi1_query_by_parent_id('E2')
        
        assert len(item_list) == 1
        assert item_list[0] is not None
        assert item_list[0]['PK'] == 'PARENT#P1'
        assert item_list[0]['SK'] == 'PARENT_ENTITY#P1E2'
        assert item_list[0]['GSI1'] == 'ENTITY#E2'
        assert item_list[0]['name'] == 'p1e2'

        repo.delete_item(parent_id, 'E1')
        item_list = repo.table_query_by_parent_id(parent_id)
        assert len(item_list) == 1

        repo.delete_item(parent_id, 'E2')
        item_list = repo.table_query_by_parent_id(parent_id)
        assert len(item_list) == 0


    def test_BatchOperations_AssociativeEntityRepository(self, docker_dynamodb):

        repo = AssociativeEntityRepository(table_name, local_url)
        repo.pk_prefix = 'PARENT'
        repo.sk_prefix = 'PARENT_ENTITY'
        repo.gsi1_prefix = 'ENTITY'
        parent_id = 'P1'

        items_to_create = []
        for i in range(10):
            item = (f'E{i}',  { 'name': f'P1E{i}'})
            items_to_create.append(item)

        repo.batch_add_items(parent_id, items_to_create)

        item_list = repo.table_query_by_parent_id(parent_id)

        assert len(item_list) == 10

        for i in range(len(item_list)):
            item = item_list[i]
            assert item is not None
            assert item['PK'] == 'PARENT#P1'
            assert item['SK'] == f'PARENT_ENTITY#P1E{i}'
            assert item['GSI1'] == f'ENTITY#E{i}'
            assert item['name'] == f'P1E{i}'
        
        items_to_delete = []
        for i in range(len(item_list)):
            item = f'E{i}'
            items_to_delete.append(item)

        repo.batch_delete_items(parent_id, items_to_delete)

        item_list = repo.table_query_by_parent_id(parent_id)

        assert len(item_list) == 0
