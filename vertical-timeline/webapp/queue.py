import boto3
import os
import json
from flask import current_app
from flask_login import current_user

sqs = boto3.resource('sqs')

def send_message(queue_url, message):
    queue = sqs.Queue(queue_url)
    queue.send_message(MessageBody=message)

# Message sample
# {
#     "TrelloAppName": "app1",
#     "TrelloAuthScope": "scope",
#     "TrelloApiKey": "key1",
#     "UserId": "user-000"
# }

def trello_data_queue_send_message():
    queue_url = os.environ['QUEUE_URL']
    message = {
        'TrelloAppName': current_app.config['TRELLO_APP_NAME'],
        'TrelloAuthScope': current_app.config['TRELLO_AUTH_SCOPE'],
        'TrelloApiKey': current_app.config['TRELLO_API_KEY'],
        'UserId': current_user.get_id()
    }
    send_message(queue_url, json.dumps(message))
