STACK_NAME = trello-vertical-timeline

build-WebAppFunction:
	rsync -av --exclude=*__pycache__ --exclude=Makefile --exclude=static . $(ARTIFACTS_DIR)
	python -m pip install -r requirements.txt -t $(ARTIFACTS_DIR)
	rm -rf $(ARTIFACTS_DIR)/bin
	rm -rf $(ARTIFACTS_DIR)/__pycache__

.PHONY: cdn
cdn:bucket = $(shell aws cloudformation describe-stacks --stack-name $(STACK_NAME) \
	--query 'Stacks[0].Outputs[?OutputKey==`StaticFilesBucket`].OutputValue' \
	--output text)
cdn:
	aws s3 sync webapp/static/ s3://$(bucket)/ --delete --acl=public-read


