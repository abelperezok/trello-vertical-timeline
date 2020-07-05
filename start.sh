export FLASK_APP=vertical-timeline/wsgi.py
export FLASK_DEBUG=1
# export APP_CONFIG_FILE=config.py
export AWS_PROFILE=iglu
export FLASK_ENV=development
export TABLE_NAME=$(aws cloudformation describe-stacks --stack-name trello-vertical-timeline \
	--query 'Stacks[0].Outputs[?OutputKey==`DynamoDbTable`].OutputValue' \
	--output text)
export QUEUE_URL=$(aws cloudformation describe-stacks --stack-name trello-vertical-timeline \
	--query 'Stacks[0].Outputs[?OutputKey==`TrelloDataQueue`].OutputValue' \
	--output text)
flask run