from datetime import date
from urllib.parse import urlencode

import requests
from verticaltimeline_common.exceptions import UnauthorizedException, GenericException

class TrelloApi:
    base_authorize_url = 'https://trello.com/1/authorize?'
    trello_api_url_base = 'https://api.trello.com/1'

    trello_api_url_me_template = trello_api_url_base + '/members/me/?key={0}&token={1}'
    trello_api_url_boards_template = trello_api_url_base + '/members/me/boards?fields=name,url,closed&key={0}&token={1}'
    trello_api_url_lists_template = trello_api_url_base + '/boards/{0}/lists?fields=name&key={1}&token={2}'
    trello_api_url_list_cards_template = trello_api_url_base + '/lists/{0}/cards?fields=name,url,due,dueComplete&key={1}&token={2}'
    trello_api_url_board_labels_template = trello_api_url_base + '/boards/{0}/labels?key={1}&token={2}'
    trello_api_url_board_cards_template = trello_api_url_base + '/boards/{0}/cards?fields=name,desc,url,due,dueComplete,idLabels,idBoard,idList&key={1}&token={2}'


    def __init__(self, trello_app_name = None, trello_auth_scope = None, trello_api_key = None):
        self.trello_app_name = trello_app_name
        self.trello_auth_scope = trello_auth_scope
        self.trello_api_key = trello_api_key

    def _issue_get_request(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError:
            raise UnauthorizedException()
        else:
            raise GenericException()

    def get_authorize_url(self, return_url):
    
        params = {
            'expiration': 'never',
            'name': self.trello_app_name,
            'scope': self.trello_auth_scope,
            'response_type': 'token',
            'key': self.trello_api_key,
            'return_url': return_url
        }
        authorize_url = TrelloApi.base_authorize_url + urlencode(params)
        return authorize_url


    def get_boards(self, token):
        url = TrelloApi.trello_api_url_boards_template.format(self.trello_api_key, token)
        data = self._issue_get_request(url)
        result = list()
        if data:
            for item in data:
                result.append({
                    'id': item['id'],
                    'name': item['name'],
                    'url': item['url'],
                    'closed': item['closed']
                })
        return result

    def get_lists(self, token, board_id):
        url = TrelloApi.trello_api_url_lists_template.format(board_id, self.trello_api_key, token)
        data = self._issue_get_request(url)
        return list(map(lambda x: dict({'id': x['id'], 'name': x['name'] }), data))

    def get_labels(self, token, board_id):
        url = TrelloApi.trello_api_url_board_labels_template.format(board_id, self.trello_api_key, token)
        data = self._issue_get_request(url)
        return list(map(lambda x: dict({'id': x['id'], 'name': x['name'], 'color': x['color'] }), data))

    def get_cards(self, token, board_id):
        url = TrelloApi.trello_api_url_board_cards_template.format(board_id, self.trello_api_key, token)
        data = self._issue_get_request(url)
        return data



