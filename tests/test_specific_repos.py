import sys
import os
sys.path.append(os.path.realpath(
    os.path.dirname(__file__)+"/../vertical-timeline/"))
from webapp.repository import UserDataRepository, UserBoardRepository, BoardListRepository, BoardLabelRepository

from tests.conftest import table_name, local_url


class TestSpecificRepository:

    def test_UserDataRepository(self, docker_dynamodb):
        repo = UserDataRepository(table_name, local_url)
        user_id = 'user-0001'

        repo.update_user_token(user_id, 'token0001')

        data = repo.get_user_data(user_id)

        assert data is not None
        assert data['trello_token'] == 'token0001'

        repo.update_user_token(user_id, 'token0002')

        data = repo.get_user_data(user_id)

        assert data is not None
        assert data['trello_token'] == 'token0002'

        repo.delete_user_data(user_id)

        data = repo.get_user_data(user_id)

        assert data is None

        repo.update_timestamp(user_id, '2020-06-09T16:35:50.538111')

        data = repo.get_user_data(user_id)

        assert data is not None
        assert data['timestamp'] == '2020-06-09T16:35:50.538111'


    def test_UserBoardRepository(self, docker_dynamodb):
        repo = UserBoardRepository(table_name, local_url)
        user_id = 'user-0001'

        items_to_create = []
        for i in range(10):
            item = {'id': f'B{i}', 'name': f'Board {i}'}
            items_to_create.append(item)

        repo.add_boards(user_id, items_to_create)

        boards = repo.get_boards(user_id)

        assert len(boards) == 10

        for i in range(len(boards)):
            item = boards[i]
            assert item is not None
            assert item['id'] == f'B{i}'
            assert item['name'] == f'Board {i}'

        repo.delete_boards(user_id, boards)

        empty_boards = repo.get_boards(user_id)

        assert len(empty_boards) == 0

    def test_BoardListRepository(self, docker_dynamodb):
        repo = BoardListRepository(table_name, local_url)
        user_id = 'user-0001'

        for i in range(3):
            items_to_create = []
            board_id = f'B{i}'
            for j in range(10):            
                item = {'id': f'L{j}', 'name': f'List {j}'}
                items_to_create.append(item)
            repo.add_lists(user_id, board_id, items_to_create)
        
        board_lists = [0, 0, 0]
        board_lists[0] = repo.get_lists(user_id, 'B0')
        board_lists[1] = repo.get_lists(user_id, 'B1')
        board_lists[2] = repo.get_lists(user_id, 'B2')

        assert len(board_lists[0]) == 10
        assert len(board_lists[1]) == 10
        assert len(board_lists[2]) == 10

        for i in range(3):
            board_id = f'B{i}'
            for j in range(10): 
                item = board_lists[i][j]
                assert item is not None
                assert item['id'] == f'L{j}'
                assert item['name'] == f'List {j}' 

        for i in range(3):
            repo.delete_lists(user_id, f'B{i}', board_lists[i])


        board_lists[0] = repo.get_lists(user_id, 'B0')
        board_lists[1] = repo.get_lists(user_id, 'B1')
        board_lists[2] = repo.get_lists(user_id, 'B2')

        assert len(board_lists[0]) == 0
        assert len(board_lists[1]) == 0
        assert len(board_lists[2]) == 0


    def test_BoardLabelRepository(self, docker_dynamodb):
        repo = BoardLabelRepository(table_name, local_url)
        user_id = 'user-0001'

        for i in range(3):
            items_to_create = []
            board_id = f'B{i}'
            for j in range(10):            
                item = {'id': f'L{j}', 'name': f'Label {j}'}
                items_to_create.append(item)
            repo.add_labels(user_id, board_id, items_to_create)
        
        board_labels = [0, 0, 0]
        board_labels[0] = repo.get_labels(user_id, 'B0')
        board_labels[1] = repo.get_labels(user_id, 'B1')
        board_labels[2] = repo.get_labels(user_id, 'B2')

        assert len(board_labels[0]) == 10
        assert len(board_labels[1]) == 10
        assert len(board_labels[2]) == 10

        for i in range(3):
            board_id = f'B{i}'
            for j in range(10): 
                item = board_labels[i][j]
                assert item is not None
                assert item['id'] == f'L{j}'
                assert item['name'] == f'Label {j}' 

        for i in range(3):
            repo.delete_labels(user_id, f'B{i}', board_labels[i])


        board_labels[0] = repo.get_labels(user_id, 'B0')
        board_labels[1] = repo.get_labels(user_id, 'B1')
        board_labels[2] = repo.get_labels(user_id, 'B2')

        assert len(board_labels[0]) == 0
        assert len(board_labels[1]) == 0
        assert len(board_labels[2]) == 0