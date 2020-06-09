from datetime import date
from urllib.parse import urlencode

import requests
from flask import current_app
from webapp.exceptions import UnauthorizedException, GenericException


class TrelloApi:
    base_authorize_url = 'https://trello.com/1/authorize?'
    trello_api_url_base = 'https://api.trello.com/1'

    trello_api_url_me_template = trello_api_url_base + '/members/me/?key={0}&token={1}'
    trello_api_url_boards_template = trello_api_url_base + '/members/me/boards?fields=name,url,closed&key={0}&token={1}'
    trello_api_url_lists_template = trello_api_url_base + '/boards/{0}/lists?fields=name&key={1}&token={2}'
    trello_api_url_list_cards_template = trello_api_url_base + '/lists/{0}/cards?fields=name,url,due,dueComplete&key={1}&token={2}'
    trello_api_url_board_cards_template = trello_api_url_base + '/boards/{0}/cards?fields=name,url,due,dueComplete,labels,desc,idBoard&key={1}&token={2}'


    def __init__(self):
        pass

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
            'name': current_app.config['TRELLO_APP_NAME'],
            'scope': current_app.config['TRELLO_AUTH_SCOPE'],
            'response_type': 'token',
            'key': current_app.config['TRELLO_API_KEY'],
            'return_url': return_url
        }
        authorize_url = TrelloApi.base_authorize_url + urlencode(params)
        return authorize_url


    def get_boards(self, token):
        api_key = current_app.config['TRELLO_API_KEY']

        url = TrelloApi.trello_api_url_boards_template.format(api_key, token)
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
        api_key = current_app.config['TRELLO_API_KEY']
        url = TrelloApi.trello_api_url_lists_template.format(board_id, api_key, token)
        data = self._issue_get_request(url)
        return list(map(lambda x: dict({'id': x['id'], 'name': x['name'] }), data))




    # this is the important method
    def get_events(self, token):
        api_key = current_app.config['TRELLO_API_KEY']

        # override the settings - it's getting all the boards
        settings = {}
        settings['boards'] = []
        boards = self.get_boards(token)
        for board in boards:
            settings['boards'].append(board['id'])
        # all this should come from configuration

        all_cards = []
        for board_id in settings['boards']:
            url = TrelloApi.trello_api_url_board_cards_template.format(board_id, api_key, token)
            data = self._issue_get_request(url)
            all_cards.extend(data)

        result = list()
        for item in all_cards:
            if item['due'] is not None and item['dueComplete'] == False:
                date_only = date.fromisoformat(item['due'].split('T')[0])
                desc = item['desc']
                if len(desc) > 150:
                    desc = item['desc'][:150] + '...'
                result.append({
                    'id': item['id'],
                    'name': item['name'],
                    'due': item['due'],
                    'due_formatted': date_only.strftime('%d %B %Y'),
                    'desc': desc,
                    'url': item['url'],
                    'idBoard': item['idBoard']
                })

        result.sort(key=lambda x: x.get('due'))

        return result

