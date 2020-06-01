from urllib.parse import urlencode
from datetime import date
from flask import request, render_template, session, redirect, jsonify, url_for, escape
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

from flask_lambda import FlaskLambda
from flask_awscognito import AWSCognitoAuthentication

import json
import requests


# class TUser():
    
#     def __init__(self, username):
#         self.is_authenticated = True
#         self.is_active = True
#         self.is_anonymous = False
#         self.username = username
#         self.claims = None

#     def get_id(self):
#         return 'user1'


class TUser(UserMixin):
    
    def __init__(self, username):
        self.username = username
        self.claims = None

    def get_id(self):
        return self.username


trello_api_url_base = 'https://api.trello.com/1'

trello_api_url_me_template = trello_api_url_base + '/members/me/?key={0}&token={1}'
trello_api_url_boards_template = trello_api_url_base + '/members/me/boards?fields=name,url,closed&key={0}&token={1}'
trello_api_url_lists_template = trello_api_url_base + '/boards/{0}/lists?fields=name&key={1}&token={2}'
trello_api_url_list_cards_template = trello_api_url_base + '/lists/{0}/cards?fields=name,url,due,dueComplete&key={1}&token={2}'
trello_api_url_board_cards_template = trello_api_url_base + '/boards/{0}/cards?fields=name,url,due,dueComplete,labels,desc,idBoard&key={1}&token={2}'

settings = {
    'boards': [ '5ec9e6d8f051cc74bbf227e1', '5e8f5500a56cfe696c55fd1f' ]
}



app = FlaskLambda(__name__)
app.config.from_pyfile('application.cfg', silent=True)

aws_auth = AWSCognitoAuthentication(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "session_expired"





@login_manager.user_loader
def load_user(user_id):
    claims = session['claims']
    user = TUser(claims['username'])
    user.claims = claims
    return user





@app.route('/session_expired')
def session_expired():
    session.clear()
    return 'your session has expired, please log in again <a href="' + url_for('login', _external=True) + '">here</a>'



# go to cognito UI
@app.route('/login')
def login():
    aws_auth.redirect_url = url_for('aws_cognito_redirect', _external=True)
    return redirect(aws_auth.get_sign_in_url())

# return from cognito UI -> go to private
@app.route('/aws_cognito_redirect')
def aws_cognito_redirect():
    access_token = aws_auth.get_access_token(request.args)
    aws_auth.token_service.verify(access_token)
    claims = aws_auth.token_service.claims
    session['claims'] = claims
    user = TUser(claims['username'])
    login_user(user)

    return redirect(url_for('account'))


@app.route('/config')
@login_required
def config():
    # for k,v in app.config.items():
    #     d.append(k + ':' + str(v))
    return jsonify(settings)


@app.route('/private')
@login_required
def private():
    json_model = {}
    json_model['logout_url'] = url_for('logout', _external=True)
    json_model['user_claims'] = current_user.claims    

    trello_token = session.get('trello_token')

    if trello_token is not None:
        json_model['trello_data'] = {
            'trello_token': trello_token,
            'trello_api_url_me' : url_for('trello_me', _external=True),
            'trello_api_url_boards': url_for('trello_boards', _external=True)
        }
    else:
        callback_url = url_for('token', _external=True)
        api_key = app.config['TRELLO_API_KEY']
        app_name = app.config['TRELLO_APP_NAME']
        scope = app.config['TRELLO_AUTH_SCOPE']

        params = {
            'expiration': 'never',
            'name': app.config['TRELLO_APP_NAME'],
            'scope': app.config['TRELLO_AUTH_SCOPE'],
            'response_type': 'token',
            'key': app.config['TRELLO_API_KEY'],
            'return_url': url_for('token', _external=True)
        }
        json_model['trello_url_authorise'] = 'https://trello.com/1/authorize?' + urlencode(params)

    return jsonify(json_model)


@app.route('/token')
@login_required
def token():
    return render_template('token.html')

@app.route('/token_post', methods=['POST'])
@login_required
def token_post():
    session['trello_token'] = request.json['token'] # request.form['token']
    # return redirect('/private')
    return jsonify({'redirect':url_for('account', _external=True)})


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect('/')



@app.route('/')
def home():
    return render_template('home.html')
    # json_model = {}
    # json_model['login_url'] = url_for('login', _external=True)
    # return jsonify(json_model)



def trello_get_boards():
    api_key = app.config['TRELLO_API_KEY']
    trello_token = session.get('trello_token')
    url = trello_api_url_boards_template.format(api_key, trello_token)
    data = requests.get(url).json()
    result = list()
    for item in data:
        result.append({
            'id': item['id'],
            'name': item['name'],
            'url': item['url'],
            'closed': item['closed']
        })
    return result







# this is the important method
def trello_events():
    api_key = app.config['TRELLO_API_KEY']
    trello_token = session.get('trello_token')

    # override the settings - it's getting all the boards
    settings['boards'] = []
    boards = trello_get_boards()
    for board in boards:
        settings['boards'].append(board['id'])
    # all this should come from configuration

    all_cards = []
    for board_id in settings['boards']:
        url = trello_api_url_board_cards_template.format(board_id, api_key, trello_token)
        data = requests.get(url).json()
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


@app.route('/events')
@login_required
def events():
    if not session.get('trello_token') :
        return 'There is not trello token, get one at <a href="' + url_for('private', _external=True) + '">here</a>'

    result = trello_events()
    return jsonify(result)






@app.route('/trello/boards')
@login_required
def trello_boards():
    data = trello_get_boards()
    result = list()
    for item in data:
        result.append({
            'id': item['id'],
            'name': item['name'],
            'url': item['url'],
            'closed': item['closed'],
            'url_lists': url_for('trello_board_lists', board_id=item['id'], _external=True),
            'url_cards': url_for('trello_board_cards', board_id=item['id'], _external=True),
        })
    return jsonify(result)


@app.route('/trello/boards/<string:board_id>/lists')
@login_required
def trello_board_lists(board_id):
    api_key = app.config['TRELLO_API_KEY']
    trello_token = session.get('trello_token')
    url = trello_api_url_lists_template.format(board_id, api_key, trello_token)
    data = requests.get(url).json()
    result = list()
    for item in data:
        result.append({
            'id': item['id'],
            'name': item['name'],
            'url_cards': url_for('trello_list_cards', list_id=item['id'], _external=True),
        })
    return jsonify(result)

@app.route('/trello/lists/<string:list_id>/cards')
@login_required
def trello_list_cards(list_id):
    api_key = app.config['TRELLO_API_KEY']
    trello_token = session.get('trello_token')
    url = trello_api_url_list_cards_template.format(list_id, api_key, trello_token)
    data = requests.get(url).json()
    return jsonify(data)

@app.route('/trello/boards/<string:board_id>/cards')
@login_required
def trello_board_cards(board_id):
    api_key = app.config['TRELLO_API_KEY']
    trello_token = session.get('trello_token')
    url = trello_api_url_board_cards_template.format(board_id, api_key, trello_token)
    data = requests.get(url).json()
    return jsonify(data)

@app.route('/trello/me')
@login_required
def trello_me():
    api_key = app.config['TRELLO_API_KEY']
    trello_token = session.get('trello_token')
    url = trello_api_url_me_template.format(api_key, trello_token)
    data = requests.get(url).json()
    result = {
        'url': data['url'],
        'username': data['username'],
        'fullName': data['fullName'],
        'initials': data['initials'],
    }
    return jsonify(result)


@app.route('/account')
@login_required
def account():
    authorize_url = ''
    if session.get('trello_token') is None:
        params = {
            'expiration': 'never',
            'name': app.config['TRELLO_APP_NAME'],
            'scope': app.config['TRELLO_AUTH_SCOPE'],
            'response_type': 'token',
            'key': app.config['TRELLO_API_KEY'],
            'return_url': url_for('token', _external=True)
        }
        authorize_url = 'https://trello.com/1/authorize?' + urlencode(params)

    return render_template('account.html', authorize_url=authorize_url, token=session.get('trello_token'))


@app.route('/revoke', methods=['POST'])
@login_required
def revoke():
    session.pop('trello_token')
    return redirect(url_for('account'))



@app.route('/timeline')
@login_required
def timeline():
    if not session.get('trello_token') :
        # return 'There is not trello token, get one at <a href="' + url_for('private', _external=True) + '">here</a>'
        return redirect(url_for('account'))

    model = trello_events()[:10]
    return render_template('timeline.html', model=model)



# # @app.route('/foo', methods=['GET', 'POST'])
# @app.route('/', defaults={'u_path': ''})
# @app.route('/<path:u_path>', methods=['GET', 'POST'])
# def foo(u_path):
#     data = {
#         'form': request.form.copy(),
#         'args': request.args.copy(),
#         'json': request.json
#     }
#     return (
#         json.dumps(data, indent=4, sort_keys=True),
#         200,
#         {'Content-Type': 'application/json'}
#     )

# @app.route('/version', methods=['GET'])
# def version():
#     return '0.0.0'

# @app.route('/home')
# def home():
#     return render_template('home.html')


    








if __name__ == '__main__':
    app.run(debug=True)






















# import json

# # import requests


# def lambda_handler(event, context):
#     """Sample pure Lambda function

#     Parameters
#     ----------
#     event: dict, required
#         API Gateway Lambda Proxy Input Format

#         Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

#     context: object, required
#         Lambda Context runtime methods and attributes

#         Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

#     Returns
#     ------
#     API Gateway Lambda Proxy Output Format: dict

#         Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
#     """

#     # try:
#     #     ip = requests.get("http://checkip.amazonaws.com/")
#     # except requests.RequestException as e:
#     #     # Send some context about this error to Lambda Logs
#     #     print(e)

#     #     raise e

#     # return {
#     #     "statusCode": 200,
#     #     "body": json.dumps({
#     #         "message": "hello world",
#     #         # "location": ip.text.replace("\n", "")
#     #     }),
#     # }

#     return event
